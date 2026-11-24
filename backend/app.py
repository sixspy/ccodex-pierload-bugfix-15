"""港口过磅闸口 — FastAPI 入口。"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from audit_svc import router as audit_router
from auth import router as auth_router
from axle_lineage_svc import router as lineage_router
from bl_svc import router as bl_router
from bridges_svc import router as bridges_router
from crane_plan_svc import router as crane_router
from customs_stub_svc import router as customs_router
from db import FRONTEND, PRODUCT_META, init_db
from gate_svc import router as gate_router
from lanes_svc import router as lanes_router
from locks import router as locks_router
from overload_svc import router as overload_router
from reconcile_svc import router as reconcile_router
from seal_svc import router as seal_router
from tickets_svc import router as tickets_router

PRODUCT = "港口过磅闸口"
SKELETON = PRODUCT_META["skeleton"]

app = FastAPI(title=PRODUCT, description=SKELETON)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (
    auth_router,
    bridges_router,
    lanes_router,
    tickets_router,
    overload_router,
    gate_router,
    seal_router,
    bl_router,
    lineage_router,
    reconcile_router,
    locks_router,
    audit_router,
    customs_router,
    crane_router,
):
    app.include_router(r)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    from db import DB_PATH, connect

    with connect() as conn:
        bridges = conn.execute(
            "SELECT COUNT(*) c FROM weigh_bridges"
        ).fetchone()["c"]
        lanes = conn.execute("SELECT COUNT(*) c FROM weigh_lanes").fetchone()["c"]
        tickets = conn.execute(
            "SELECT COUNT(*) c FROM weigh_tickets"
        ).fetchone()["c"]
        tables = conn.execute(
            "SELECT COUNT(*) c FROM sqlite_master WHERE type='table'"
        ).fetchone()["c"]
    return {
        "ok": True,
        "product": PRODUCT,
        "skeleton": SKELETON,
        "bridges": bridges,
        "lanes": lanes,
        "tickets": tickets,
        "tables": tables,
        "db": str(DB_PATH),
        "meta": PRODUCT_META,
    }


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")