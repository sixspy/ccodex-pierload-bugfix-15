"""提单册与过磅票对账证明。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from auth import AuthHeader, require_user
from validators import (
    adjudication_label,
    ticket_bypass_bit,
    validate_bl_match,
)

router = APIRouter(tags=["reconcile"])


def _adjudication_summary(ticket_rows: list[dict]) -> dict:
    """第30号·回态修辰：对账卡片的裁定归集。

    唯一来源是正式票态列 weigh_tickets.status（source 明示），
    不读任何影子/草稿回态，避免“影子未晋升、对账当已裁定”的双口径。
    """
    statuses = [t["status"] for t in ticket_rows]
    side_pending = sum(1 for s in statuses if ticket_bypass_bit(s))
    all_adjudicated = bool(statuses) and side_pending == 0 and all(
        s in ("已裁定", "已放行", "已封闸") for s in statuses
    )
    return {
        "source": "weigh_tickets.status",
        "all_adjudicated": all_adjudicated,
        "side_pending": side_pending,
        "label": adjudication_label(statuses) if statuses else "无过磅票",
    }


@router.get("/api/reconcile")
def reconcile_all(authorization: AuthHeader = None):
    require_user(authorization)
    from db import connect

    with connect() as conn:
        rows = conn.execute(
            """SELECT bl_code, declared_gross_t FROM bl_manifests ORDER BY bl_code"""
        ).fetchall()
        items = []
        for bl in rows:
            items.append(_reconcile_bl(conn, bl["bl_code"]))
        return {"items": items}


@router.get("/api/reconcile/{bl_code}")
def reconcile_one(bl_code: str, authorization: AuthHeader = None):
    require_user(authorization)
    from db import connect

    with connect() as conn:
        bl = conn.execute(
            "SELECT * FROM bl_manifests WHERE bl_code=?", (bl_code,)
        ).fetchone()
        if not bl:
            raise HTTPException(404, "提单不存在")
        return _reconcile_bl(conn, bl_code)


def _reconcile_bl(conn, bl_code: str) -> dict:
    bl = conn.execute(
        "SELECT * FROM bl_manifests WHERE bl_code=?", (bl_code,)
    ).fetchone()
    tickets = conn.execute(
        """SELECT ticket_code, gross_t, status, generation FROM weigh_tickets
           WHERE bl_ref=? AND status NOT IN ('作废')""",
        (bl_code,),
    ).fetchall()
    if not tickets:
        return {
            "bl_code": bl_code,
            "declared_gross_t": bl["declared_gross_t"],
            "ticket_sum_t": 0,
            "balanced": False,
            "reason": "无过磅票",
            "tickets": [],
            "adjudication": {
                "source": "weigh_tickets.status",
                "all_adjudicated": False,
                "side_pending": 0,
                "label": "无过磅票",
            },
            "all_adjudicated": False,
            "adjudication_label": "无过磅票",
        }
    ticket_items = []
    for t in tickets:
        d = dict(t)
        d["bypass_pending"] = ticket_bypass_bit(d.get("status"))
        ticket_items.append(d)
    adjudication = _adjudication_summary(ticket_items)
    ticket_sum = round(sum(float(t["gross_t"]) for t in tickets), 3)
    declared = float(bl["declared_gross_t"])
    matched = validate_bl_match(declared, ticket_sum, tolerance=0.1)
    seal_rows = conn.execute(
        """SELECT s.seal_ref, s.ticket_generation, t.ticket_code
           FROM gate_seals s JOIN weigh_tickets t ON t.id=s.ticket_id
           WHERE t.bl_ref=?""",
        (bl_code,),
    ).fetchall()
    proof_ok = matched and len(seal_rows) >= 1
    return {
        "bl_code": bl_code,
        "declared_gross_t": declared,
        "ticket_sum_t": ticket_sum,
        "balanced": matched,
        "proof_ready": proof_ok,
        "seal_count": len(seal_rows),
        "tickets": ticket_items,
        "seals": [dict(s) for s in seal_rows],
        "adjudication": adjudication,
        # 顶层同义字段，方便对账卡片/总览直接绑定
        "all_adjudicated": adjudication["all_adjudicated"],
        "adjudication_label": adjudication["label"],
    }


@router.get("/api/proof/ticket/{ticket_code}")
def proof_ticket(ticket_code: str, authorization: AuthHeader = None):
    require_user(authorization)
    from db import connect

    with connect() as conn:
        ticket = conn.execute(
            "SELECT * FROM weigh_tickets WHERE ticket_code=?", (ticket_code,)
        ).fetchone()
        if not ticket:
            raise HTTPException(404, "票不存在")
        bl = conn.execute(
            "SELECT * FROM bl_manifests WHERE bl_code=?", (ticket["bl_ref"],)
        ).fetchone()
        seal = conn.execute(
            """SELECT * FROM gate_seals WHERE ticket_id=? ORDER BY id DESC LIMIT 1""",
            (ticket["id"],),
        ).fetchone()
        release = conn.execute(
            """SELECT * FROM gate_releases WHERE ticket_id=? AND status='已放行'""",
            (ticket["id"],),
        ).fetchone()
        overload_closed = not conn.execute(
            """SELECT id FROM overload_holds WHERE ticket_id=? AND status='开放'""",
            (ticket["id"],),
        ).fetchone()
        manifest_match = False
        if seal and bl:
            manifest_match = validate_bl_match(
                float(bl["declared_gross_t"]), float(ticket["gross_t"])
            )
        return {
            "ticket_code": ticket_code,
            "bl_ref": ticket["bl_ref"],
            "ticket_status": ticket["status"],
            "bypass_pending": ticket_bypass_bit(ticket["status"]),
            "gross_t": ticket["gross_t"],
            "manifest_matches_bl": manifest_match,
            "has_seal": seal is not None,
            "seal_generation": seal["ticket_generation"] if seal else None,
            "released": release is not None,
            "overload_closed": overload_closed,
            "coherent": bool(
                manifest_match and overload_closed and (seal or release)
            ),
        }