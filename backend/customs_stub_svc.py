"""海关申报空桩（可挂载接口）。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from auth import AuthHeader, require_user, require_writer
from db import connect, now_iso, write_audit
from models import StubJobIn

router = APIRouter(tags=["customs_stub"])


class CustomsStubIn(StubJobIn):
    bl_code: str
    row_count: int = 0


@router.get("/api/customs/jobs")
def list_jobs(authorization: AuthHeader = None):
    require_user(authorization)
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM customs_stub_jobs ORDER BY id DESC LIMIT 100"
        ).fetchall()
        return {"items": [dict(r) for r in rows], "stub": True, "status": "空桩未对接"}


@router.post("/api/customs-stub")
def enqueue_stub(body: CustomsStubIn, authorization: AuthHeader = None):
    user = require_writer(authorization)
    with connect() as conn:
        bl = conn.execute(
            "SELECT bl_code FROM bl_manifests WHERE bl_code=?", (body.bl_code,)
        ).fetchone()
        if not bl:
            raise HTTPException(422, "提单须先登记")
        now = now_iso()
        cur = conn.execute(
            """INSERT INTO customs_stub_jobs(bl_code,row_count,mode,status,detail,created_at)
               VALUES (?,?,?,?,?,?)""",
            (
                body.bl_code,
                body.row_count,
                body.mode,
                "已入队",
                body.detail or "海关空桩预演",
                now,
            ),
        )
        write_audit(conn, user, "customs_stub", body.bl_code, {"job_id": cur.lastrowid})
        conn.commit()
        return {
            "id": cur.lastrowid,
            "status": "已入队",
            "message": "空桩：未对接海关回执",
        }