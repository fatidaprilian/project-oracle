from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    from fastapi import Depends, FastAPI, Header, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
except ImportError:
    raise ImportError(
        "FastAPI is required to run the API. Install it with: pip install fastapi uvicorn"
    )

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

# CORS Configuration
allowed_origins = os.getenv(
    "ORACLE_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DEFAULT_REGISTRY_PATH = Path("registry/parameter_change_requests.jsonl")
DEFAULT_STRATEGY_CONFIG_PATH = Path("reports/strategy-configs")

API_AUTH_ENABLED = os.getenv("ORACLE_API_AUTH_ENABLED", "false").lower() == "true"
API_AUTH_TOKEN = os.getenv("ORACLE_API_AUTH_TOKEN", "")


def require_api_auth(authorization: str | None = Header(default=None)) -> None:
    if not API_AUTH_ENABLED:
        return

    if not API_AUTH_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="ORACLE_API_AUTH_ENABLED=true but ORACLE_API_AUTH_TOKEN is empty",
        )

    expected = f"Bearer {API_AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class HealthResponse(BaseModel):
    status: str
    version: str


class ApiRootResponse(BaseModel):
    service: str
    api_docs_url: str
    health_url: str
    frontend_url: str | None = None


class ConfigReadinessResponse(BaseModel):
    auth_enabled: bool
    auth_token_configured: bool
    postgres_enabled: bool
    postgres_dsn_configured: bool
    redis_enabled: bool
    redis_url_configured: bool
    sentiment_base_url_configured: bool
    sentiment_api_key_configured: bool
    ai_analyst_base_url_configured: bool
    ai_analyst_api_key_configured: bool


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


class SymbolInfoResponse(BaseModel):
    symbol: str
    total_requests: int
    pending: int
    approved: int
    rejected: int
    ready_to_promote: int


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


@app.get("/", response_model=ApiRootResponse)
def root() -> ApiRootResponse:
    frontend_url = os.getenv("ORACLE_FRONTEND_URL", "").strip() or None
    return ApiRootResponse(
        service="Project Oracle API",
        api_docs_url="/docs",
        health_url="/health",
        frontend_url=frontend_url,
    )


@app.get("/api/v1/config/readiness", response_model=ConfigReadinessResponse)
def config_readiness() -> ConfigReadinessResponse:
    postgres_enabled = os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true"
    redis_enabled = os.getenv("ORACLE_ENABLE_REDIS", "false").lower() == "true"

    postgres_dsn = os.getenv("ORACLE_POSTGRES_DSN", "").strip()
    redis_url = os.getenv("ORACLE_REDIS_URL", "").strip()

    return ConfigReadinessResponse(
        auth_enabled=API_AUTH_ENABLED,
        auth_token_configured=bool(API_AUTH_TOKEN.strip()),
        postgres_enabled=postgres_enabled,
        postgres_dsn_configured=bool(postgres_dsn),
        redis_enabled=redis_enabled,
        redis_url_configured=bool(redis_url),
        sentiment_base_url_configured=bool(os.getenv("ORACLE_SENTIMENT_BASE_URL", "").strip()),
        sentiment_api_key_configured=bool(os.getenv("ORACLE_SENTIMENT_API_KEY", "").strip()),
        ai_analyst_base_url_configured=bool(os.getenv("ORACLE_AI_ANALYST_BASE_URL", "").strip()),
        ai_analyst_api_key_configured=bool(os.getenv("ORACLE_AI_ANALYST_API_KEY", "").strip()),
    )


@app.post("/api/v1/weekly-workflow", response_model=WorkflowResponse)
def trigger_weekly_workflow(
    symbol: str = "",
    _: None = Depends(require_api_auth),
) -> WorkflowResponse:
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
def get_governance_summary(symbol: str = "") -> GovernanceSummaryResponse:
    try:
        records = load_parameter_change_requests(DEFAULT_REGISTRY_PATH)
        summary = {
            "total": 0,
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "ready_to_promote": 0,
        }
        for record in records:
            if symbol and record.get("symbol", "") != symbol:
                continue
            summary["total"] += 1
            status = str(record.get("status", "pending")).lower()
            if status in ("pending", "approved", "rejected"):
                summary[status] += 1
            validation = record.get("validation", {})
            is_valid = bool(validation.get("is_valid", False)
                            ) if isinstance(validation, dict) else False
            if status == "approved" and is_valid:
                summary["ready_to_promote"] += 1
        return GovernanceSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve summary: {str(e)}")


@app.get("/api/v1/governance/requests", response_model=list[RequestRecord])
def list_governance_requests(symbol: str = "") -> list[RequestRecord]:
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
            if not symbol or record.get("symbol", "") == symbol
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list requests: {str(e)}")


@app.get("/api/v1/symbols", response_model=list[SymbolInfoResponse])
def list_symbols() -> list[SymbolInfoResponse]:
    try:
        records = load_parameter_change_requests(DEFAULT_REGISTRY_PATH)
        symbol_info: dict[str, dict[str, int]] = {}

        for record in records:
            symbol = record.get("symbol", "default")
            if symbol not in symbol_info:
                symbol_info[symbol] = {
                    "total": 0,
                    "pending": 0,
                    "approved": 0,
                    "rejected": 0,
                    "ready_to_promote": 0,
                }

            summary = symbol_info[symbol]
            summary["total"] += 1
            status = str(record.get("status", "pending")).lower()
            if status in ("pending", "approved", "rejected"):
                summary[status] += 1
            validation = record.get("validation", {})
            is_valid = bool(validation.get("is_valid", False)
                            ) if isinstance(validation, dict) else False
            if status == "approved" and is_valid:
                summary["ready_to_promote"] += 1

        return [
            SymbolInfoResponse(
                symbol=symbol,
                total_requests=info["total"],
                pending=info["pending"],
                approved=info["approved"],
                rejected=info["rejected"],
                ready_to_promote=info["ready_to_promote"],
            )
            for symbol, info in sorted(symbol_info.items())
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list symbols: {str(e)}")


@app.post("/api/v1/governance/approve", response_model=dict[str, bool | str])
def approve_request(
    approval: ApprovalRequest,
    _: None = Depends(require_api_auth),
) -> dict[str, bool | str]:
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
def promote_requests(_: None = Depends(require_api_auth)) -> PromoteResponse:
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
