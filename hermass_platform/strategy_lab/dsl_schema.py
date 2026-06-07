"""DSL v2 Schema - Pydantic v2 Models + JSON Schema generation.

This module defines the canonical data structures for Strategy DSL v2.
All strategy representations must validate against these models before execution.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Enums / Literals
# ---------------------------------------------------------------------------

ConditionLogic = Literal["and", "or"]
Direction = Literal["above", "below", "cross_up", "cross_down"]
Operator = Literal[">", "<", ">=", "<=", "==", "!=", "in", "not_in"]


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class Hypothesis(BaseModel):
    """Strategy hypothesis and market regime assumptions."""

    model_config = ConfigDict(extra="allow")

    summary: str = ""
    market_regime: list[str] = Field(default_factory=list)


class ConditionBlock(BaseModel):
    """A single condition block within entry, exit, or filters.

    Attributes:
        condition_type: Registered condition type name (e.g. "ma_golden_cross").
        params: Type-specific parameters (validated by ConditionRegistry).
        logic: How this condition combines with others in the same section.
        weight: Influence weight for scoring (0.0 - 1.0).
    """

    model_config = ConfigDict(extra="forbid")

    condition_type: str = Field(
        ...,
        description="Registered condition type name",
        examples=["ma_golden_cross", "stop_loss_pct"],
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Type-specific parameters",
    )
    logic: ConditionLogic = Field(
        default="and",
        description="Logical combination with other conditions in section",
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Influence weight for scoring",
    )

    @field_validator("condition_type")
    @classmethod
    def _validate_condition_type_format(cls, v: str) -> str:
        if not v:
            raise ValueError("condition_type must not be empty")
        if not all(c.isalnum() or c == "_" for c in v):
            raise ValueError("condition_type must be snake_case alphanumeric")
        return v


class RiskConfig(BaseModel):
    """Risk management configuration - enforced by red-line checks.

    Constraints:
        - risk_per_trade: 0 < x <= 0.10 (10% max per trade)
        - max_position_pct: 0 < x <= 0.25 (25% max position)
        - stop_loss_required: MUST be True (hard requirement)
    """

    model_config = ConfigDict(extra="forbid")

    risk_per_trade: float = Field(
        ...,
        gt=0.0,
        le=0.10,
        description="Maximum risk per trade as fraction of capital",
    )
    max_position_pct: float = Field(
        ...,
        gt=0.0,
        le=0.25,
        description="Maximum position size as fraction of portfolio",
    )
    stop_loss_required: Literal[True] = Field(
        default=True,
        description="Stop loss is mandatory - cannot be disabled",
    )


class EvaluationConfig(BaseModel):
    """Backtest evaluation requirements."""

    model_config = ConfigDict(extra="allow")

    walk_forward_required: bool = Field(
        default=True,
        description="Require walk-forward validation",
    )
    min_oos_trades: int = Field(
        default=10,
        ge=1,
        description="Minimum out-of-sample trades for validity",
    )


class ExecutionConfig(BaseModel):
    """Execution mode configuration."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["paper"] = Field(
        default="paper",
        description="Execution mode - only paper trading in MVP",
    )
    human_confirm_required: Literal[True] = Field(
        default=True,
        description="Human confirmation required for all orders",
    )


class Provenance(BaseModel):
    """Audit trail for strategy creation."""

    model_config = ConfigDict(extra="allow")

    created_by: str = Field(default="", description="Agent or user identifier")
    source_message_id: str = Field(
        default="", description="Original chat message ID if applicable"
    )


class Metadata(BaseModel):
    """Optional strategy metadata."""

    model_config = ConfigDict(extra="allow")

    author: str = ""
    tags: list[str] = Field(default_factory=list)
    suitable_environments: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Main DSL Model
# ---------------------------------------------------------------------------

