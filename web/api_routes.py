"""JSON API routes for Strategy Lab.

Programmatic endpoints over hermass_platform.strategy_lab services.
No HTML, no business logic.
"""

from __future__ import annotations

import os
import traceback
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from hermass_platform.strategy_lab.api_models import (
    BacktestResponse,
    ValidateStrategyResponse,
    ValidationErrorItem,
)
from hermass_platform.strategy_lab.audit import StrategyAuditLogger
from hermass_platform.strategy_lab.backtest_adapter import (
    BacktestResult as EngineBacktestResult,
    run_dsl_backtest,
)
from hermass_platform.strategy_lab.dsl_schema import StrategyDSL
from hermass_platform.strategy_lab.dsl_validator import (
    ValidationError as InternalValidationError,
    ValidationLevel,
    ValidationWarning as InternalValidationWarning,
    validate_dsl,
)
from hermass_platform.strategy_lab.e2e_runner import (
    NLToDSLParser,
    _hash_payload,
    _persist_trades_and_events,
)
from hermass_platform.strategy_lab.preview_service import PreviewService
from hermass_platform.strategy_lab.storage import StrategyLabStorage

from .onboarding_routes import _check_invite_token


router = APIRouter(prefix="/api/strategy-lab", tags=["strategy-lab-api"])

DSL_VERSION = "strategy_dsl_v2"

STORAGE_DB = os.getenv(
    "STRATEGY_LAB_STORAGE_DB",
    "outputs/strategy_lab/web_storage.duckdb",
)
AUDIT_DB = os.getenv(
    "STRATEGY_LAB_AUDIT_DB",
    "outputs/strategy_lab/web_audit.duckdb",
)
FOUNDATION_DB = os.getenv("FOUNDATION_DB", "data/p116_foundation.duckdb")
STATE_CUBE_DB = os.getenv("STATE_CUBE_DB", "data/state_cube.duckdb")


# ---------------------------------------------------------------------------
# Auth helper for API endpoints
# ---------------------------------------------------------------------------

def _require_api_auth(request: Request) -> None:
    """Raise 403 if invite token is missing or invalid.

    API endpoints should return 403 (not redirect) since they are
    consumed programmatically, not by browsers.
    """
    token = _check_invite_token(request)
    if token is None:
        raise HTTPException(
            status_code=403,
            detail="Authentication required. Provide a valid invite token via ?invite=TOKEN query param or cookie."
        )


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    strategy_id: str = Field(..., pattern=r"^[a-z0-9_]+$")
    natural_language: str


class ValidateRequest(BaseModel):
    dsl: dict[str, Any]
    trace_id: str | None = None


class PreviewRequest(BaseModel):
    dsl: dict[str, Any]
    trace_id: str
    data_source: str = "mock"


class BacktestRequest(BaseModel):
    dsl: dict[str, Any]
    trace_id: str
    start_date: str = "2023-01-01"
    end_date: str = "2024-12-31"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _storage() -> StrategyLabStorage:
    storage = StrategyLabStorage(STORAGE_DB)
    storage.init_schema()
    return storage


def _audit_logger() -> StrategyAuditLogger:
    logger = StrategyAuditLogger(AUDIT_DB)
    logger.init_schema()
    return logger


def _foundation_db_path() -> Path | None:
    path = Path(FOUNDATION_DB)
    return path if path.exists() else None


def _state_cube_db_path() -> Path | None:
    path = Path(STATE_CUBE_DB)
    return path if path.exists() else None


def _validation_result_to_response(
    val: Any,
    trace_id: str,
) -> ValidateStrategyResponse:
    """Convert internal ValidationResult to API response model."""

    def _err_to_item(e: InternalValidationError) -> ValidationErrorItem:
        return ValidationErrorItem(
            level=e.level.value,
            code=e.code,
            message=e.message,
            path=e.path,
        )

    def _warn_to_item(w: InternalValidationWarning) -> ValidationErrorItem:
        return ValidationErrorItem(
            level=w.level.value,
            code=w.code,
            message=w.message,
            path=w.path,
        )

    return ValidateStrategyResponse(
        trace_id=trace_id,
        dsl_version=DSL_VERSION,
        passed=val.passed,
        level=val.level.value,
        errors=[_err_to_item(e) for e in val.errors],
        warnings=[_warn_to_item(w) for w in val.warnings],
    )


