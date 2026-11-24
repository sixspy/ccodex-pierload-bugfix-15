"""SQLite：港口过磅闸口母仓公共库层。"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB_PATH = DATA / "app.db"
FIXTURES = ROOT / "fixtures"
FRONTEND = ROOT / "frontend"

PRODUCT_META = {
    "product": "港口过磅闸口",
    "skeleton": "过磅票入闸后裁定超重才放行，驳回进旁路挂起，闸代快照与提单册对账",
    "modules": [
        "bridges",
        "lanes",
        "tickets",
        "overload",
        "gate",
        "seal",
        "bl",
        "axle_lineage",
        "reconcile",
        "locks",
        "audit",
    ],
    "stubs": ["customs_stub", "crane_plan"],
}


def connect() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def sha_password(password: str) -> str:
    import hashlib

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def now_iso() -> str:
    from datetime import datetime

    return datetime.now().isoformat(timespec="seconds")


SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  username TEXT PRIMARY KEY,
  password_sha TEXT NOT NULL,
  role TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS weigh_bridges(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  bridge_code TEXT UNIQUE NOT NULL,
  pier_zone TEXT NOT NULL,
  name TEXT NOT NULL,
  max_gross_t REAL NOT NULL,
  axle_limit INTEGER NOT NULL DEFAULT 6,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS weigh_lanes(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lane_code TEXT UNIQUE NOT NULL,
  bridge_id INTEGER NOT NULL,
  direction TEXT NOT NULL,
  overload_threshold_t REAL NOT NULL,
  side_lane_ref TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(bridge_id) REFERENCES weigh_bridges(id)
);
CREATE TABLE IF NOT EXISTS weigh_tickets(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticket_code TEXT UNIQUE NOT NULL,
  lane_id INTEGER NOT NULL,
  bl_ref TEXT NOT NULL,
  vehicle_plate TEXT NOT NULL,
  axle_weights TEXT NOT NULL,
  gross_t REAL NOT NULL,
  generation INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL,
  adjudicated_at TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(lane_id) REFERENCES weigh_lanes(id)
);
CREATE TABLE IF NOT EXISTS overload_holds(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticket_id INTEGER NOT NULL,
  hold_key TEXT NOT NULL,
  overweight_t REAL NOT NULL,
  threshold_t REAL NOT NULL,
  status TEXT NOT NULL,
  opened_at TEXT NOT NULL,
  closed_at TEXT,
  side_lane_note TEXT,
  FOREIGN KEY(ticket_id) REFERENCES weigh_tickets(id)
);
CREATE TABLE IF NOT EXISTS gate_releases(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticket_id INTEGER NOT NULL,
  lane_id INTEGER NOT NULL,
  release_ref TEXT NOT NULL,
  status TEXT NOT NULL,
  officer TEXT NOT NULL,
  released_at TEXT NOT NULL,
  FOREIGN KEY(ticket_id) REFERENCES weigh_tickets(id),
  FOREIGN KEY(lane_id) REFERENCES weigh_lanes(id)
);
CREATE TABLE IF NOT EXISTS gate_seals(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticket_id INTEGER NOT NULL,
  ticket_generation INTEGER NOT NULL,
  manifest TEXT NOT NULL,
  seal_ref TEXT NOT NULL,
  status TEXT NOT NULL,
  sealed_at TEXT NOT NULL,
  FOREIGN KEY(ticket_id) REFERENCES weigh_tickets(id)
);
CREATE TABLE IF NOT EXISTS bl_manifests(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  bl_code TEXT UNIQUE NOT NULL,
  cargo_desc TEXT NOT NULL,
  declared_gross_t REAL NOT NULL,
  vessel_voyage TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS axle_lineage(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  from_ticket_id INTEGER NOT NULL,
  to_ticket_id INTEGER,
  edge_type TEXT NOT NULL,
  detail TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(from_ticket_id) REFERENCES weigh_tickets(id)
);
CREATE TABLE IF NOT EXISTS pier_locks(
  lock_key TEXT PRIMARY KEY,
  holder TEXT NOT NULL,
  acquired_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contention_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lock_key TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_trail(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  target TEXT,
  payload TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS customs_stub_jobs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  bl_code TEXT NOT NULL,
  row_count INTEGER NOT NULL,
  mode TEXT NOT NULL,
  status TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS crane_plan_jobs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticket_id INTEGER,
  berth_slot TEXT NOT NULL,
  mode TEXT NOT NULL,
  status TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL
);
"""


def write_audit(
    conn: sqlite3.Connection, actor: str, action: str, target: str, payload: dict
) -> None:
    conn.execute(
        """INSERT INTO audit_trail(actor,action,target,payload,created_at)
           VALUES (?,?,?,?,?)""",
        (actor, action, target, json.dumps(payload, ensure_ascii=False), now_iso()),
    )


