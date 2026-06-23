"""API Models - Pydantic models for Strategy Lab API requests/responses.

These models define the contract between the Web layer (not implemented here)
and the service layer. All models are JSON-serializable and include audit fields.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .condition_registry import PreviewSupport
from .dsl_schema import StrategyDSL
from .dsl_validator import ValidationLevel


# ---------------------------------------------------------------------------
# Preview Models
# ---------------------------------------------------------------------------

class ConditionPreviewItem(BaseModel):
    """Preview result for a single condition."""

    model_config = ConfigDict(extra="forbid")

    condition_type: str = Field(..., description="Condition type name")
    params: dict[str, Any] = Field(default_factory=dict, description="Condition parameters")
    preview_support: str = Field(
        default=PreviewSupport.FULLY_SUPPORTED.value,
        description="Preview support classification",
    )
    has_context_required: bool = Field(
        default=False,
        description="Whether this condition requires backtest context",
    )
    estimated_hits: int | None = Field(
        default=None,
        description="Estimated hit count (None if not applicable)",
    )
    notes: str = Field(
        default="",
        description="Human-readable notes about this condition's preview",
    )


class SectionPreviewItem(BaseModel):
    """Preview result for a strategy section (entry/exit/filters)."""

    model_config = ConfigDict(extra="forbid")

    section: Literal["entry", "exit", "filters"] = Field(..., description="Section name")
    conditions: list[ConditionPreviewItem] = Field(
        default_factory=list,
        description="Preview results for each condition in this section",
    )
    total_estimated_hits: int | None = Field(
        default=None,
        description="Aggregated estimated hits for the section",
    )
    has_context_required: bool = Field(
        default=False,
        description="Whether any condition in this section requires context",
    )


class PreviewOverallItem(BaseModel):
    """Overall preview summary."""

    model_config = ConfigDict(extra="forbid")

    overall_status: Literal["success", "partial", "failed"] = Field(
        ..., description="Overall preview status",
    )
    total_sections: int = Field(default=0, description="Number of sections previewed")
    sections_with_context_required: int = Field(
        default=0,
        description="Number of sections requiring backtest context",
    )
    total_estimated_hits: int | None = Field(
        default=None,
        description="Overall estimated hit count across all sections",
    )
    errors: list[str] = Field(default_factory=list, description="Any preview errors")
    warnings: list[str] = Field(default_factory=list, description="Any preview warnings")


class PreviewRequest(BaseModel):
    """Request to preview a strategy's conditions."""

    model_config = ConfigDict(extra="forbid")

    dsl: StrategyDSL = Field(..., description="Strategy DSL to preview")
    data_source: Literal["mock", "duckdb"] = Field(
        default="mock",
        description="Data source for preview",
    )
    trace_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique trace ID for audit trail",
    )


class PreviewResponse(BaseModel):
    """Response from strategy preview."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(..., description="Trace ID from request")
    dsl_version: str = Field(
        default="strategy_dsl_v2",
        description="DSL schema version",
    )
    input_hash: str = Field(
        default="",
        description="Hash of input DSL for deduplication",
    )
    overall: PreviewOverallItem = Field(..., description="Overall preview summary")
    sections: list[SectionPreviewItem] = Field(
        default_factory=list,
        description="Per-section preview results",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Top-level errors that prevented preview",
    )

    @model_validator(mode="after")
    def _compute_input_hash(self) -> "PreviewResponse":
        """Compute input hash if not provided."""
        if not self.input_hash:
            # Try to find DSL in sections or compute from overall
            # For now, use a placeholder based on trace_id + overall status
            import hashlib

            data = f"{self.trace_id}:{self.overall.overall_status}"
            self.input_hash = hashlib.sha256(data.encode()).hexdigest()[:16]
        return self


# ---------------------------------------------------------------------------
# Validation Models
# ---------------------------------------------------------------------------

class ValidateStrategyRequest(BaseModel):
    """Request to validate a strategy DSL."""

    model_config = ConfigDict(extra="forbid")

    dsl: StrategyDSL = Field(..., description="Strategy DSL to validate")
    levels: list[ValidationLevel] = Field(
        default_factory=lambda: list(ValidationLevel),
        description="Validation levels to run",
    )
    trace_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique trace ID for audit trail",
    )


class ValidationErrorItem(BaseModel):
    """Serializable validation error."""

    model_config = ConfigDict(extra="forbid")

    level: str = Field(..., description="Validation level")
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    path: str = Field(default="", description="JSON path to offending field")


class ValidateStrategyResponse(BaseModel):
    """Response from strategy validation."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(..., description="Trace ID from request")
    dsl_version: str = Field(default="strategy_dsl_v2")
    passed: bool = Field(..., description="Whether validation passed")
    level: str = Field(..., description="Highest failed validation level")
    errors: list[ValidationErrorItem] = Field(default_factory=list)
    warnings: list[ValidationErrorItem] = Field(default_factory=list)
    red_line_result: dict[str, Any] = Field(
        default_factory=dict,
        description="Red-line check summary for audit",
    )
    input_hash: str = Field(default="")
    output_hash: str = Field(default="")