def _engine_backtest_to_response(bt: EngineBacktestResult) -> BacktestResponse:
    """Convert internal BacktestResult to API response model."""
    from hermass_platform.strategy_lab.api_models import BacktestMetrics

    metrics = bt.metrics or {}
    status: Any = (
        "failed" if bt.status == "failed"
        else "partial" if bt.risk_flags
        else "success"
    )
    return BacktestResponse(
        trace_id=bt.trace_id or "",
        dsl_version=DSL_VERSION,
        status=status,
        mode=bt.mode or "light_stub",
        metrics=BacktestMetrics(
            total_return=metrics.get("total_return"),
            annual_return=metrics.get("annual_return"),
            sharpe_ratio=metrics.get("sharpe_ratio"),
            max_drawdown=metrics.get("max_drawdown"),
            profit_factor=metrics.get("profit_factor"),
            trade_count=metrics.get("trade_count"),
            total_trades=metrics.get("total_trades"),
            win_rate=metrics.get("win_rate"),
            avg_holding_days=metrics.get("avg_holding_days"),
            turnover=metrics.get("turnover"),
            cost_total=metrics.get("cost_total"),
        ),
        risk_flags=bt.risk_flags or [],
        warnings=bt.warnings or [],
        trade_count=metrics.get("trade_count"),
        daily_curve=bt.daily_curve[:100] if bt.daily_curve else [],
        trades=bt.trades[:100] if bt.trades else [],
        state_breakdown=bt.state_breakdown or {},
        data_version=bt.data_version,
        elapsed_seconds=bt.elapsed_seconds,
        errors=[],
        daily_curve_total_count=len(bt.daily_curve) if bt.daily_curve else 0,
        trades_truncated=(bt.trades is not None and len(bt.trades) > 100),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/generate")
async def api_generate(request: Request, req: GenerateRequest) -> dict[str, Any]:
    """Generate DSL from Chinese natural language and validate it."""
    _require_api_auth(request)
    trace_id = str(uuid4())
    audit = _audit_logger()
    errors: list[str] = []

    try:
        dsl = NLToDSLParser().parse(req.natural_language, req.strategy_id)
    except Exception as exc:
        errors.append(str(exc))
        audit.log_generation(
            trace_id=trace_id,
            strategy_id=req.strategy_id,
            dsl_version=DSL_VERSION,
            input_payload={"natural_language": req.natural_language},
            output_payload={"errors": errors},
            red_line_result={"passed": False, "triggered_rules": []},
        )
        raise HTTPException(status_code=400, detail={
            "trace_id": trace_id,
            "success": False,
            "errors": errors,
        }) from exc

    validation = validate_dsl(dsl)
    val_response = _validation_result_to_response(validation, trace_id)
    red_line_result = {
        "passed": not validation.has_red_line_violation,
        "triggered_rules": [
            e.code for e in validation.errors if e.level == ValidationLevel.RED_LINE
        ],
    }

    audit.log_generation(
        trace_id=trace_id,
        strategy_id=req.strategy_id,
        dsl_version=DSL_VERSION,
        input_payload={"natural_language": req.natural_language},
        output_payload=dsl.to_dict(),
        red_line_result=red_line_result,
    )
    audit.log_validation(
        trace_id=trace_id,
        strategy_id=req.strategy_id,
        dsl_version=DSL_VERSION,
        input_payload=dsl.to_dict(),
        output_payload=val_response.model_dump(),
        red_line_result=red_line_result,
    )

    # Persist strategy version so downstream backtest can reference it.
    if validation.passed:
        storage = _storage()
        storage.save_strategy_version(
            strategy_id=req.strategy_id,
            dsl=dsl.to_dict(),
            trace_id=trace_id,
            input_hash=_hash_payload({"natural_language": req.natural_language}),
            output_hash=_hash_payload(dsl.to_dict()),
        )

    return {
        "trace_id": trace_id,
        "success": validation.passed,
        "dsl": dsl.to_dict(),
        "validation": val_response.model_dump(),
        "red_line_result": red_line_result,
    }


@router.post("/validate")
async def api_validate(request: Request, req: ValidateRequest) -> dict[str, Any]:
    """Validate a DSL payload."""
    _require_api_auth(request)
    trace_id = req.trace_id or str(uuid4())
    try:
        strategy_id = req.dsl.get("strategy_id", "unknown")
        dsl_obj = StrategyDSL.model_validate(req.dsl)
    except Exception as exc:
        raise HTTPException(status_code=400, detail={
            "trace_id": trace_id,
            "success": False,
            "errors": [str(exc)],
        }) from exc

    validation = validate_dsl(dsl_obj)
    val_response = _validation_result_to_response(validation, trace_id)
    red_line_result = {
        "passed": not validation.has_red_line_violation,
        "triggered_rules": [
            e.code for e in validation.errors if e.level == ValidationLevel.RED_LINE
        ],
    }

    _audit_logger().log_validation(
        trace_id=trace_id,
        strategy_id=strategy_id,
        dsl_version=DSL_VERSION,
        input_payload=req.dsl,
        output_payload=val_response.model_dump(),
        red_line_result=red_line_result,
    )

    return {
        "trace_id": trace_id,
        "success": validation.passed,
        "validation": val_response.model_dump(),
        "red_line_result": red_line_result,
    }


@router.post("/preview")
async def api_preview(request: Request, req: PreviewRequest) -> dict[str, Any]:
    """Run condition preview for a DSL."""
    _require_api_auth(request)
    try:
        dsl_obj = StrategyDSL.model_validate(req.dsl)
    except Exception as exc:
        raise HTTPException(status_code=400, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": [str(exc)],
        }) from exc

    # 红线校验：preview 前必须重新执行 validate_dsl
    validation = validate_dsl(dsl_obj)
    if validation.has_red_line_violation:
        red_line_result = {
            "passed": False,
            "triggered_rules": [
                e.code for e in validation.errors if e.level == ValidationLevel.RED_LINE
            ],
        }
        _audit_logger().log_preview(
            trace_id=req.trace_id,
            strategy_id=dsl_obj.strategy_id,
            dsl_version=DSL_VERSION,
            input_payload=req.dsl,
            output_payload={"error": "Red line violation", "validation": validation.model_dump()},
            red_line_result=red_line_result,
        )
        raise HTTPException(status_code=403, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": [f"Red line violation: {e.code}" for e in validation.errors if e.level == ValidationLevel.RED_LINE],
            "red_line_result": red_line_result,
        })

    service = PreviewService()
    preview = service.preview(dsl_obj, data_source=req.data_source, trace_id=req.trace_id)

    _audit_logger().log_preview(
        trace_id=req.trace_id,
        strategy_id=dsl_obj.strategy_id,
        dsl_version=DSL_VERSION,
        input_payload=req.dsl,
        output_payload=preview.model_dump(),
        red_line_result={"passed": True, "triggered_rules": []},
    )

    return {
        "trace_id": req.trace_id,
        "success": preview.overall.overall_status != "failed",
        "preview": preview.model_dump(),
    }


