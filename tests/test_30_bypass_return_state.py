"""旁路回态修复 · 第30号 · 三红/三绿复现夹具（回态修辰）。

正确性口径只有一个：**驳回回态**。
本模块封死采用【甲路径】：
    驳回写口（/api/overloads/close，兼名 /api/overloads/reject）必须在
    同一事务内关闭挂起、把 weigh_tickets.status 由「旁路挂起」改写为
    「已裁定」并抹掉旁路位（bypass_pending=False），写 audit；
    任一步失败整笔回滚。
【乙路径】（影子回态草稿、正式票态零改、待确认原子晋升）不在本仓混用：
    测试乙点破“影子回态未晋升，对账却当已裁定”的假修复，并禁止影子表。

三测：
    甲 test_30_jia_reject_rewrites_ticket_state_in_txn
        复现“驳回后票态未回”：写口报成功，主票状态列仍旁路挂起。
    乙 test_30_yi_reconcile_anchors_on_formal_status_no_shadow
        对账/总览/五页同源只能认正式票态列；未晋升的影子/半截回写
        绝不能被对账当成已裁定。
    争用 test_30_zhengyong_concurrent_reject_same_ticket_single_winner
        两路会话同票并发抢驳回锁：只准一个 200，后到 409 且只留争用痕。

夹具来源：fixtures/tickets.json + fixtures/overloads.json
    WT-LN-N-01-IN-002 / HOLD-WT-LN-N-01-IN-002（开放旁路挂起，BL-2026-0103）。
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app import app
from db import connect, init_db

TICKET_CODE = "WT-LN-N-01-IN-002"
HOLD_KEY = "HOLD-WT-LN-N-01-IN-002"
BL_CODE = "BL-2026-0103"
MARK = "回态修辰·第30号"


@pytest.fixture(autouse=True)
def _db(tmp_path, monkeypatch):
    monkeypatch.setattr("db.DB_PATH", tmp_path / "t30.db")
    init_db()
    yield


def _auth(c: TestClient, user: str = "admin", password: str = "admin123") -> dict:
    tok = c.post(
        "/api/login", json={"username": user, "password": password}
    ).json()["token"]
    return {"Authorization": "Bearer " + tok}


def _seeded_bypass_ids(c: TestClient, h: dict) -> tuple[int, int]:
    """返回 (ticket_id, hold_id)，全部从文件库夹具读出。"""
    tickets = c.get("/api/tickets?status=旁路挂起", headers=h).json()["items"]
    ticket = next(t for t in tickets if t["ticket_code"] == TICKET_CODE)
    holds = c.get("/api/overloads?status=开放", headers=h).json()["items"]
    hold = next(x for x in holds if x["hold_key"] == HOLD_KEY)
    assert hold["ticket_code"] == TICKET_CODE
    return ticket["id"], hold["id"]


# ---------------------------------------------------------------------------
# 甲：驳回写口必须同事务回态，不许“挂起已闭、票态仍旁路”
# ---------------------------------------------------------------------------
def test_30_jia_reject_rewrites_ticket_state_in_txn():
    c = TestClient(app)
    h = _auth(c)
    ticket_id, hold_id = _seeded_bypass_ids(c, h)

    # 复现夹具前置：票态确实卡在旁路挂起
    before = c.get(f"/api/tickets/{ticket_id}", headers=h).json()["ticket"]
    assert before["status"] == "旁路挂起"

    r = c.post(
        "/api/overloads/close",
        headers=h,
        json={"hold_id": hold_id, "note": f"{MARK} 甲驳回"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # 写口不能再谎报：ticket_adjudicated=True 必须有真实票态回写支撑
    assert body["ticket_adjudicated"] is True
    assert body.get("ticket_status") == "已裁定"
    assert body.get("status_rewritten") is True

    detail = c.get(f"/api/tickets/{ticket_id}", headers=h).json()
    t = detail["ticket"]
    assert t["status"] == "已裁定", "甲口径：驳回同事务必须把票态列改写为已裁定"
    assert t["adjudicated_at"], "回态时必须落裁定时间"
    assert t["bypass_pending"] is False, "旁路位必须随状态改写抹掉"

    open_holds = [x for x in detail["overload_holds"] if x["status"] == "开放"]
    assert open_holds == []

    # 放行页同源：票回到已裁定后必须放得行（按钮不再灰/不再 409）
    gate = c.post(
        "/api/gate/release",
        headers=h,
        json={"ticket_id": ticket_id, "officer": "三十号验收"},
    )
    assert gate.status_code == 200, gate.text

    # 审计必须记录真实回写，禁止再写 status_rewritten=False
    audits = c.get("/api/audit?limit=50", headers=h).json()["items"]
    close_audit = next(a for a in audits if a["action"] == "overload_close")
    assert close_audit["payload"].get("status_rewritten") is True
    assert close_audit["payload"].get("new_status") == "已裁定"


# ---------------------------------------------------------------------------
# 乙：对账只认正式票态列；点破“影子回态未晋升，对账当已裁定”的混口径假修
# ---------------------------------------------------------------------------
def test_30_yi_reconcile_anchors_on_formal_status_no_shadow():
    c = TestClient(app)
    h = _auth(c)
    ticket_id, hold_id = _seeded_bypass_ids(c, h)

    r = c.post(
        "/api/overloads/close",
        headers=h,
        json={"hold_id": hold_id, "note": f"{MARK} 乙驳回"},
    )
    assert r.status_code == 200
    assert r.json()["ticket_adjudicated"] is True

    # 写口声称已裁定，对账就必须与正式票态列一致（当前埋雷：对账仍读旁路挂起）
    recon = c.get(f"/api/reconcile/{BL_CODE}", headers=h).json()
    row = next(t for t in recon["tickets"] if t["ticket_code"] == TICKET_CODE)
    assert row["status"] == "已裁定"
    assert row["bypass_pending"] is False
    adj = recon["adjudication"]
    assert adj["source"] == "weigh_tickets.status"
    assert adj["all_adjudicated"] is True
    assert adj["side_pending"] == 0
    assert adj["label"] == "已裁定"
    # 顶层同义口径，供对账卡片/总览直接绑定
    assert recon["all_adjudicated"] is True
    assert recon["adjudication_label"] == "已裁定"

    # 点破乙：人为做出“影子回态/半截回写未晋升”的状态——挂起已闭，
    # 但正式票态列被留在旁路挂起。对账绝不能凭影子/闭环痕迹当已裁定。
    with connect() as conn:
        conn.execute(
            "UPDATE weigh_tickets SET status='旁路挂起' WHERE id=?",
            (ticket_id,),
        )
        conn.commit()
    recon_shadow = c.get(f"/api/reconcile/{BL_CODE}", headers=h).json()
    shadow_row = next(
        t for t in recon_shadow["tickets"] if t["ticket_code"] == TICKET_CODE
    )
    assert shadow_row["status"] == "旁路挂起"
    assert shadow_row["bypass_pending"] is True
    assert recon_shadow["adjudication"]["all_adjudicated"] is False
    assert recon_shadow["adjudication"]["side_pending"] >= 1
    assert recon_shadow["adjudication"]["label"] == "旁路挂起"

    # 甲口径封死：仓内不得存在影子/草稿回态表（禁止甲乙混用）
    with connect() as conn:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert not [
        n for n in tables if "shadow" in n.lower() or "draft" in n.lower()
    ], f"{MARK} 禁止引入影子回态表与甲口径混用"


# ---------------------------------------------------------------------------
# 争用：两路会话同票并发打驳回写口，只准一个赢家，后到 409 + 争用痕
# ---------------------------------------------------------------------------
def test_30_zhengyong_concurrent_reject_same_ticket_single_winner():
    setup_c = TestClient(app)
    ticket_id, hold_id = _seeded_bypass_ids(setup_c, _auth(setup_c))
    barrier = threading.Barrier(2)

    def fire(user: str, password: str):
        # 每路线程独立 TestClient / 会话，打同一个驳回写口
        cc = TestClient(app)
        hh = _auth(cc, user, password)
        barrier.wait(timeout=15)
        try:
            resp = cc.post(
                "/api/overloads/close",
                headers=hh,
                json={"hold_id": hold_id, "note": f"{MARK} 争用 {user}"},
            )
            return {"who": user, "code": resp.status_code, "body": resp.json()}
        except Exception as exc:  # 服务端 500/锁异常也算破功，不能吞
            return {"who": user, "code": "EXC", "body": repr(exc)}

    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [
            pool.submit(fire, "admin", "admin123"),
            pool.submit(fire, "writer", "writer123"),
        ]
        results = [f.result(timeout=30) for f in futs]

    codes = [r["code"] for r in results]
    assert "EXC" not in codes, f"驳回写口不得在争用下 500：{results}"
    assert codes.count(200) == 1, f"同票驳回必须恰好一个成功：{results}"
    loser = next(r for r in results if r["code"] != 200)
    assert loser["code"] == 409, f"后到必须 409：{loser}"

    # 赢家回态落定
    c = TestClient(app)
    h = _auth(c)
    t = c.get(f"/api/tickets/{ticket_id}", headers=h).json()["ticket"]
    assert t["status"] == "已裁定"
    holds = c.get("/api/overloads", headers=h).json()["items"]
    target = [x for x in holds if x["id"] == hold_id]
    assert len(target) == 1 and target[0]["status"] == "已关闭"

    # 后到只留争用痕：争用台账必须有该票锁的记录（且跨回滚存活）
    cont = c.get("/api/contention", headers=h).json()["items"]
    traces = [x for x in cont if x["lock_key"] == f"ticket:{ticket_id}"]
    assert traces, f"必须留下 ticket:{ticket_id} 的争用痕，实际：{cont}"
    assert any(x.get("action") == "争用" for x in traces)

    # 判负收尾不得泄漏票锁：锁表中不能残留该 ticket 锁
    locks_now = c.get("/api/locks", headers=h).json()["items"]
    assert all(
        x["lock_key"] != f"ticket:{ticket_id}" for x in locks_now
    ), f"驳回 settle 后票锁残留：{locks_now}"

    # 票最终仍可放行（赢家口径完整）
    gate = c.post(
        "/api/gate/release", headers=h, json={"ticket_id": ticket_id}
    )
    assert gate.status_code == 200, gate.text
