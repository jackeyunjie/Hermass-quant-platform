"""Strategy Lab Web UI routes.

Thin HTTP layer over hermass_platform.strategy_lab services.
No business logic, no direct DuckDB access, no LLM calls.
"""

from __future__ import annotations

import hashlib
import os
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from hermass_platform.strategy_lab.api_models import (
    BacktestMetrics,
    BacktestResponse,
    ValidationErrorItem,
    ValidateStrategyResponse,
)
from hermass_platform.strategy_lab.audit import StrategyAuditLogger
from hermass_platform.strategy_lab.backtest_adapter import (
    BacktestResult as EngineBacktestResult,
    run_dsl_backtest,
)
from hermass_platform.strategy_lab.backtest_evidence import (
    build_trade_event_evidence,
    build_trade_records,
)
from hermass_platform.strategy_lab.dsl_schema import StrategyDSL
from hermass_platform.strategy_lab.e2e_runner import _persist_trades_and_events
from hermass_platform.strategy_lab.dsl_validator import ValidationLevel, validate_dsl
from hermass_platform.strategy_lab.e2e_runner import NLToDSLParser
from hermass_platform.strategy_lab.preview_service import PreviewService
from hermass_platform.strategy_lab.storage import StrategyLabStorage

from .onboarding_routes import _check_invite_token, _set_invite_cookie, INVITE_COOKIE_NAME

from .data_readiness import (
    default_backtest_run_tag,
    load_data_readiness,
    readiness_badge_class,
)

# ---------------------------------------------------------------------------
# Configuration & helpers
# ---------------------------------------------------------------------------

STORAGE_DB = os.getenv(
    "STRATEGY_LAB_STORAGE_DB",
    "outputs/strategy_lab/web_storage.duckdb",
)
AUDIT_DB = os.getenv(
    "STRATEGY_LAB_AUDIT_DB",
    "outputs/strategy_lab/web_audit.duckdb",
)
FOUNDATION_DB = os.getenv(
    "FOUNDATION_DB",
    "data/p116_foundation.duckdb",
)
STATE_CUBE_DB = os.getenv(
    "STATE_CUBE_DB",
    "data/state_cube.duckdb",
)

DSL_VERSION = "strategy_dsl_v2"

