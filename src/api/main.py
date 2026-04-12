from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from oracle.application.strategy_intelligence import (
    load_parameter_change_requests,
    promote_approved_requests,
    summarize_parameter_change_registry,
    update_request_status_by_id,
)
from oracle.application.weekly_workflow import run_weekly_workflow


app = FastAPI(
    title="Project Oracle API",
    description="Strategy intelligence and governance REST API",
    version="0.1.0",
)

# Configuration
DEFAULT_REGISTRY_PATH = Path("registry/parameter_change_requests.jsonl")
DEFAULT_STRATEGY_CONFIG_PATH = Path("reports/strategy-configs")


class HealthResponse(BaseModel):
    status: str
    version: str


class WorkflowResponse(BaseModel):
    success: bool
    ai_review_packet_path: str | None = None
    weekly_report_path: str | None = None
    promoted_config_path: str | None = None
    error: str | None = None
    details: list[str] = []


class GovernanceSummaryResponse(BaseModel):
    total: int
    pending: int
    approved: int
    rejected: int
    ready_to_promote: int


class RequestRecord(BaseModel):
    request_id: str
    status: str
    is_valid: bool | None = None
    promoted: bool = False


class ApprovalRequest(BaseModel):
    request_id: str
    status: str  # approved, rejected, or pending


class PromoteResponse(BaseModel):
    promoted: bool
    config_path: str | None = None
    reason: str | None = None


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="healthy", version="0.1.0")


@app.post("/api/v1/weekly-workflow", response_model=WorkflowResponse)
def trigger_weekly_workflow() -> WorkflowResponse:
    result = run_weekly_workflow()
    return WorkflowResponse(
        success=result.success,
        ai_review_packet_path=str(
            result.ai_review_packet_path) if result.ai_review_packet_path else None,
        weekly_report_path=str(
            result.weekly_report_path) if result.weekly_report_path else None,
        promoted_config_path=str(
            result.promoted_config_path) if result.promoted_config_path else None,
        error=result.error,
        details=result.details,
    )


@app.get("/api/v1/governance/summary", response_model=GovernanceSummaryResponse)
def get_governance_summary() -> GovernanceSummaryResponse:
    try:
        summary = summarize_parameter_change_registry(DEFAULT_REGISTRY_PATH)
        return GovernanceSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve summary: {str(e)}")


@app.get("/api/v1/governance/requests", response_model=list[RequestRecord])
def list_governance_requests() -> list[RequestRecord]:
    try:
        records = load_parameter_change_requests(DEFAULT_REGISTRY_PATH)
        return [
            RequestRecord(
                request_id=record.get("request_id", ""),
                status=record.get("status", "unknown"),
                is_valid=record.get("validation", {}).get("is_valid") if isinstance(
                    record.get("validation"), dict) else None,
                promoted=record.get("promoted", False),
            )
            for record in records
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list requests: {str(e)}")


@app.post("/api/v1/governance/approve", response_model=dict[str, bool | str])
def approve_request(approval: ApprovalRequest) -> dict[str, bool | str]:
    try:
        if approval.status not in ("approved", "rejected", "pending"):
            raise HTTPException(
                status_code=400,
                detail="Status must be one of: approved, rejected, pending",
            )
        updated = update_request_status_by_id(
            DEFAULT_REGISTRY_PATH, approval.request_id, approval.status)
        return {"updated": updated, "request_id": approval.request_id, "status": approval.status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update request: {str(e)}")


@app.post("/api/v1/governance/promote", response_model=PromoteResponse)
def promote_requests() -> PromoteResponse:
    try:
        config_path = promote_approved_requests(
            DEFAULT_REGISTRY_PATH, DEFAULT_STRATEGY_CONFIG_PATH)
        if config_path:
            return PromoteResponse(promoted=True, config_path=str(config_path))
        else:
            return PromoteResponse(promoted=False, reason="no-approved-valid-requests")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Promotion failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
