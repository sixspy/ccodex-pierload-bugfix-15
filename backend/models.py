"""Pydantic 入参模型。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class BridgeIn(BaseModel):
    bridge_code: str = Field(min_length=3, max_length=32)
    pier_zone: str
    name: str
    max_gross_t: float = Field(gt=0, lt=200)
    axle_limit: int = Field(ge=2, le=12)
    status: str = "运行"


class LaneIn(BaseModel):
    lane_code: str
    bridge_id: int
    direction: str
    overload_threshold_t: float = Field(gt=0)
    side_lane_ref: str = ""
    status: str = "开放"


class AxleWeight(BaseModel):
    axle: int
    w: float = Field(gt=0)


class TicketIn(BaseModel):
    lane_id: int
    bl_ref: str
    vehicle_plate: str
    axle_weights: list[AxleWeight]
    ticket_code: str | None = None


class OverloadOpenIn(BaseModel):
    ticket_id: int
    threshold_t: float | None = None
    side_lane_note: str = ""


class OverloadCloseIn(BaseModel):
    hold_id: int
    note: str = ""


class GateReleaseIn(BaseModel):
    ticket_id: int
    officer: str = "闸口员"


class SealIn(BaseModel):
    ticket_id: int
    manifest: str | None = None


class BlIn(BaseModel):
    bl_code: str
    cargo_desc: str
    declared_gross_t: float
    vessel_voyage: str


class LineageIn(BaseModel):
    from_ticket_id: int
    to_ticket_id: int | None = None
    edge_type: str
    detail: str


class StubJobIn(BaseModel):
    mode: str = "dry_run"
    detail: str = ""