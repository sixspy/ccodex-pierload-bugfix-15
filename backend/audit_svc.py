"""审计轨迹只读。"""
from __future__ import annotations

import json

from fastapi import APIRouter

from auth import AuthHeader, require_user
from db import connect

router = APIRouter(tags=["audit"])


@router.get("/api/audit")
def list_audit(authorization: AuthHeader = None, limit: int = 150):
    require_user(authorization)
    limit = max(10, min(limit, 500))
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_trail ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        items = []
        for r in rows:
            d = dict(r)
            try:
                d["payload"] = json.loads(d["payload"] or "{}")
            except json.JSONDecodeError:
                pass
            items.append(d)
        return {"items": items}