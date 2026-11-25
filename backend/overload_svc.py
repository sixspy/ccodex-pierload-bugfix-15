"""超重挂起：旁路驳回与闭环。

第30号·回态修辰 口径封死（甲路径，禁混乙影子口径）：
驳回写口 /api/overloads/close（兼名 /api/overloads/reject）必须在**同一事务**内
  1) 把 overload_holds 开放挂起置为已关闭（条件更新，并发下只许一方命中）；
  2) 该票已无开放挂起时，把 weigh_tickets.status 由「旁路挂起」改写为「已裁定」、
     落 adjudicated_at，抹掉旁路位；
  3) 写审计 status_rewritten=true/new_status=已裁定。
任一步抛错整笔回滚，绝不允许“挂起已闭、主票态仍旁路挂起”。
两人同票并发驳回抢 ticket:{id} 锁，后到 409 且只留 contention_log 争用痕。
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from auth import AuthHeader, require_user, require_writer
from db import connect, now_iso, write_audit
from locks import log_contention, release, require_lock, try_acquire
from models import OverloadCloseIn, OverloadOpenIn, OverloadRejectIn
from validators import (
    RETURN_STATE_STATUS,
    adjudicate_overload,
    is_bypass_pending,
    validate_ticket_mutable,
)

router = APIRouter(tags=["overload"])


@router.get("/api/overloads")
def list_overloads(authorization: AuthHeader = None, status: str | None = None):
    require_user(authorization)
    with connect() as conn:
        q = """SELECT h.*, t.ticket_code, t.vehicle_plate, t.gross_t,
                      t.status AS ticket_status
               FROM overload_holds h JOIN weigh_tickets t ON t.id=h.ticket_id"""
        if status:
            rows = conn.execute(
                q + " WHERE h.status=? ORDER BY h.id DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute(q + " ORDER BY h.id DESC").fetchall()
        return {"items": [dict(r) for r in rows]}


@router.post("/api/overloads/open")
def open_overload(body: OverloadOpenIn, authorization: AuthHeader = None):
    user = require_writer(authorization)
    lock_key = f"ticket:{body.ticket_id}"
    with connect() as conn:
        require_lock(conn, lock_key, user)
        try:
            ticket = conn.execute(
                """SELECT t.*, l.overload_threshold_t FROM weigh_tickets t
                   JOIN weigh_lanes l ON l.id=t.lane_id WHERE t.id=?""",
                (body.ticket_id,),
            ).fetchone()
            if not ticket:
                raise HTTPException(404, "过磅票不存在")
            validate_ticket_mutable(dict(ticket))
            open_one = conn.execute(
                """SELECT id FROM overload_holds WHERE ticket_id=? AND status='开放'""",
                (body.ticket_id,),
            ).fetchone()
            if open_one:
                raise HTTPException(409, "已有开放挂起")
            threshold = body.threshold_t or float(ticket["overload_threshold_t"])
            is_over, overweight = adjudicate_overload(
                float(ticket["gross_t"]), threshold
            )
            if not is_over:
                raise HTTPException(422, "未超重，不必挂起")
            now = now_iso()
            hold_key = f"HOLD-{ticket['ticket_code']}-M"
            cur = conn.execute(
                """INSERT INTO overload_holds(ticket_id,hold_key,overweight_t,threshold_t,
                   status,opened_at,side_lane_note) VALUES (?,?,?,?,?,?,?)""",
                (
                    body.ticket_id,
                    hold_key,
                    overweight,
                    threshold,
                    "开放",
                    now,
                    body.side_lane_note or "人工挂起",
                ),
            )
            conn.execute(
                "UPDATE weigh_tickets SET status='旁路挂起' WHERE id=?",
                (body.ticket_id,),
            )
            write_audit(
                conn,
                user,
                "overload_open",
                hold_key,
                {"hold_id": cur.lastrowid, "overweight_t": overweight},
            )
            conn.commit()
            return {
                "id": cur.lastrowid,
                "hold_key": hold_key,
                "overweight_t": overweight,
                "status": "开放",
            }
        finally:
            release(conn, lock_key, user)


def _resolve_hold(conn, *, hold_id: int | None, ticket_id: int | None):
    """按 hold_id 或 ticket_id 解析要驳回的挂起。"""
    if hold_id is not None:
        hold = conn.execute(
            "SELECT * FROM overload_holds WHERE id=?", (hold_id,)
        ).fetchone()
        if not hold:
            raise HTTPException(404, "挂起不存在")
        return hold
    if ticket_id is None:
        raise HTTPException(422, "hold_id 与 ticket_id 至少给一个")
    hold = conn.execute(
        """SELECT * FROM overload_holds
           WHERE ticket_id=? ORDER BY (status='开放') DESC, id DESC LIMIT 1""",
        (ticket_id,),
    ).fetchone()
    if not hold:
        raise HTTPException(404, "该票没有超重挂起")
    return hold


class _RejectLostRace(Exception):
    """条件更新未命中：另一会话已先完成驳回。"""


def _lose_locked_contender(conn, lock_key: str, user: str, detail: str):
    """持锁后的判负收尾：释放本会话锁 + 落争用痕，同一 commit 持久化，再 409。

    必须先 release 再 commit：否则锁行会随 commit 残留，变成死锁票。
    detail 同时作为 409 文案，保留“挂起已关闭”等既有口径关键词。
    """
    release(conn, lock_key, user)
    log_contention(conn, lock_key, user, detail)
    conn.commit()
    raise HTTPException(409, detail)


def _reject_open_hold(conn, hold, user: str, note: str) -> dict:
    """甲路径核心：关挂起 + 同事务回写正式票态。调用方负责连接/锁与提交。"""
    ticket_id = hold["ticket_id"]
    now = now_iso()

    # 条件更新作为并发终判：只有仍开放的一方能命中 1 行，杜绝双 200。
    cur = conn.execute(
        """UPDATE overload_holds
           SET status='已关闭', closed_at=?, side_lane_note=?
           WHERE id=? AND status='开放'""",
        (now, note or hold["side_lane_note"], hold["id"]),
    )
    if cur.rowcount != 1:
        # 锁内条件更新仍未命中：交给路由做“释放锁+争用痕+409”收尾。
        raise _RejectLostRace()

    open_left = conn.execute(
        """SELECT COUNT(*) c FROM overload_holds
           WHERE ticket_id=? AND status='开放'""",
        (ticket_id,),
    ).fetchone()["c"]

    status_rewritten = False
    if not open_left:
        # BUGFIX-15 修复（第30号）：不再 pass。同事务把票态列回写为已裁定，
        # 抹掉「旁路挂起」旁路位；已放行/已封闸/作废不允许倒退覆盖。
        upd = conn.execute(
            """UPDATE weigh_tickets
               SET status=?,
                   adjudicated_at=COALESCE(adjudicated_at, ?)
               WHERE id=? AND status=?""",
            (RETURN_STATE_STATUS, now, ticket_id, "旁路挂起"),
        )
        status_rewritten = upd.rowcount == 1

    row = conn.execute(
        "SELECT status FROM weigh_tickets WHERE id=?", (ticket_id,)
    ).fetchone()
    new_status = row["status"] if row else None
    if status_rewritten:
        # 显式抹掉旁路位的同源派生不需要额外列：状态离开旁路挂起即抹位。
        assert not is_bypass_pending(new_status)

    write_audit(
        conn,
        user,
        "overload_close",
        hold["hold_key"],
        {
            "note": note,
            "hold_id": hold["id"],
            "ticket_id": ticket_id,
            "open_left": open_left,
            "status_rewritten": status_rewritten,
            "new_status": new_status,
            "path": "jia_same_txn_return_state",
        },
    )
    return {
        "ok": True,
        "hold_id": hold["id"],
        "ticket_id": ticket_id,
        "ticket_adjudicated": not open_left,
        "status_rewritten": status_rewritten,
        "ticket_status": new_status,
    }


@router.post("/api/overloads/close")
def close_overload(body: OverloadCloseIn, authorization: AuthHeader = None):
    user = require_writer(authorization)
    with connect() as conn:
        meta = conn.execute(
            "SELECT ticket_id FROM overload_holds WHERE id=?", (body.hold_id,)
        ).fetchone()
        if not meta:
            raise HTTPException(404, "挂起不存在")
        lock_key = f"ticket:{meta['ticket_id']}"
        # 先抢同票挂起锁；判负时 require_lock 已提交争用痕并抛 409。
        require_lock(conn, lock_key, user)
        try:
            # 持锁后再读状态，锁外不做“已关闭”终判，避免后到无痕 409。
            hold = conn.execute(
                "SELECT * FROM overload_holds WHERE id=?", (body.hold_id,)
            ).fetchone()
            if hold is None:
                _lose_locked_contender(
                    conn, lock_key, user, "后到判负：挂起不存在"
                )
            if hold["status"] != "开放":
                _lose_locked_contender(
                    conn, lock_key, user, "争用：挂起已关闭，驳回回态已被先到会话完成；后到只留争用痕"
                )
            try:
                result = _reject_open_hold(conn, hold, user, body.note)
            except _RejectLostRace:
                _lose_locked_contender(
                    conn, lock_key, user, "争用：挂起已关闭（条件更新未命中），先到已驳回回态；后到只留争用痕"
                )
            conn.commit()
            return result
        finally:
            release(conn, lock_key, user)


@router.post("/api/overloads/reject")
def reject_overload(body: OverloadRejectIn, authorization: AuthHeader = None):
    """第30号“驳回写口”正名路由，与 /close 同一甲路径核心，不搞第二口径。"""
    user = require_writer(authorization)
    with connect() as conn:
        hold = _resolve_hold(
            conn, hold_id=body.hold_id, ticket_id=body.ticket_id
        )
        lock_key = f"ticket:{hold['ticket_id']}"
        # 用 try_acquire 以便按 ticket_id 解析后统一在本函数处理判负提交。
        if not try_acquire(conn, lock_key, user):
            conn.commit()  # 提交 try_acquire 已写入的争用痕
            raise HTTPException(409, "争用：后到只记争用，不写业务")
        try:
            hold = conn.execute(
                "SELECT * FROM overload_holds WHERE id=?", (hold["id"],)
            ).fetchone()
            if hold is None or hold["status"] != "开放":
                _lose_locked_contender(
                    conn, lock_key, user, "争用：挂起已关闭，驳回回态已被先到会话完成；后到只留争用痕"
                )
            try:
                result = _reject_open_hold(conn, hold, user, body.note)
            except _RejectLostRace:
                _lose_locked_contender(
                    conn, lock_key, user, "争用：挂起已关闭（条件更新未命中），先到已驳回回态；后到只留争用痕"
                )
            conn.commit()
            result["rejected"] = True
            return result
        finally:
            release(conn, lock_key, user)