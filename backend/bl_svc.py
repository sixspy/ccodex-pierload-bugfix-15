"""提单册登记。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from auth import AuthHeader, require_user, require_writer
from db import connect, now_iso, write_audit
from models import BlIn

router = APIRouter(tags=["bl"])


@router.get("/api/bl")
def list_bl(authorization: AuthHeader = None):
    require_user(authorization)
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM bl_manifests ORDER BY bl_code"
        ).fetchall()
        return {"items": [dict(r) for r in rows]}


@router.get("/api/bl/{bl_code}")
def get_bl(bl_code: str, authorization: AuthHeader = None):
    require_user(authorization)
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM bl_manifests WHERE bl_code=?", (bl_code,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "提单不存在")
        tickets = conn.execute(
            """SELECT ticket_code, gross_t, status FROM weigh_tickets
               WHERE bl_ref=? ORDER BY id DESC""",
            (bl_code,),
        ).fetchall()
        return {"bl": dict(row), "tickets": [dict(t) for t in tickets]}


@router.post("/api/bl")
def create_bl(body: BlIn, authorization: AuthHeader = None):
    user = require_writer(authorization)
    with connect() as conn:
        if conn.execute(
            "SELECT id FROM bl_manifests WHERE bl_code=?", (body.bl_code,)
        ).fetchone():
            raise HTTPException(409, "提单号已存在")
        now = now_iso()
        cur = conn.execute(
            """INSERT INTO bl_manifests(bl_code,cargo_desc,declared_gross_t,vessel_voyage,
               status,created_at) VALUES (?,?,?,?,?,?)""",
            (
                body.bl_code,
                body.cargo_desc,
                body.declared_gross_t,
                body.vessel_voyage,
                "在港",
                now,
            ),
        )
        write_audit(conn, user, "bl_register", body.bl_code, {"bl_id": cur.lastrowid})
        conn.commit()
        return {"id": cur.lastrowid, "bl_code": body.bl_code}