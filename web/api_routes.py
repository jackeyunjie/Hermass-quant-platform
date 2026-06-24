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
from hermass_platform.strategy_lab.multi_timeframe_engine import (
    MultiPeriodEngine,
    MultiTimeframeEngine,
    run_multi_period_backtest,
    run_multi_timeframe_backtest,
)
from hermass_platform.strategy_lab.preview_service import PreviewService
from hermass_platform.strategy_lab.storage import StrategyLabStorage

from .onboarding_routes import _check_invite_token


router = APIRouter(prefix="/api/strategy-lab", tags=["strategy-lab-api"])

DSL_VERSION = "strategy_dsl_v2"

STORAGE_DB = os.getenv(
    "STRATEGY_LAB_STORAGE_DB",
    os.path.join(os.path.dirname(__file__), "..", "outputs", "strategy_lab", "mvp_e2e_acceptance_storage.duckdb"),
)
AUDIT_DB = os.getenv(
    "STRATEGY_LAB_AUDIT_DB",
    os.path.join(os.path.dirname(__file__), "..", "outputs", "strategy_lab", "mvp_e2e_acceptance_audit.duckdb"),
)
FOUNDATION_DB = os.getenv(
    "FOUNDATION_DB",
    os.path.join(os.path.dirname(__file__), "..", "outputs", "benchmarks", "_synthetic_tmp.duckdb"),
)
STATE_CUBE_DB = os.getenv(
    "STATE_CUBE_DB",
    os.path.join(os.path.dirname(__file__), "..", "outputs", "strategy_lab", "mvp_e2e_acceptance_storage.duckdb"),
)


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    natural_language: str
    strategy_id: str = ""


class ValidateRequest(BaseModel):
    dsl: dict[str, Any]
    trace_id: str = ""


class PreviewRequest(BaseModel):
    dsl: dict[str, Any]
    trace_id: str
    data_source: str = "mock"


class BacktestRequest(BaseModel):
    dsl: dict[str, Any]
    trace_id: str
    start_date: str = "2023-01-01"
    end_date: str = "2024-12-31"


class MultiTimeframeBacktestRequest(BaseModel):
    dsl: dict[str, Any]
    trace_id: str
    start_date: str = "2023-01-01"
    end_date: str = "2024-12-31"
    timeframes: list[str] = Field(default_factory=lambda: ["D1", "W1"])
    primary_timeframe: str = "D1"
    require_all_timeframes: bool = False


class BacktestPeriodInput(BaseModel):
    start_date: str
    end_date: str
    label: str = ""


class MultiPeriodBacktestRequest(BaseModel):
    dsl: dict[str, Any]
    trace_id: str
    periods: list[BacktestPeriodInput]
    aggregate_method: str = "concat"
    min_periods_required: int = 1


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
            field=e.field,
        )

    def _warn_to_item(w: InternalValidationWarning) -> ValidationErrorItem:
        return ValidationErrorItem(
            level="warning",
            code=w.code,
            message=w.message,
            field=w.field,
        )

    return ValidateStrategyResponse(
        trace_id=trace_id,
        passed=val.passed,
        level=val.level.value,
        errors=[_err_to_item(e) for e in val.errors],
        warnings=[_warn_to_item(w) for w in val.warnings],
        has_red_line_violation=val.has_red_line_violation,
    )


def _engine_backtest_to_response(bt: EngineBacktestResult) -> BacktestResponse:
    """Convert EngineBacktestResult to API response model."""
    return BacktestResponse(
        trace_id=bt.trace_id or "",
        status=bt.status,
        mode=bt.mode,
        metrics=bt.metrics,
        total_trades=len(bt.trades) if bt.trades else 0,
        trades=bt.trades[:100] if bt.trades else [],
        risk_flags=bt.risk_flags,
        state_breakdown=bt.state_breakdown or {},
        data_version=bt.data_version,
        elapsed_seconds=bt.elapsed_seconds,
        errors=[],
        daily_curve_total_count=len(bt.daily_curve) if bt.daily_curve else 0,
        trades_truncated=(bt.trades is not None and len(bt.trades) > 100),
    )


