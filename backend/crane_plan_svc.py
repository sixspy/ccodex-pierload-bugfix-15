"""岸桥计划空桩（可挂载接口）。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from auth import AuthHeader, require_user, require_writer
from db import connect, now_iso, write_audit
from models import StubJobIn

router = APIRouter(tags=["crane_plan"])


class CraneStubIn(StubJobIn):
    ticket_id: int | None = None
    berth_slot: str = "B-07"


@router.get("/api/crane/jobs")
def list_jobs(authorization: AuthHeader = None):
    require_user(authorization)
    with connect() as conn:
        rows = conn.execute(
            """SELECT j.*, t.ticket_code FROM crane_plan_jobs j
               LEFT JOIN weigh_tickets t ON t.id=j.ticket_id
               ORDER BY j.id DESC LIMIT 100"""
        ).fetchall()
        return {"items": [dict(r) for r in rows], "stub": True, "status": "空桩未对接"}


@router.post("/api/crane-stub")
def enqueue_stub(body: CraneStubIn, authorization: AuthHeader = None):
    user = require_writer(authorization)
    with connect() as conn:
        if body.ticket_id:
            ticket = conn.execute(
                "SELECT id FROM weigh_tickets WHERE id=?", (body.ticket_id,)
            ).fetchone()
            if not ticket:
                raise HTTPException(404, "过磅票不存在")
        now = now_iso()
        cur = conn.execute(
            """INSERT INTO crane_plan_jobs(ticket_id,berth_slot,mode,status,detail,created_at)
               VALUES (?,?,?,?,?,?)""",
            (
                body.ticket_id,
                body.berth_slot,
                body.mode,
                "已入队",
                body.detail or "岸桥计划空桩预演",
                now,
            ),
        )
        write_audit(conn, user, "crane_stub", body.berth_slot, {"job_id": cur.lastrowid})
        conn.commit()
        return {
            "id": cur.lastrowid,
            "status": "已入队",
            "message": "空桩：未对接岸桥排程",
        }