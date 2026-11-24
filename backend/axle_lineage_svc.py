"""轴重血缘边。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from auth import AuthHeader, require_user, require_writer
from db import connect, now_iso, write_audit
from models import LineageIn

router = APIRouter(tags=["lineage"])


@router.get("/api/lineage")
def list_lineage(authorization: AuthHeader = None):
    require_user(authorization)
    with connect() as conn:
        rows = conn.execute(
            """SELECT e.*, a.ticket_code from_code, b.ticket_code to_code
               FROM axle_lineage e
               JOIN weigh_tickets a ON a.id=e.from_ticket_id
               LEFT JOIN weigh_tickets b ON b.id=e.to_ticket_id
               ORDER BY e.id DESC"""
        ).fetchall()
        return {"items": [dict(r) for r in rows]}


@router.get("/api/lineage/ticket/{ticket_id}")
def lineage_for_ticket(ticket_id: int, authorization: AuthHeader = None):
    require_user(authorization)
    with connect() as conn:
        out_edges = conn.execute(
            """SELECT e.*, b.ticket_code to_code FROM axle_lineage e
               LEFT JOIN weigh_tickets b ON b.id=e.to_ticket_id
               WHERE e.from_ticket_id=?""",
            (ticket_id,),
        ).fetchall()
        in_edges = conn.execute(
            """SELECT e.*, a.ticket_code from_code FROM axle_lineage e
               JOIN weigh_tickets a ON a.id=e.from_ticket_id
               WHERE e.to_ticket_id=?""",
            (ticket_id,),
        ).fetchall()
        return {
            "outbound": [dict(x) for x in out_edges],
            "inbound": [dict(x) for x in in_edges],
        }


@router.post("/api/lineage")
def add_lineage(body: LineageIn, authorization: AuthHeader = None):
    user = require_writer(authorization)
    with connect() as conn:
        fr = conn.execute(
            "SELECT id, ticket_code FROM weigh_tickets WHERE id=?",
            (body.from_ticket_id,),
        ).fetchone()
        if not fr:
            raise HTTPException(404, "起点票不存在")
        if body.to_ticket_id:
            to = conn.execute(
                "SELECT id FROM weigh_tickets WHERE id=?", (body.to_ticket_id,)
            ).fetchone()
            if not to:
                raise HTTPException(404, "终点票不存在")
        now = now_iso()
        cur = conn.execute(
            """INSERT INTO axle_lineage(from_ticket_id,to_ticket_id,edge_type,detail,created_at)
               VALUES (?,?,?,?,?)""",
            (
                body.from_ticket_id,
                body.to_ticket_id,
                body.edge_type,
                body.detail,
                now,
            ),
        )
        write_audit(
            conn,
            user,
            "lineage_edge",
            fr["ticket_code"],
            {"edge_id": cur.lastrowid, "edge_type": body.edge_type},
        )
        conn.commit()
        return {"id": cur.lastrowid}