def _load_json(name: str):
    path = FIXTURES / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def seed_users(conn: sqlite3.Connection) -> None:
    seeds = (
        ("admin", sha_password("admin123"), "admin"),
        ("writer", sha_password("writer123"), "clerk"),
        ("viewer", sha_password("viewer123"), "viewer"),
    )
    for u, pw, role in seeds:
        conn.execute(
            "INSERT OR IGNORE INTO users(username,password_sha,role) VALUES (?,?,?)",
            (u, pw, role),
        )


def _bridge_id(conn, code: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM weigh_bridges WHERE bridge_code=?", (code,)
    ).fetchone()
    return int(row["id"]) if row else None


def seed_bridges(conn: sqlite3.Connection) -> None:
    for row in _load_json("bridges.json"):
        if conn.execute(
            "SELECT id FROM weigh_bridges WHERE bridge_code=?",
            (row["bridge_code"],),
        ).fetchone():
            continue
        conn.execute(
            """INSERT INTO weigh_bridges(bridge_code,pier_zone,name,max_gross_t,
               axle_limit,status,created_at) VALUES (?,?,?,?,?,?,?)""",
            (
                row["bridge_code"],
                row["pier_zone"],
                row["name"],
                float(row["max_gross_t"]),
                int(row.get("axle_limit", 6)),
                row.get("status", "运行"),
                row.get("created_at", now_iso()),
            ),
        )


def seed_lanes(conn: sqlite3.Connection) -> None:
    for row in _load_json("lanes.json"):
        if conn.execute(
            "SELECT id FROM weigh_lanes WHERE lane_code=?", (row["lane_code"],)
        ).fetchone():
            continue
        br = _bridge_id(conn, row["bridge_code"])
        if not br:
            continue
        conn.execute(
            """INSERT INTO weigh_lanes(lane_code,bridge_id,direction,overload_threshold_t,
               side_lane_ref,status,created_at) VALUES (?,?,?,?,?,?,?)""",
            (
                row["lane_code"],
                br,
                row["direction"],
                float(row["overload_threshold_t"]),
                row.get("side_lane_ref", ""),
                row.get("status", "开放"),
                row.get("created_at", now_iso()),
            ),
        )


def _lane_id(conn, code: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM weigh_lanes WHERE lane_code=?", (code,)
    ).fetchone()
    return int(row["id"]) if row else None


