"""码头锁与争用登记（写入路径嵌入）。"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from auth import AuthHeader, require_user, require_writer
from db import connect, now_iso, write_audit

router = APIRouter(tags=["locks"])


class LockIn(BaseModel):
    lock_key: str
    action: str = "acquire"


def log_contention(
    conn, lock_key: str, actor: str, detail: str, action: str = "争用"
) -> None:
    """在调用方连接上落一条争用痕。

    注意：必须由调用方在抛 409/回滚业务事务之前 conn.commit()，
    否则“后到只留争用痕”会随整笔业务一起回滚掉（第30号修复点）。
    """
    conn.execute(
        """INSERT INTO contention_log(lock_key,actor,action,detail,created_at)
           VALUES (?,?,?,?,?)""",
        (lock_key, actor, action, detail, now_iso()),
    )


def try_acquire(conn, lock_key: str, holder: str) -> bool:
    now = now_iso()
    row = conn.execute(
        "SELECT holder FROM pier_locks WHERE lock_key=?", (lock_key,)
    ).fetchone()
    if row is None:
        try:
            conn.execute(
                "INSERT INTO pier_locks(lock_key,holder,acquired_at) VALUES (?,?,?)",
                (lock_key, holder, now),
            )
        except sqlite3.IntegrityError:
            # 两路会话 SELECT 都未见锁、并发 INSERT 撞主键：后到判负并留痕。
            winner = conn.execute(
                "SELECT holder FROM pier_locks WHERE lock_key=?", (lock_key,)
            ).fetchone()
            who = winner["holder"] if winner is not None else "先到会话"
            log_contention(conn, lock_key, holder, f"抢锁竞态，持有者={who}")
            return False
        except sqlite3.OperationalError as exc:
            # 锁等待超时等：按争用处理，绝不放行业务写。
            log_contention(conn, lock_key, holder, f"锁忙判负：{exc}")
            return False
        return True
    if row["holder"] == holder:
        return True
    log_contention(conn, lock_key, holder, f"持有者={row['holder']}")
    return False


def release(conn, lock_key: str, holder: str) -> None:
    conn.execute(
        "DELETE FROM pier_locks WHERE lock_key=? AND holder=?",
        (lock_key, holder),
    )


def require_lock(conn, lock_key: str, holder: str) -> None:
    if not try_acquire(conn, lock_key, holder):
        # 各嵌入写口都在业务写之前抢锁；此处先提交，确保争用痕跨业务回滚存活。
        conn.commit()
        raise HTTPException(409, "争用：后到只记争用，不写业务")


@router.get("/api/locks")
def list_locks(authorization: AuthHeader = None):
    require_user(authorization)
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM pier_locks ORDER BY acquired_at DESC"
        ).fetchall()
        return {"items": [dict(r) for r in rows]}


@router.get("/api/contention")
def list_contention(authorization: AuthHeader = None):
    require_user(authorization)
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM contention_log ORDER BY id DESC LIMIT 200"
        ).fetchall()
        return {"items": [dict(r) for r in rows]}


@router.post("/api/locks/acquire")
def acquire_lock(body: LockIn, authorization: AuthHeader = None):
    user = require_writer(authorization)
    with connect() as conn:
        ok = try_acquire(conn, body.lock_key, user)
        write_audit(conn, user, "lock_acquire", body.lock_key, {"ok": ok})
        conn.commit()
        if not ok:
            raise HTTPException(409, "争用：未能获得锁")
        return {"ok": True, "lock_key": body.lock_key, "holder": user}


@router.post("/api/locks/release")
def release_lock(body: LockIn, authorization: AuthHeader = None):
    user = require_writer(authorization)
    with connect() as conn:
        release(conn, body.lock_key, user)
        write_audit(conn, user, "lock_release", body.lock_key, {})
        conn.commit()
        return {"ok": True}