router = APIRouter(prefix="/strategy-lab", tags=["strategy-lab"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _disclaimer() -> str:
    return "本工具仅用于策略研究与技术验证，不构成投资建议。回测结果不代表未来收益。"


def _require_auth_or_redirect(request: Request) -> str | RedirectResponse:
    """Check invite token; return token if valid, or redirect to login page."""
    token = _check_invite_token(request)
    if token is None:
        # Not authenticated - redirect to login page with return URL
        current_path = str(request.url.path)
        if request.url.query:
            current_path += "?" + str(request.url.query)
        return RedirectResponse(
            url=f"/onboarding/login?next={current_path}",
            status_code=303,
        )
    return token


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


def _readiness_context() -> dict[str, Any]:
    """Build template context keys for data readiness display."""
    readiness = load_data_readiness()
    verdict = readiness.get("verdict", "NOT_READY")
    ui = readiness.get("ui_display", {})
    return {
        "readiness_verdict": verdict,
        "readiness_badge": readiness_badge_class(verdict),
        "readiness_message": ui.get("zh", ""),
        "readiness_next_steps": readiness.get("next_steps", []),
        "default_run_tag": default_backtest_run_tag(readiness),
    }


def _ctx(request: Request, **kwargs: Any) -> dict[str, Any]:
    """Merge base template context with readiness keys."""
    base = {"request": request}
    base.update(kwargs)
    base.update(_readiness_context())
    return base


def _to_dict(obj: Any) -> dict[str, Any]:
    """Serialize Pydantic model or dataclass to dict."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[union-attr]
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    raise TypeError(f"Cannot serialize {type(obj)}")


def _run_tag_from_backtest(bt: EngineBacktestResult | None) -> str:
    if bt is None:
        return default_backtest_run_tag()
    if bt.mode == "light_real_v1":
        return "light_real_v1"
    return "light_stub"


def _stored_backtest_mode(metrics: dict[str, Any] | None) -> str:
    """Infer persisted run tag from stored backtest metrics."""
    if not metrics:
        return default_backtest_run_tag()
    return str(metrics.get("_mode") or default_backtest_run_tag())


def _engine_backtest_to_response(
    bt: EngineBacktestResult,
) -> BacktestResponse:
    """Convert internal backtest dataclass to API response model."""
    metrics = bt.metrics or {}
    return BacktestResponse(
        trace_id=bt.trace_id or "",
        dsl_version=DSL_VERSION,
        status=bt.status,  # type: ignore[arg-type]
        mode=bt.mode,  # type: ignore[arg-type]
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
        trade_count=(bt.metrics or {}).get("trade_count") if bt.metrics else None,
        daily_curve=bt.daily_curve[:100] if bt.daily_curve else [],
        trades=bt.trades[:100] if bt.trades else [],
        state_breakdown=bt.state_breakdown or {},
        data_version=bt.data_version,
        elapsed_seconds=bt.elapsed_seconds,
        errors=[],
        daily_curve_total_count=len(bt.daily_curve) if bt.daily_curve else 0,
        trades_truncated=(bt.trades is not None and len(bt.trades) > 100),
    )


def _validation_result_to_response(
    val: Any,
    trace_id: str,
) -> ValidateStrategyResponse:
    """Convert internal ValidationResult to API ValidateStrategyResponse."""
    from hermass_platform.strategy_lab.dsl_validator import (
        ValidationError as InternalValidationError,
        ValidationWarning as InternalValidationWarning,
    )

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

    red_line_errors = [e for e in val.errors if e.level == ValidationLevel.RED_LINE]
    red_line_result = {
        "passed": len(red_line_errors) == 0,
        "triggered_rules": [e.code for e in red_line_errors],
    }

    return ValidateStrategyResponse(
        trace_id=trace_id,
        passed=val.passed,
        level=val.level.value,
        errors=[_err_to_item(e) for e in val.errors],
        warnings=[_warn_to_item(w) for w in val.warnings],
        red_line_result=red_line_result,
    )


# ---------------------------------------------------------------------------
# Page 0: Visual Strategy Builder (React Node-based)
# ---------------------------------------------------------------------------

@router.get("/builder")
async def builder_page(request: Request) -> HTMLResponse:
    """Render the visual strategy builder page."""
    auth = _require_auth_or_redirect(request)
    if isinstance(auth, RedirectResponse):
        return auth

    return templates.TemplateResponse(
        request,
        "strategy_builder.html",
        _ctx(request),
    )


# ---------------------------------------------------------------------------
# Page 1: Strategy Structuring
# ---------------------------------------------------------------------------

@router.get("/structuring")
async def structuring_page(request: Request) -> HTMLResponse:
    """Render the strategy structuring form."""
    auth = _require_auth_or_redirect(request)
    if isinstance(auth, RedirectResponse):
        return auth

    return templates.TemplateResponse(
        request,
        "structuring.html",
        _ctx(
            request,
            trace_id="",
            strategy_id="",
            natural_language="",
            dsl=None,
            generation_errors=[],
            validation=None,
            red_line_result={"passed": True, "triggered_rules": []},
            run_tag=default_backtest_run_tag(),
            disclaimer=_disclaimer(),
        ),
    )


@router.post("/structuring")
async def structuring_submit(
    request: Request,
    strategy_id: str = Form(...),
    natural_language: str = Form(...),
) -> HTMLResponse:
    """Parse NL to DSL, validate, save version, log audit."""
    trace_id = str(uuid4())
    dsl: dict[str, Any] | None = None
    generation_errors: list[str] = []
    validation: ValidateStrategyResponse | None = None
    red_line_result: dict[str, Any] = {"passed": True, "triggered_rules": []}

    try:
        parser = NLToDSLParser()
        dsl_obj = parser.parse(natural_language, strategy_id)
        dsl = dsl_obj.to_dict()

        internal_validation = validate_dsl(dsl_obj)
        validation = _validation_result_to_response(internal_validation, trace_id)
        red_line_result = validation.red_line_result

        # Persist strategy version
        storage = _storage()
        storage.save_strategy_version(
            strategy_id=strategy_id,
            dsl=dsl,
            trace_id=trace_id,
            input_hash=hashlib.sha256(natural_language.encode()).hexdigest()[:16],
            output_hash=hashlib.sha256(
                dsl_obj.model_dump_json().encode()
            ).hexdigest()[:16],
        )

        # Audit generation + validation
        audit = _audit_logger()
        audit.log_generation(
            trace_id=trace_id,
            strategy_id=strategy_id,
            dsl_version=DSL_VERSION,
            input_payload={"strategy_id": strategy_id, "natural_language": natural_language},
            output_payload=dsl,
            red_line_result=red_line_result,
        )
        audit.log_validation(
            trace_id=trace_id,
            strategy_id=strategy_id,
            dsl_version=DSL_VERSION,
            input_payload=dsl,
            output_payload={
                "passed": validation.passed,
                "level": validation.level,
                "errors": [e.model_dump() for e in validation.errors],
            },
            red_line_result=red_line_result,
        )
    except Exception as exc:  # noqa: BLE001
        generation_errors.append(str(exc))
        # Still log generation failure if we have a trace_id
        try:
            audit = _audit_logger()
            audit.log_generation(
                trace_id=trace_id,
                strategy_id=strategy_id,
                dsl_version=DSL_VERSION,
                input_payload={"strategy_id": strategy_id, "natural_language": natural_language},
                output_payload={"error": str(exc)},
                red_line_result={"passed": False, "triggered_rules": []},
            )
        except Exception:  # noqa: BLE001
            pass

    return templates.TemplateResponse(
        request,
        "structuring.html",
        _ctx(
            request,
            trace_id=trace_id,
            strategy_id=strategy_id,
            natural_language=natural_language,
            dsl=dsl,
            generation_errors=generation_errors,
            validation=validation.model_dump() if validation else None,
            red_line_result=red_line_result,
            run_tag=default_backtest_run_tag(),
            disclaimer=_disclaimer(),
        ),
    )


# ---------------------------------------------------------------------------
# Page 2: Strategy Diagnosis
# ---------------------------------------------------------------------------

@router.get("/diagnosis")
async def diagnosis_page(
    request: Request,
    trace_id: str | None = Query(None),
) -> HTMLResponse:
    """Render the diagnosis form, optionally preloaded by trace_id."""
    auth = _require_auth_or_redirect(request)
    if isinstance(auth, RedirectResponse):
        return auth

    dsl_snapshot: dict[str, Any] | None = None
    backtest_summary: dict[str, Any] | None = None
    errors: list[str] = []

    if trace_id:
        storage = _storage()
        version = storage.get_strategy_version_by_trace_id(trace_id)
        if version:
            dsl_snapshot = version.dsl
        backtest = storage.get_backtest(trace_id)
        if backtest:
            backtest_summary = {
                "status": backtest.status,
                "mode": _stored_backtest_mode(backtest.metrics),
                "metrics": backtest.metrics,
            }
        if not version and not backtest:
            errors.append(f"未找到 trace_id={trace_id} 的策略版本或回测记录")

    return templates.TemplateResponse(
        request,
        "diagnosis.html",
        _ctx(
            request,
            trace_id=trace_id or "",
            dsl_snapshot=dsl_snapshot,
            preview=None,
            backtest=backtest_summary,
            run_tag=backtest_summary["mode"] if backtest_summary else default_backtest_run_tag(),
            errors=errors,
            disclaimer=_disclaimer(),
        ),
    )


@router.post("/diagnosis/run")
async def diagnosis_run(
    request: Request,
    trace_id: str = Form(...),
    start_date: str = Form("2023-01-01"),
    end_date: str = Form("2024-12-31"),
    stage: str = Form(...),  # "preview" or "backtest"
) -> HTMLResponse:
    """Run preview or backtest for a previously saved strategy."""
    errors: list[str] = []
    preview: dict[str, Any] | None = None
    backtest_summary: dict[str, Any] | None = None
    dsl_snapshot: dict[str, Any] | None = None
    run_tag = default_backtest_run_tag()

    storage = _storage()
    version = storage.get_strategy_version_by_trace_id(trace_id)
    if not version:
        errors.append(f"未找到 trace_id={trace_id} 的策略版本")
        return templates.TemplateResponse(
            request,
            "diagnosis.html",
            _ctx(
                request,
                trace_id=trace_id,
                dsl_snapshot=dsl_snapshot,
                preview=preview,
                backtest=backtest_summary,
                run_tag=run_tag,
                errors=errors,
                disclaimer=_disclaimer(),
            ),
        )

    dsl_snapshot = version.dsl
    try:
        dsl_obj = StrategyDSL.model_validate(dsl_snapshot)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"DSL 反序列化失败: {exc}")
        return templates.TemplateResponse(
            request,
            "diagnosis.html",
            _ctx(
                request,
                trace_id=trace_id,
                dsl_snapshot=dsl_snapshot,
                preview=preview,
                backtest=backtest_summary,
                run_tag=run_tag,
                errors=errors,
                disclaimer=_disclaimer(),
            ),
        )

    audit = _audit_logger()
    strategy_id = dsl_snapshot.get("strategy_id", "unknown")

    # 红线校验：preview/backtest 前必须重新执行 validate_dsl
    validation = validate_dsl(dsl_obj)
    if validation.has_red_line_violation:
        red_line_result = {
            "passed": False,
            "triggered_rules": [
                e.code for e in validation.errors if e.level == ValidationLevel.RED_LINE
            ],
        }
        errors.append(f"Red line violation: {[e.code for e in validation.errors if e.level == ValidationLevel.RED_LINE]}")
        if stage == "preview":
            audit.log_preview(
                trace_id=trace_id,
                strategy_id=strategy_id,
                dsl_version=DSL_VERSION,
                input_payload=dsl_snapshot,
                output_payload={"error": "Red line violation", "validation": validation.model_dump()},
                red_line_result=red_line_result,
            )
        else:
            audit.log_backtest(
                trace_id=trace_id,
                strategy_id=strategy_id,
                dsl_version=DSL_VERSION,
                input_payload=dsl_snapshot,
                output_payload={"error": "Red line violation", "validation": validation.model_dump()},
                red_line_result=red_line_result,
            )
        return templates.TemplateResponse(
            request,
            "diagnosis.html",
            _ctx(
                request,
                trace_id=trace_id,
                dsl_snapshot=dsl_snapshot,
                preview=None,
                backtest_summary=None,
                errors=errors,
                run_tag=run_tag,
                disclaimer=_disclaimer(),
            ),
        )

    try:
        if stage == "preview":
            service = PreviewService()
            preview_response = service.preview(
                dsl=dsl_obj,
                data_source="mock",
                trace_id=trace_id,
            )
            preview = preview_response.model_dump()
            audit.log_preview(
                trace_id=trace_id,
                strategy_id=strategy_id,
                dsl_version=DSL_VERSION,
                input_payload=dsl_snapshot,
                output_payload=preview,
                red_line_result={"passed": True, "triggered_rules": []},
            )
        elif stage == "backtest":
            foundation = _foundation_db_path()
            state_cube = _state_cube_db_path()
            engine_result = run_dsl_backtest(
                dsl=dsl_obj,
                start_date=start_date,
                end_date=end_date,
                foundation_db=foundation,
                state_cube_db=state_cube,
                trace_id=trace_id,
            )
            response = _engine_backtest_to_response(engine_result)
            backtest_summary = response.model_dump()
            run_tag = _run_tag_from_backtest(engine_result)

            # Persist backtest + trades + events
            persisted_metrics = response.metrics.model_dump()
            persisted_metrics["_mode"] = response.mode
            storage.save_backtest_result(
                strategy_id=strategy_id,
                trace_id=trace_id,
                status=response.status,
                metrics=persisted_metrics,
                dsl_snapshot=dsl_snapshot,
            )
            # Persist full trade records and event evidence from signal frame.
            # Use the engine result (not the truncated response) so storage holds
            # the complete set and events satisfy the foreign-key constraint.
            try:
                _persist_trades_and_events(
                    storage=storage,
                    bt_result=engine_result,
                    dsl=dsl_obj,
                    trace_id=trace_id,
                    strategy_id=strategy_id,
                )
            except Exception as persist_exc:  # noqa: BLE001
                errors.append(f"交易证据保存失败: {persist_exc}")
                traceback.print_exc()

            audit.log_backtest(
                trace_id=trace_id,
                strategy_id=strategy_id,
                dsl_version=DSL_VERSION,
                input_payload={
                    "dsl": dsl_snapshot,
                    "start_date": start_date,
                    "end_date": end_date,
                    "foundation_db": str(foundation) if foundation else None,
                },
                output_payload=backtest_summary,
                red_line_result={"passed": response.status != "failed", "triggered_rules": response.risk_flags},
            )
        else:
            errors.append(f"不支持的 stage: {stage}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{stage} 执行失败: {exc}")
        traceback.print_exc()

    return templates.TemplateResponse(
        request,
        "diagnosis.html",
        _ctx(
            request,
            trace_id=trace_id,
            dsl_snapshot=dsl_snapshot,
            preview=preview,
            backtest=backtest_summary,
            run_tag=run_tag,
            errors=errors,
            disclaimer=_disclaimer(),
        ),
    )


# ---------------------------------------------------------------------------
# Page 3: Evidence Lab
# ---------------------------------------------------------------------------

@router.get("/evidence")
async def evidence_page(
    request: Request,
    trace_id: str | None = Query(None),
) -> HTMLResponse:
    """Render audit timeline and stored trade evidence for a trace_id."""
    auth = _require_auth_or_redirect(request)
    if isinstance(auth, RedirectResponse):
        return auth

    errors: list[str] = []
    audit_records: list[dict[str, Any]] = []
    backtest_summary: dict[str, Any] | None = None
    trades: list[dict[str, Any]] = []
    trade_events: list[dict[str, Any]] = []

    if trace_id:
        try:
            audit = _audit_logger()
            audit_records = [_to_dict(r) for r in audit.list_by_trace_id(trace_id)]

            storage = _storage()
            backtest = storage.get_backtest(trace_id)
            if backtest:
                backtest_summary = {
                    "status": backtest.status,
                    "mode": _stored_backtest_mode(backtest.metrics),
                    "metrics": backtest.metrics,
                    "dsl_snapshot": backtest.dsl_snapshot,
                }
            trades = [_to_dict(t) for t in storage.list_trades(trace_id=trace_id)]
            trade_events = [_to_dict(e) for e in storage.list_trade_events(trace_id=trace_id)]

            if not audit_records and not backtest_summary and not trades:
                errors.append(f"未找到 trace_id={trace_id} 的任何记录")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"查询证据失败: {exc}")
            traceback.print_exc()

    return templates.TemplateResponse(
        request,
        "evidence.html",
        _ctx(
            request,
            trace_id=trace_id or "",
            audit_records=audit_records,
            backtest_summary=backtest_summary,
            trades=trades,
            trade_events=trade_events,
            errors=errors,
            run_tag=backtest_summary["mode"] if backtest_summary else default_backtest_run_tag(),
            disclaimer=_disclaimer(),
        ),
    )