# ---------------------------------------------------------------------------
# Generation Models
# ---------------------------------------------------------------------------

class GenerateStrategyRequest(BaseModel):
    """Request to generate a strategy from natural language."""

    model_config = ConfigDict(extra="forbid")

    natural_language: str = Field(
        ...,
        max_length=2000,
        description="Natural language strategy description in Chinese",
    )
    strategy_id: str = Field(
        ...,
        pattern=r"^[a-z0-9_]+$",
        description="Desired strategy identifier",
    )
    trace_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique trace ID for audit trail",
    )


class GenerateStrategyResponse(BaseModel):
    """Response from strategy generation."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(..., description="Trace ID from request")
    dsl: StrategyDSL | None = Field(
        default=None,
        description="Generated strategy DSL (None if generation failed)",
    )
    validation_result: ValidateStrategyResponse | None = Field(
        default=None,
        description="Validation result of generated DSL",
    )
    errors: list[str] = Field(default_factory=list)
    input_hash: str = Field(default="")
    output_hash: str = Field(default="")


# ---------------------------------------------------------------------------
# Backtest Models (Stub for Phase 1)
# ---------------------------------------------------------------------------

class BacktestRequest(BaseModel):
    """Request to run a light backtest."""

    model_config = ConfigDict(extra="forbid")

    dsl: StrategyDSL = Field(..., description="Strategy DSL to backtest")
    start_date: str | None = Field(
        default=None,
        description="Backtest start date (YYYY-MM-DD)",
    )
    end_date: str | None = Field(
        default=None,
        description="Backtest end date (YYYY-MM-DD)",
    )
    trace_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique trace ID for audit trail",
    )
    mode: Literal["light"] = Field(
        default="light",
        description="Backtest execution mode",
    )
    initial_capital: float = Field(
        default=1_000_000.0,
        gt=0,
        description="Starting portfolio value",
    )
    foundation_db: str | None = Field(
        default=None,
        description="Path to foundation DuckDB (injected by service layer)",
    )
    state_cube_db: str | None = Field(
        default=None,
        description="Path to state cube DuckDB (injected by service layer)",
    )
    universe: list[str] | None = Field(
        default=None,
        description="Optional list of symbols to backtest",
    )


class BacktestMetrics(BaseModel):
    """Core backtest metrics."""

    model_config = ConfigDict(extra="forbid")

    total_return: float | None = Field(default=None)
    annual_return: float | None = Field(default=None)
    sharpe_ratio: float | None = Field(default=None)
    max_drawdown: float | None = Field(default=None)
    profit_factor: float | None = Field(default=None)
    trade_count: int | None = Field(default=None)
    total_trades: int | None = Field(default=None)
    win_rate: float | None = Field(default=None)
    avg_holding_days: float | None = Field(default=None)
    turnover: float | None = Field(default=None)
    cost_total: float | None = Field(default=None)


class BacktestResponse(BaseModel):
    """Response from backtest execution."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(...)
    dsl_version: str = Field(default="strategy_dsl_v2")
    status: Literal["success", "partial", "failed"] = Field(default="failed")
    mode: Literal["light_real_v1", "light_stub"] = Field(default="light_real_v1")
    metrics: BacktestMetrics = Field(default_factory=BacktestMetrics)
    risk_flags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    trade_count: int | None = Field(default=None)
    daily_curve: list[dict[str, Any]] = Field(default_factory=list)
    trades: list[dict[str, Any]] = Field(default_factory=list)
    state_breakdown: dict[str, Any] = Field(default_factory=dict)
    data_version: str | None = Field(default=None)
    elapsed_seconds: float | None = Field(default=None)
    errors: list[str] = Field(default_factory=list)
    input_hash: str = Field(default="")
    output_hash: str = Field(default="")

    # Truncation metadata (for paginated/truncated responses)
    daily_curve_total_count: int | None = Field(
        default=None,
        description="Total number of daily curve points (may exceed len(daily_curve) if truncated)",
    )
    trades_truncated: bool = Field(
        default=False,
        description="True when trades list was truncated to the first N entries",
    )


class GetBacktestResponse(BaseModel):
    """Response when retrieving a stored backtest result."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(...)
    dsl_version: str = Field(default="strategy_dsl_v2")
    status: Literal["success", "partial", "failed"] = Field(default="failed")
    metrics: BacktestMetrics = Field(default_factory=BacktestMetrics)
    dsl_snapshot: dict[str, Any] | None = Field(
        default=None,
        description="Snapshot of DSL used for this backtest",
    )
    errors: list[str] = Field(default_factory=list)
    created_at: str = Field(default="", description="ISO timestamp")