@router.post("/backtest")
async def api_backtest(request: Request, req: BacktestRequest) -> dict[str, Any]:
    """Run light backtest for a DSL and persist results."""
    _require_api_auth(request)
    try:
        dsl_obj = StrategyDSL.model_validate(req.dsl)
    except Exception as exc:
        raise HTTPException(status_code=400, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": [str(exc)],
        }) from exc

    # 红线校验：backtest 前必须重新执行 validate_dsl
    validation = validate_dsl(dsl_obj)
    if validation.has_red_line_violation:
        red_line_result = {
            "passed": False,
            "triggered_rules": [
                e.code for e in validation.errors if e.level == ValidationLevel.RED_LINE
            ],
        }
        _audit_logger().log_backtest(
            trace_id=req.trace_id,
            strategy_id=dsl_obj.strategy_id,
            dsl_version=DSL_VERSION,
            input_payload=req.dsl,
            output_payload={"error": "Red line violation", "validation": validation.model_dump()},
            red_line_result=red_line_result,
        )
        raise HTTPException(status_code=403, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": [f"Red line violation: {e.code}" for e in validation.errors if e.level == ValidationLevel.RED_LINE],
            "red_line_result": red_line_result,
        })

    foundation = _foundation_db_path()
    state_cube = _state_cube_db_path()
    if foundation is None:
        raise HTTPException(status_code=503, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": ["Foundation DB not found"],
        })

    try:
        engine_result = run_dsl_backtest(
            dsl=dsl_obj,
            start_date=req.start_date,
            end_date=req.end_date,
            foundation_db=foundation,
            state_cube_db=state_cube,
            trace_id=req.trace_id,
        )
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": [str(exc)],
        }) from exc

    response = _engine_backtest_to_response(engine_result)
    storage = _storage()

    # Persist backtest result
    metrics_dict = dict(engine_result.metrics)
    metrics_dict["_mode"] = response.mode
    storage.save_backtest_result(
        strategy_id=dsl_obj.strategy_id,
        trace_id=req.trace_id,
        status=response.status,
        metrics=metrics_dict,
        dsl_snapshot=req.dsl,
    )

    # Persist trades and events
    try:
        _persist_trades_and_events(
            storage=storage,
            bt_result=engine_result,
            dsl=dsl_obj,
            trace_id=req.trace_id,
            strategy_id=dsl_obj.strategy_id,
        )
    except Exception:
        traceback.print_exc()

    _audit_logger().log_backtest(
        trace_id=req.trace_id,
        strategy_id=dsl_obj.strategy_id,
        dsl_version=DSL_VERSION,
        input_payload={
            "dsl": req.dsl,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "foundation_db": str(foundation),
        },
        output_payload=response.model_dump(),
        red_line_result={
            "passed": response.status != "failed",
            "triggered_rules": response.risk_flags,
        },
    )

    return {
        "trace_id": req.trace_id,
        "success": response.status != "failed",
        "backtest": response.model_dump(),
    }


@router.get("/backtest/{trace_id}")
async def api_get_backtest(request: Request, trace_id: str) -> dict[str, Any]:
    """Retrieve a persisted backtest result by trace_id."""
    _require_api_auth(request)
    storage = _storage()
    backtest = storage.get_backtest(trace_id)
    if not backtest:
        raise HTTPException(status_code=404, detail={
            "trace_id": trace_id,
            "success": False,
            "errors": ["Backtest not found"],
        })

    return {
        "trace_id": trace_id,
        "success": True,
        "backtest": {
            "status": backtest.status,
            "mode": backtest.metrics.get("_mode", "light_stub") if backtest.metrics else "light_stub",
            "metrics": backtest.metrics,
            "dsl_snapshot": backtest.dsl_snapshot,
        },
    }
