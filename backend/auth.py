"""登录与角色鉴权。"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from db import connect, sha_password, write_audit

router = APIRouter(tags=["auth"])
SECRET = b"pierload-dev-secret-not-for-prod"
AuthHeader = Annotated[str | None, Header(alias="Authorization")]


class LoginIn(BaseModel):
    username: str
    password: str


def _sign(payload: dict) -> str:
    body = base64.urlsafe_b64encode(
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    sig = hmac.new(SECRET, body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def _parse(token: str) -> dict:
    try:
        body, sig = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(401, "令牌无效") from exc
    expect = hmac.new(SECRET, body.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expect, sig):
        raise HTTPException(401, "令牌签名错误")
    data = json.loads(base64.urlsafe_b64decode(body.encode("ascii")))
    if data.get("exp", 0) < time.time():
        raise HTTPException(401, "令牌已过期")
    return data


def require_user(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "未登录")
    data = _parse(authorization[7:].strip())
    return data["u"]


def require_writer(authorization: str | None) -> str:
    user = require_user(authorization)
    with connect() as conn:
        row = conn.execute(
            "SELECT role FROM users WHERE username=?", (user,)
        ).fetchone()
    if not row:
        raise HTTPException(401, "用户不存在")
    if row["role"] == "viewer":
        raise HTTPException(403, "只读账号禁止写入")
    return user


@router.post("/api/login")
def login(body: LoginIn):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username=?", (body.username,)
        ).fetchone()
        if not row or row["password_sha"] != sha_password(body.password):
            raise HTTPException(401, "用户名或密码错误")
        token = _sign(
            {"u": row["username"], "r": row["role"], "exp": time.time() + 86400}
        )
        write_audit(
            conn, row["username"], "login", row["username"], {"role": row["role"]}
        )
        conn.commit()
        return {"token": token, "username": row["username"], "role": row["role"]}


@router.get("/api/me")
def me(authorization: AuthHeader = None):
    user = require_user(authorization)
    with connect() as conn:
        row = conn.execute(
            "SELECT username, role FROM users WHERE username=?", (user,)
        ).fetchone()
    if not row:
        raise HTTPException(401, "用户不存在")
    return dict(row)


@router.get("/api/dashboard")
def dashboard(authorization: AuthHeader = None):
    require_user(authorization)
    from db import dashboard_stats

    with connect() as conn:
        return dashboard_stats(conn)