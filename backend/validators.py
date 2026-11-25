"""过磅与闸口校验。"""
from __future__ import annotations

from fastapi import HTTPException

# 第30号·回态修辰：五页（超重/过磅/放行/对账/总览）同源票态口径。
# 「旁路位」只认 weigh_tickets.status == 旁路挂起；驳回同事务回写为已裁定。
BYPASS_PENDING_STATUS = "旁路挂起"
ADJUDICATED_STATUS = "已裁定"
# 已完成裁定并继续下流的票态，对账均按“已裁定（含已放行/已封闸）”归集。
ADJUDICATED_LIKE_STATUSES = ("已裁定", "已放行", "已封闸")
# 驳回回态允许落定的目标票态。
RETURN_STATE_STATUS = "已裁定"


def is_bypass_pending(status: str | None) -> bool:
    """票是否仍挂在旁路（旁路位未抹掉）。唯一判定口径。"""
    return status == BYPASS_PENDING_STATUS


def ticket_bypass_bit(status: str | None) -> bool:
    """对外派生的显式旁路位：True=仍旁路挂起，False=已回态/未挂起。"""
    return is_bypass_pending(status)


def is_adjudicated_state(status: str | None) -> bool:
    """正式票态列是否已处于裁定之后（含放行/封闸）。"""
    return status in ADJUDICATED_LIKE_STATUSES


def adjudication_label(statuses: list[str]) -> str:
    """对账卡片/总览共用的裁定归集标签，只来源于正式票态列。"""
    if any(is_bypass_pending(s) for s in statuses):
        return BYPASS_PENDING_STATUS
    if statuses and all(is_adjudicated_state(s) for s in statuses):
        return ADJUDICATED_STATUS
    if statuses and len(set(statuses)) == 1:
        return statuses[0]
    return "票态不一"


def validate_lane_open(lane: dict) -> None:
    if lane["status"] not in ("开放", "维护"):
        raise HTTPException(409, "车道已关闭")
    if lane["status"] == "维护":
        raise HTTPException(409, "车道维护中禁止过磅")


def validate_axle_count(axles: list, axle_limit: int) -> None:
    if len(axles) < 2:
        raise HTTPException(422, "至少两根轴重")
    if len(axles) > axle_limit:
        raise HTTPException(422, f"轴数超限（限 {axle_limit} 轴）")


def validate_axle_weights(axles: list) -> tuple[float, float, float]:
    weights = []
    for a in axles:
        w = float(a.get("w", a.w if hasattr(a, "w") else 0))
        if w <= 0:
            raise HTTPException(422, "轴重须为正")
        weights.append(w)
    gross = round(sum(weights), 3)
    peak_axle = max(weights)
    spread = peak_axle - min(weights)
    return gross, peak_axle, spread


def validate_gross_cap(gross: float, max_gross: float) -> None:
    if gross > max_gross * 1.15:
        raise HTTPException(422, "毛重远超地磅额定量程")
    if gross <= 0:
        raise HTTPException(422, "毛重无效")


def validate_bl_match(declared: float, gross: float, tolerance: float = 0.08) -> bool:
    if declared <= 0:
        return False
    return abs(gross - declared) / declared <= tolerance


def adjudicate_overload(gross: float, threshold: float) -> tuple[bool, float]:
    overweight = round(gross - threshold, 3)
    return overweight > 0, max(overweight, 0.0)


def validate_ticket_mutable(ticket: dict) -> None:
    if ticket["status"] in ("已封闸", "已放行", "作废"):
        raise HTTPException(409, "票态已锁定")


def validate_ticket_sealable(ticket: dict) -> None:
    if ticket["status"] in ("已封闸", "作废"):
        raise HTTPException(409, "票态已锁定")


def validate_no_open_overload(conn, ticket_id: int) -> None:
    row = conn.execute(
        """SELECT id FROM overload_holds
           WHERE ticket_id=? AND status='开放' LIMIT 1""",
        (ticket_id,),
    ).fetchone()
    if row:
        raise HTTPException(409, "存在开放超重挂起，不得放行")


def format_manifest(ticket: dict, gross: float, generation: int) -> str:
    return (
        f"票号={ticket['ticket_code']};"
        f"提单={ticket['bl_ref']};"
        f"车牌={ticket['vehicle_plate']};"
        f"毛重={gross}t;"
        f"闸代={generation}"
    )