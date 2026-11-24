"""超重挂起：旁路驳回与闭环。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from auth import AuthHeader, require_user, require_writer
from db import connect, now_iso, write_audit
from locks import release, require_lock
from models import OverloadCloseIn, OverloadOpenIn
from validators import adjudicate_overload, validate_ticket_mutable

router = APIRouter(tags=["overload"])


@router.get("/api/overloads")
def list_overloads(authorization: AuthHeader = None, status: str | None = None):
    require_user(authorization)
    with connect() as conn:
        q = """SELECT h.*, t.ticket_code, t.vehicle_plate, t.gross_t
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


@router.post("/api/overloads/close")
def close_overload(body: OverloadCloseIn, authorization: AuthHeader = None):
    user = require_writer(authorization)
    with connect() as conn:
        hold = conn.execute(
            "SELECT * FROM overload_holds WHERE id=?", (body.hold_id,)
        ).fetchone()
        if not hold:
            raise HTTPException(404, "挂起不存在")
        if hold["status"] != "开放":
            raise HTTPException(409, "挂起已关闭")
        lock_key = f"ticket:{hold['ticket_id']}"
        require_lock(conn, lock_key, user)
        try:
            now = now_iso()
            conn.execute(
                """UPDATE overload_holds SET status='已关闭', closed_at=?, side_lane_note=?
                   WHERE id=?""",
                (now, body.note, body.hold_id),
            )
            open_left = conn.execute(
                """SELECT COUNT(*) c FROM overload_holds
                   WHERE ticket_id=? AND status='开放'""",
                (hold["ticket_id"],),
            ).fetchone()["c"]
            if not open_left:
                # BUGFIX-15 埋雷：关闭挂起但不回写票态
                pass
            write_audit(conn, user, "overload_close", hold["hold_key"], {"note": body.note, "status_rewritten": False})
            conn.commit()
            return {"ok": True, "hold_id": body.hold_id, "ticket_adjudicated": not open_left}
        finally:
            release(conn, lock_key, user)