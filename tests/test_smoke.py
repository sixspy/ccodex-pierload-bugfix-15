import json

import pytest
from fastapi.testclient import TestClient

from app import app
from db import init_db


@pytest.fixture(autouse=True)
def _db(tmp_path, monkeypatch):
    monkeypatch.setattr("db.DB_PATH", tmp_path / "t.db")
    init_db()
    yield


def _auth(c: TestClient, user="admin", password="admin123") -> dict:
    tok = c.post(
        "/api/login", json={"username": user, "password": password}
    ).json()["token"]
    return {"Authorization": "Bearer " + tok}


def test_health_and_seed():
    c = TestClient(app)
    health = c.get("/api/health").json()
    assert health["product"] == "港口过磅闸口"
    assert health["bridges"] >= 4
    assert health["lanes"] >= 5
    assert health["tickets"] >= 4
    assert "customs_stub" in health["meta"]["stubs"]


def test_weigh_overload_gate_seal_flow():
    c = TestClient(app)
    h = _auth(c)
    lanes = c.get("/api/lanes", headers=h).json()["items"]
    lane = next(x for x in lanes if x["lane_code"] == "LN-N-01-IN")
    axles = [
        {"axle": 1, "w": 10.0},
        {"axle": 2, "w": 14.0},
        {"axle": 3, "w": 14.0},
        {"axle": 4, "w": 14.0},
    ]
    ticket = c.post(
        "/api/tickets",
        headers=h,
        json={
            "lane_id": lane["id"],
            "bl_ref": "BL-2026-0101",
            "vehicle_plate": "测A·00001",
            "axle_weights": axles,
            "ticket_code": "WT-FLOW-001",
        },
    ).json()
    assert ticket["overload"] is True
    assert ticket["status"] == "旁路挂起"
    holds = c.get("/api/overloads?status=开放", headers=h).json()["items"]
    hold = next(x for x in holds if x["ticket_code"] == "WT-FLOW-001")
    close = c.post(
        "/api/overloads/close",
        headers=h,
        json={"hold_id": hold["id"], "note": "驳载完成"},
    )
    assert close.status_code == 200
    assert close.json()["ticket_adjudicated"] is True
    gate = c.post(
        "/api/gate/release",
        headers=h,
        json={"ticket_id": ticket["id"], "officer": "验收员"},
    )
    assert gate.status_code == 200
    seal = c.post("/api/seals", headers=h, json={"ticket_id": ticket["id"]})
    assert seal.status_code == 200
    assert seal.json()["generation"] == 2
    proof = c.get("/api/proof/ticket/WT-FLOW-001", headers=h).json()
    assert proof["released"] is True
    assert proof["overload_closed"] is True


def test_gate_blocked_with_open_overload():
    c = TestClient(app)
    h = _auth(c)
    tickets = c.get("/api/tickets?status=旁路挂起", headers=h).json()["items"]
    pending = tickets[0]
    assert (
        c.post(
            "/api/gate/release",
            headers=h,
            json={"ticket_id": pending["id"]},
        ).status_code
        == 409
    )


def test_reconcile_bl():
    c = TestClient(app)
    h = _auth(c)
    recon = c.get("/api/reconcile/BL-2026-0101", headers=h).json()
    assert "declared_gross_t" in recon
    assert recon["tickets"]


def test_lineage_readable():
    c = TestClient(app)
    h = _auth(c)
    edges = c.get("/api/lineage", headers=h).json()["items"]
    assert len(edges) >= 1


def test_lock_contention():
    c = TestClient(app)
    h1 = _auth(c, "admin", "admin123")
    h2 = _auth(c, "writer", "writer123")
    assert (
        c.post(
            "/api/locks/acquire", headers=h1, json={"lock_key": "lane:99"}
        ).status_code
        == 200
    )
    assert (
        c.post(
            "/api/locks/acquire", headers=h2, json={"lock_key": "lane:99"}
        ).status_code
        == 409
    )
    cont = c.get("/api/contention", headers=h1).json()["items"]
    assert any(x["lock_key"] == "lane:99" for x in cont)


def test_viewer_readonly():
    c = TestClient(app)
    h = _auth(c, "viewer", "viewer123")
    assert c.get("/api/bridges", headers=h).status_code == 200
    assert (
        c.post(
            "/api/bridges",
            headers=h,
            json={
                "bridge_code": "WB-NEW-99",
                "pier_zone": "北岸",
                "name": "只读探测",
                "max_gross_t": 50,
                "axle_limit": 6,
            },
        ).status_code
        == 403
    )


def test_seal_bumps_generation():
    c = TestClient(app)
    h = _auth(c)
    lanes = c.get("/api/lanes", headers=h).json()["items"]
    lane = next(x for x in lanes if x["lane_code"] == "LN-S-01-OUT")
    ticket = c.post(
        "/api/tickets",
        headers=h,
        json={
            "lane_id": lane["id"],
            "bl_ref": "BL-2026-0102",
            "vehicle_plate": "测B·00002",
            "axle_weights": [{"axle": 1, "w": 6.0}, {"axle": 2, "w": 5.5}],
            "ticket_code": "WT-SEAL-001",
        },
    ).json()
    assert ticket["status"] == "已裁定"
    c.post(
        "/api/gate/release",
        headers=h,
        json={"ticket_id": ticket["id"]},
    )
    seal = c.post("/api/seals", headers=h, json={"ticket_id": ticket["id"]}).json()
    assert seal["generation"] == 2
    assert "闸代=2" in seal["manifest"]