def seed_tickets(conn: sqlite3.Connection) -> None:
    for row in _load_json("tickets.json"):
        if conn.execute(
            "SELECT id FROM weigh_tickets WHERE ticket_code=?", (row["ticket_code"],)
        ).fetchone():
            continue
        lane = _lane_id(conn, row["lane_code"])
        if not lane:
            continue
        axles = row.get("axle_weights", [])
        gross = float(row.get("gross_t", sum(float(a.get("w", 0)) for a in axles)))
        conn.execute(
            """INSERT INTO weigh_tickets(ticket_code,lane_id,bl_ref,vehicle_plate,
               axle_weights,gross_t,generation,status,adjudicated_at,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                row["ticket_code"],
                lane,
                row["bl_ref"],
                row["vehicle_plate"],
                json.dumps(axles, ensure_ascii=False),
                gross,
                int(row.get("generation", 1)),
                row.get("status", "已裁定"),
                row.get("adjudicated_at"),
                row.get("created_at", now_iso()),
            ),
        )


def seed_overloads(conn: sqlite3.Connection) -> None:
    for row in _load_json("overloads.json"):
        ticket = conn.execute(
            "SELECT id FROM weigh_tickets WHERE ticket_code=?", (row["ticket_code"],)
        ).fetchone()
        if not ticket:
            continue
        exists = conn.execute(
            "SELECT id FROM overload_holds WHERE hold_key=?", (row["hold_key"],)
        ).fetchone()
        if exists:
            continue
        conn.execute(
            """INSERT INTO overload_holds(ticket_id,hold_key,overweight_t,threshold_t,
               status,opened_at,closed_at,side_lane_note) VALUES (?,?,?,?,?,?,?,?)""",
            (
                ticket["id"],
                row["hold_key"],
                float(row["overweight_t"]),
                float(row["threshold_t"]),
                row.get("status", "开放"),
                row["opened_at"],
                row.get("closed_at"),
                row.get("side_lane_note", ""),
            ),
        )


def seed_bl_manifests(conn: sqlite3.Connection) -> None:
    for row in _load_json("bl_manifests.json"):
        if conn.execute(
            "SELECT id FROM bl_manifests WHERE bl_code=?", (row["bl_code"],)
        ).fetchone():
            continue
        conn.execute(
            """INSERT INTO bl_manifests(bl_code,cargo_desc,declared_gross_t,vessel_voyage,
               status,created_at) VALUES (?,?,?,?,?,?)""",
            (
                row["bl_code"],
                row["cargo_desc"],
                float(row["declared_gross_t"]),
                row["vessel_voyage"],
                row.get("status", "在港"),
                row.get("created_at", now_iso()),
            ),
        )


def seed_gate_samples(conn: sqlite3.Connection) -> None:
    for row in _load_json("gate_releases.json"):
        ticket = conn.execute(
            "SELECT id, lane_id FROM weigh_tickets WHERE ticket_code=?",
            (row["ticket_code"],),
        ).fetchone()
        if not ticket:
            continue
        if conn.execute(
            "SELECT id FROM gate_releases WHERE release_ref=?", (row["release_ref"],)
        ).fetchone():
            continue
        conn.execute(
            """INSERT INTO gate_releases(ticket_id,lane_id,release_ref,status,officer,released_at)
               VALUES (?,?,?,?,?,?)""",
            (
                ticket["id"],
                ticket["lane_id"],
                row["release_ref"],
                row.get("status", "已放行"),
                row.get("officer", "闸口员"),
                row["released_at"],
            ),
        )


def seed_seals_sample(conn: sqlite3.Connection) -> None:
    for row in _load_json("gate_seals.json"):
        ticket = conn.execute(
            "SELECT id, generation FROM weigh_tickets WHERE ticket_code=?",
            (row["ticket_code"],),
        ).fetchone()
        if not ticket:
            continue
        if conn.execute(
            "SELECT id FROM gate_seals WHERE seal_ref=?", (row["seal_ref"],)
        ).fetchone():
            continue
        conn.execute(
            """INSERT INTO gate_seals(ticket_id,ticket_generation,manifest,seal_ref,status,sealed_at)
               VALUES (?,?,?,?,?,?)""",
            (
                ticket["id"],
                int(row.get("ticket_generation", ticket["generation"])),
                row["manifest"],
                row["seal_ref"],
                row.get("status", "已封闸"),
                row["sealed_at"],
            ),
        )


def seed_lineage_samples(conn: sqlite3.Connection) -> None:
    for row in _load_json("axle_lineage.json"):
        fr = conn.execute(
            "SELECT id FROM weigh_tickets WHERE ticket_code=?", (row["from_ticket"],)
        ).fetchone()
        if not fr:
            continue
        to_id = None
        if row.get("to_ticket"):
            to_row = conn.execute(
                "SELECT id FROM weigh_tickets WHERE ticket_code=?", (row["to_ticket"],)
            ).fetchone()
            to_id = to_row["id"] if to_row else None
        if conn.execute(
            """SELECT id FROM axle_lineage WHERE from_ticket_id=? AND edge_type=? AND detail=?""",
            (fr["id"], row["edge_type"], row["detail"]),
        ).fetchone():
            continue
        conn.execute(
            """INSERT INTO axle_lineage(from_ticket_id,to_ticket_id,edge_type,detail,created_at)
               VALUES (?,?,?,?,?)""",
            (
                fr["id"],
                to_id,
                row["edge_type"],
                row["detail"],
                row.get("created_at", now_iso()),
            ),
        )


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        seed_users(conn)
        seed_bridges(conn)
        seed_lanes(conn)
        seed_bl_manifests(conn)
        seed_tickets(conn)
        seed_overloads(conn)
        seed_gate_samples(conn)
        seed_seals_sample(conn)
        seed_lineage_samples(conn)
        conn.commit()


def dashboard_stats(conn: sqlite3.Connection) -> dict:
    bridges = conn.execute("SELECT COUNT(*) c FROM weigh_bridges").fetchone()["c"]
    lanes = conn.execute("SELECT COUNT(*) c FROM weigh_lanes").fetchone()["c"]
    tickets = conn.execute("SELECT COUNT(*) c FROM weigh_tickets").fetchone()["c"]
    open_holds = conn.execute(
        "SELECT COUNT(*) c FROM overload_holds WHERE status='开放'"
    ).fetchone()["c"]
    released = conn.execute(
        "SELECT COUNT(*) c FROM gate_releases WHERE status='已放行'"
    ).fetchone()["c"]
    sealed = conn.execute(
        "SELECT COUNT(*) c FROM gate_seals WHERE status='已封闸'"
    ).fetchone()["c"]
    bl_count = conn.execute("SELECT COUNT(*) c FROM bl_manifests").fetchone()["c"]
    stubs = {
        "customs_stub_jobs": conn.execute(
            "SELECT COUNT(*) c FROM customs_stub_jobs"
        ).fetchone()["c"],
        "crane_plan_jobs": conn.execute(
            "SELECT COUNT(*) c FROM crane_plan_jobs"
        ).fetchone()["c"],
    }
    pending = conn.execute(
        """SELECT COUNT(*) c FROM weigh_tickets
           WHERE status='旁路挂起'"""
    ).fetchone()["c"]
    return {
        "bridges": bridges,
        "lanes": lanes,
        "tickets": tickets,
        "open_overloads": open_holds,
        "gate_releases": released,
        "gate_seals": sealed,
        "bl_manifests": bl_count,
        "side_pending": pending,
        "stubs": stubs,
        "meta": PRODUCT_META,
    }