class StrategyDSL(BaseModel):
    """Strategy DSL v2 - Canonical representation of a quantitative strategy.

    This is the single source of truth for strategy definition.
    All natural language inputs must be translated to this structure.
    All execution paths must validate against this schema.

    Required fields:
        - strategy_id: Unique identifier (snake_case)
        - name: Human-readable name (max 64 chars)
        - schema_version: Must be "strategy_dsl_v2"
        - entry: At least one entry condition
        - exit: At least one exit condition
        - risk: Risk configuration with mandatory stop loss
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "examples": [
                {
                    "strategy_id": "ma_crossover_v1",
                    "name": "MA5上穿MA20策略",
                    "schema_version": "strategy_dsl_v2",
                    "description": "均线金叉买入，死叉卖出",
                    "entry": [
                        {
                            "condition_type": "ma_golden_cross",
                            "params": {"fast_period": 5, "slow_period": 20},
                            "logic": "and",
                            "weight": 1.0,
                        }
                    ],
                    "exit": [
                        {
                            "condition_type": "ma_death_cross",
                            "params": {"fast_period": 5, "slow_period": 20},
                            "logic": "and",
                            "weight": 1.0,
                        },
                        {
                            "condition_type": "stop_loss_pct",
                            "params": {"value": 0.08},
                            "logic": "or",
                            "weight": 1.0,
                        },
                    ],
                    "filters": [
                        {
                            "condition_type": "limit_up_filter",
                            "params": {"allow": False},
                            "logic": "and",
                            "weight": 1.0,
                        }
                    ],
                    "risk": {
                        "risk_per_trade": 0.02,
                        "max_position_pct": 0.20,
                        "stop_loss_required": True,
                    },
                }
            ],
        },
    )

    strategy_id: str = Field(
        ...,
        pattern=r"^[a-z0-9_]+$",
        description="Unique strategy identifier (snake_case, alphanumeric)",
    )
    name: str = Field(
        ...,
        max_length=64,
        description="Human-readable strategy name",
    )
    schema_version: Literal["strategy_dsl_v2"] = Field(
        default="strategy_dsl_v2",
        description="DSL schema version identifier",
    )
    description: str = Field(
        default="",
        description="Strategy description",
    )
    hypothesis: Hypothesis = Field(
        default_factory=Hypothesis,
        description="Strategy hypothesis and market regime assumptions",
    )
    entry: list[ConditionBlock] = Field(
        ...,
        min_length=1,
        description="Entry conditions - at least one required",
    )
    filters: list[ConditionBlock] = Field(
        default_factory=list,
        description="Pre-entry filter conditions",
    )
    exit: list[ConditionBlock] = Field(
        ...,
        min_length=1,
        description="Exit conditions - at least one required",
    )
    risk: RiskConfig = Field(
        ...,
        description="Risk management configuration",
    )
    evaluation: EvaluationConfig = Field(
        default_factory=EvaluationConfig,
        description="Backtest evaluation requirements",
    )
    execution: ExecutionConfig = Field(
        default_factory=ExecutionConfig,
        description="Execution mode configuration",
    )
    provenance: Provenance = Field(
        default_factory=Provenance,
        description="Audit trail for strategy creation",
    )
    metadata: Metadata = Field(
        default_factory=Metadata,
        description="Optional strategy metadata",
    )

    @field_validator("strategy_id")
    @classmethod
    def _validate_strategy_id(cls, v: str) -> str:
        if not v:
            raise ValueError("strategy_id must not be empty")
        if v[0].isdigit():
            raise ValueError("strategy_id must not start with a digit")
        return v

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def to_json(self) -> str:
        """Serialize to canonical JSON string."""
        return self.model_dump_json(indent=2, by_alias=True)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return self.model_dump(by_alias=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategyDSL:
        """Deserialize from dictionary."""
        return cls.model_validate(data)

    def get_all_conditions(self) -> list[ConditionBlock]:
        """Return all conditions across entry, exit, and filters."""
        return self.entry + self.exit + self.filters

    def has_condition_type(self, condition_type: str) -> bool:
        """Check if strategy uses a specific condition type."""
        return any(c.condition_type == condition_type for c in self.get_all_conditions())

    def get_conditions_by_type(self, condition_type: str) -> list[ConditionBlock]:
        """Get all conditions of a specific type."""
        return [c for c in self.get_all_conditions() if c.condition_type == condition_type]