def _require_api_auth(request: Request) -> None:
    """Require authentication for API endpoints."""
    token = _check_invite_token(request)
    if token is None:
        raise HTTPException(
            status_code=403,
            detail="Authentication required. Please provide a valid invite token via cookie or query parameter.",
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


@router.post("/backtest/multi-timeframe")
async def api_multi_timeframe_backtest(request: Request, req: MultiTimeframeBacktestRequest) -> dict[str, Any]:
    """Run multi-timeframe backtest across D1/W1/MN1 simultaneously."""
    _require_api_auth(request)
    try:
        dsl_obj = StrategyDSL.model_validate(req.dsl)
    except Exception as exc:
        raise HTTPException(status_code=400, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": [str(exc)],
        }) from exc

    # 红线校验
    validation = validate_dsl(dsl_obj)
    if validation.has_red_line_violation:
        red_line_result = {
            "passed": False,
            "triggered_rules": [
                e.code for e in validation.errors if e.level == ValidationLevel.RED_LINE
            ],
        }
        raise HTTPException(status_code=403, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": [f"Red line violation: {e.code}" for e in validation.errors if e.level == ValidationLevel.RED_LINE],
            "red_line_result": red_line_result,
        })

    # Update DSL with multi-timeframe config
    dsl_dict = dsl_obj.model_dump()
    dsl_dict["multi_timeframe"] = {
        "timeframes": req.timeframes,
        "primary_timeframe": req.primary_timeframe,
        "require_all_timeframes": req.require_all_timeframes,
    }
    dsl_obj = StrategyDSL.model_validate(dsl_dict)

    foundation = _foundation_db_path()
    if foundation is None:
        raise HTTPException(status_code=503, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": ["Foundation DB not found"],
        })

    try:
        result = run_multi_timeframe_backtest(
            dsl=dsl_obj,
            start_date=req.start_date,
            end_date=req.end_date,
            foundation_db=foundation,
        )
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": [str(exc)],
        }) from exc

    # Convert to response
    timeframe_results = []
    for tf in result.timeframe_results:
        timeframe_results.append({
            "timeframe": tf.timeframe,
            "signal_count": tf.signal_count,
            "agreement_rate": tf.agreement_rate,
            "metrics": tf.result.metrics if tf.result.metrics else {},
            "status": tf.result.status,
        })

    _audit_logger().log_backtest(
        trace_id=req.trace_id,
        strategy_id=dsl_obj.strategy_id,
        dsl_version=DSL_VERSION,
        input_payload={
            "dsl": req.dsl,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "timeframes": req.timeframes,
            "primary_timeframe": req.primary_timeframe,
        },
        output_payload={
            "overall_metrics": result.overall_metrics,
            "timeframe_results": timeframe_results,
            "cross_timeframe_signals": result.cross_timeframe_signals,
        },
        red_line_result={"passed": True, "triggered_rules": []},
    )

    return {
        "trace_id": req.trace_id,
        "success": result.status != "failed",
        "multi_timeframe": {
            "primary_timeframe": result.primary_timeframe,
            "overall_metrics": result.overall_metrics,
            "timeframe_results": timeframe_results,
            "cross_timeframe_signals": result.cross_timeframe_signals,
            "elapsed_seconds": result.elapsed_seconds,
            "status": result.status,
            "warnings": result.warnings,
        },
    }


@router.post("/backtest/multi-period")
async def api_multi_period_backtest(request: Request, req: MultiPeriodBacktestRequest) -> dict[str, Any]:
    """Run multi-period backtest across multiple date ranges."""
    _require_api_auth(request)
    try:
        dsl_obj = StrategyDSL.model_validate(req.dsl)
    except Exception as exc:
        raise HTTPException(status_code=400, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": [str(exc)],
        }) from exc

    # 红线校验
    validation = validate_dsl(dsl_obj)
    if validation.has_red_line_violation:
        red_line_result = {
            "passed": False,
            "triggered_rules": [
                e.code for e in validation.errors if e.level == ValidationLevel.RED_LINE
            ],
        }
        raise HTTPException(status_code=403, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": [f"Red line violation: {e.code}" for e in validation.errors if e.level == ValidationLevel.RED_LINE],
            "red_line_result": red_line_result,
        })

    # Update DSL with multi-period config
    dsl_dict = dsl_obj.model_dump()
    dsl_dict["multi_period"] = {
        "periods": [
            {"start_date": p.start_date, "end_date": p.end_date, "label": p.label}
            for p in req.periods
        ],
        "aggregate_method": req.aggregate_method,
        "min_periods_required": req.min_periods_required,
    }
    dsl_obj = StrategyDSL.model_validate(dsl_dict)

    foundation = _foundation_db_path()
    if foundation is None:
        raise HTTPException(status_code=503, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": ["Foundation DB not found"],
        })

    try:
        result = run_multi_period_backtest(
            dsl=dsl_obj,
            foundation_db=foundation,
        )
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={
            "trace_id": req.trace_id,
            "success": False,
            "errors": [str(exc)],
        }) from exc

    # Convert to response
    period_results = []
    for p in result.period_results:
        period_results.append({
            "label": p.period_label,
            "start_date": p.start_date,
            "end_date": p.end_date,
            "metrics": p.result.metrics if p.result.metrics else {},
            "trade_count": len(p.result.trades) if p.result.trades else 0,
            "status": p.status,
        })

    _audit_logger().log_backtest(
        trace_id=req.trace_id,
        strategy_id=dsl_obj.strategy_id,
        dsl_version=DSL_VERSION,
        input_payload={
            "dsl": req.dsl,
            "periods": [p.model_dump() for p in req.periods],
            "aggregate_method": req.aggregate_method,
        },
        output_payload={
            "overall_metrics": result.overall_metrics,
            "period_results": period_results,
            "period_comparison": result.period_comparison,
        },
        red_line_result={"passed": True, "triggered_rules": []},
    )

    return {
        "trace_id": req.trace_id,
        "success": result.status != "failed",
        "multi_period": {
            "overall_metrics": result.overall_metrics,
            "period_results": period_results,
            "period_comparison": result.period_comparison,
            "elapsed_seconds": result.elapsed_seconds,
            "status": result.status,
            "warnings": result.warnings,
        },
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
