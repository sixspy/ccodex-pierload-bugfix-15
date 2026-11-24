"""过磅车道登记。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from auth import AuthHeader, require_user, require_writer
from db import connect, now_iso, write_audit
from models import LaneIn

router = APIRouter(tags=["lanes"])


@router.get("/api/lanes")
def list_lanes(authorization: AuthHeader = None, bridge_id: int | None = None):
    require_user(authorization)
    with connect() as conn:
        if bridge_id:
            rows = conn.execute(
                """SELECT l.*, b.bridge_code, b.name bridge_name FROM weigh_lanes l
                   JOIN weigh_bridges b ON b.id=l.bridge_id
                   WHERE l.bridge_id=? ORDER BY l.lane_code""",
                (bridge_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT l.*, b.bridge_code, b.name bridge_name FROM weigh_lanes l
                   JOIN weigh_bridges b ON b.id=l.bridge_id
                   ORDER BY l.lane_code"""
            ).fetchall()
        return {"items": [dict(r) for r in rows]}


@router.get("/api/lanes/{lane_id}")
def get_lane(lane_id: int, authorization: AuthHeader = None):
    require_user(authorization)
    with connect() as conn:
        row = conn.execute(
            """SELECT l.*, b.bridge_code, b.max_gross_t, b.axle_limit
               FROM weigh_lanes l JOIN weigh_bridges b ON b.id=l.bridge_id
               WHERE l.id=?""",
            (lane_id,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "车道不存在")
        tickets = conn.execute(
            """SELECT ticket_code, status, gross_t FROM weigh_tickets
               WHERE lane_id=? ORDER BY id DESC LIMIT 8""",
            (lane_id,),
        ).fetchall()
        return {"lane": dict(row), "recent_tickets": [dict(t) for t in tickets]}


@router.post("/api/lanes")
def create_lane(body: LaneIn, authorization: AuthHeader = None):
    user = require_writer(authorization)
    with connect() as conn:
        br = conn.execute(
            "SELECT id FROM weigh_bridges WHERE id=?", (body.bridge_id,)
        ).fetchone()
        if not br:
            raise HTTPException(404, "所属地磅不存在")
        if conn.execute(
            "SELECT id FROM weigh_lanes WHERE lane_code=?", (body.lane_code,)
        ).fetchone():
            raise HTTPException(409, "车道编码已存在")
        if body.overload_threshold_t > 200:
            raise HTTPException(422, "超限阈值不合理")
        now = now_iso()
        cur = conn.execute(
            """INSERT INTO weigh_lanes(lane_code,bridge_id,direction,overload_threshold_t,
               side_lane_ref,status,created_at) VALUES (?,?,?,?,?,?,?)""",
            (
                body.lane_code,
                body.bridge_id,
                body.direction,
                body.overload_threshold_t,
                body.side_lane_ref,
                body.status,
                now,
            ),
        )
        write_audit(conn, user, "lane_create", body.lane_code, {"lane_id": cur.lastrowid})
        conn.commit()
        return {"id": cur.lastrowid, "lane_code": body.lane_code}