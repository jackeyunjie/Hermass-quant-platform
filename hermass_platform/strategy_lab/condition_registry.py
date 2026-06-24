"""Condition Registry - Type-safe registration and validation of strategy conditions.

All condition types must be registered before use. The registry enforces:
    - Parameter schema validation (JSON Schema subset)
    - Category classification (entry, exit, filter)
    - Translator dialect support (duckdb, polars, both)

Usage:
    registry = ConditionRegistry.default()
    spec = registry.get("ma_golden_cross")
    result = registry.validate_params("ma_golden_cross", {"fast_period": 5, "slow_period": 20})
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ConditionCategory(str, Enum):
    """Classification of condition purpose."""

    ENTRY = "entry"
    EXIT = "exit"
    FILTER = "filter"


class TranslatorDialect(str, Enum):
    """Supported translation targets."""

    DUCKDB = "duckdb"
    POLARS = "polars"
    BOTH = "both"


class PreviewSupport(str, Enum):
    """条件在 Preview 中的支持状态。"""

    FULLY_SUPPORTED = "fully_supported"
    MOCK_ONLY = "mock_only"
    REQUIRES_BACKTEST_CONTEXT = "requires_backtest_context"
    UNSUPPORTED = "unsupported"


class ContextRequirement(str, Enum):
    """条件执行所需的上下文类型。"""

    NONE = "none"
    POSITION = "position"
    PORTFOLIO = "portfolio"
    MARKET_STATE = "market_state"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ParamSchema:
    """Schema for a single parameter.

    Attributes:
        name: Parameter name.
        param_type: JSON Schema type ("string", "number", "integer", "boolean", "array").
        required: Whether this parameter is mandatory.
        default: Default value if not provided.
        description: Human-readable description.
        constraints: Additional JSON Schema constraints (min, max, enum, etc.).
    """

    name: str
    param_type: Literal["string", "number", "integer", "boolean", "array"]
    required: bool = True
    default: Any = None
    description: str = ""
    constraints: dict[str, Any] = field(default_factory=dict)

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema property definition."""
        schema: dict[str, Any] = {"type": self.param_type, "description": self.description}
        schema.update(self.constraints)
        return schema


@dataclass(frozen=True)
class ConditionSpec:
    """Specification for a registered condition type.

    Attributes:
        condition_type: Unique type identifier (snake_case).
        category: Primary category (entry, exit, filter).
        params: List of parameter schemas.
        translator: Supported translation dialect(s).
        description: Human-readable description.
        examples: Example parameter sets for documentation.
        required_columns: Static column dependency templates.
        required_tables: Static table dependencies.
        context_requirements: Runtime context needed beyond static data.
        preview_support: Preview support classification.
        preview_notes: Human-readable explanation for preview limitations.
    """

    condition_type: str
    category: ConditionCategory
    params: list[ParamSchema]
    translator: TranslatorDialect
    description: str = ""
    examples: list[dict[str, Any]] = field(default_factory=list)

    # 数据源依赖（静态声明）
    required_columns: list[str] = field(default_factory=list)
    required_tables: list[str] = field(default_factory=list)

    # 执行上下文依赖（运行时）
    context_requirements: list[ContextRequirement] = field(default_factory=list)

    # Preview 支持状态
    preview_support: PreviewSupport = PreviewSupport.FULLY_SUPPORTED
    preview_notes: str = ""

    def get_param(self, name: str) -> ParamSchema | None:
        """Get parameter schema by name."""
        for p in self.params:
            if p.name == name:
                return p
        return None

    def resolve_required_columns(self, params: dict[str, Any]) -> list[str]:
        """Resolve required column templates using condition params.

        Adds ``*_lower`` aliases for string params so timeframe values like
        ``D1`` resolve to translator-compatible column names such as
        ``close_d1``.
        """
        format_params: dict[str, Any] = dict(params)
        for key, value in params.items():
            if isinstance(value, str):
                format_params[f"{key}_lower"] = value.lower()

        resolved: list[str] = []
        for col in self.required_columns:
            try:
                resolved.append(col.format(**format_params))
            except KeyError:
                resolved.append(col)
        return resolved

    def get_required_params(self) -> list[ParamSchema]:
        """Get all required parameters."""
        return [p for p in self.params if p.required]


@dataclass(frozen=True)
class ValidationResult:
    """Result of parameter validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class ConditionRegistry:
    """Central registry for all condition types.

    Thread-safe for reads after initialization. Register all types at startup.
    """

    def __init__(self) -> None:
        self._registry: dict[str, ConditionSpec] = {}

    # -- Registration -----------------------------------------------------

    def register(self, spec: ConditionSpec) -> None:
        """Register a condition type.

        Raises:
            ValueError: If condition_type already registered or invalid.
        """
        if not spec.condition_type:
            raise ValueError("condition_type must not be empty")
        if spec.condition_type in self._registry:
            raise ValueError(
                f"Condition type '{spec.condition_type}' is already registered"
            )
        self._registry[spec.condition_type] = spec

    def register_many(self, specs: list[ConditionSpec]) -> None:
        """Register multiple condition types."""
        for spec in specs:
            self.register(spec)

    # -- Queries ----------------------------------------------------------

    def get(self, condition_type: str) -> ConditionSpec:
        """Get specification for a condition type.

        Raises:
            KeyError: If condition_type is not registered.
        """
        if condition_type not in self._registry:
            raise KeyError(
                f"Unknown condition type: '{condition_type}'. "
                f"Registered types: {list(self._registry.keys())}"
            )
        return self._registry[condition_type]

    def has(self, condition_type: str) -> bool:
        """Check if a condition type is registered."""
        return condition_type in self._registry

    def list_all(self) -> list[ConditionSpec]:
        """List all registered condition types."""
        return list(self._registry.values())

    def list_by_category(self, category: ConditionCategory | str) -> list[ConditionSpec]:
        """List condition types by category."""
        cat = ConditionCategory(category) if isinstance(category, str) else category
        return [s for s in self._registry.values() if s.category == cat]

    def list_by_translator(self, dialect: TranslatorDialect | str) -> list[ConditionSpec]:
        """List condition types supporting a specific dialect."""
        d = TranslatorDialect(dialect) if isinstance(dialect, str) else dialect
        if d == TranslatorDialect.BOTH:
            return list(self._registry.values())
        return [
            s
            for s in self._registry.values()
            if s.translator in (d, TranslatorDialect.BOTH)
        ]

    # -- Validation -------------------------------------------------------

    def validate_params(self, condition_type: str, params: dict[str, Any]) -> ValidationResult:
        """Validate parameters against a condition type's schema.

        Returns:
            ValidationResult with detailed error messages.
        """
        errors: list[str] = []
        warnings: list[str] = []

        try:
            spec = self.get(condition_type)
        except KeyError as e:
            return ValidationResult(valid=False, errors=[str(e)])

        # Check required params
        for req in spec.get_required_params():
            if req.name not in params:
                errors.append(f"Missing required parameter: '{req.name}'")
                continue
            val = params[req.name]
            err = self._check_type(req, val)
            if err:
                errors.append(err)
            else:
                err = self._check_constraints(req, val)
                if err:
                    errors.append(err)

        # Check unknown params
        known = {p.name for p in spec.params}
        for key in params:
            if key not in known:
                warnings.append(f"Unknown parameter: '{key}' (will be ignored)")

        # Check optional params with provided values
        for opt in spec.params:
            if not opt.required and opt.name in params:
                err = self._check_type(opt, params[opt.name])
                if err:
                    errors.append(err)
                else:
                    err = self._check_constraints(opt, params[opt.name])
                    if err:
                        errors.append(err)

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    @staticmethod
    def _check_type(param: ParamSchema, value: Any) -> str | None:
        """Check if value matches the declared parameter type."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
        }
        expected = type_map.get(param.param_type)
        if expected is None:
            return None  # Unknown type, skip
        if not isinstance(value, expected):
            return (
                f"Parameter '{param.name}' expects type '{param.param_type}', "
                f"got '{type(value).__name__}'"
            )
        return None

    @staticmethod
    def _check_constraints(param: ParamSchema, value: Any) -> str | None:
        """Check value against parameter constraints."""
        constraints = param.constraints

        # Numeric constraints
        if param.param_type in ("number", "integer"):
            if "minimum" in constraints and value < constraints["minimum"]:
                return (
                    f"Parameter '{param.name}' value {value} is below "
                    f"minimum {constraints['minimum']}"
                )
            if "maximum" in constraints and value > constraints["maximum"]:
                return (
                    f"Parameter '{param.name}' value {value} exceeds "
                    f"maximum {constraints['maximum']}"
                )

        # Enum constraint
        if "enum" in constraints and value not in constraints["enum"]:
            return (
                f"Parameter '{param.name}' value '{value}' not in allowed values: "
                f"{constraints['enum']}"
            )

        # Array minItems
        if param.param_type == "array" and "minItems" in constraints:
            if len(value) < constraints["minItems"]:
                return (
                    f"Parameter '{param.name}' array must have at least "
                    f"{constraints['minItems']} items, got {len(value)}"
                )

        return None

    # -- Factory ----------------------------------------------------------

    @classmethod
    def default(cls) -> ConditionRegistry:
        """Create a registry with all MVP condition types pre-registered."""
        registry = cls()
        registry.register_many(_MVP_CONDITIONS)
        return registry


# ---------------------------------------------------------------------------
# MVP Condition Definitions
# ---------------------------------------------------------------------------

_MVP_CONDITIONS: list[ConditionSpec] = [
    # -- Moving Average Conditions ----------------------------------------
    ConditionSpec(
        condition_type="ma_golden_cross",
        category=ConditionCategory.ENTRY,
        params=[
            ParamSchema(
                name="fast_period",
                param_type="integer",
                required=True,
                description="Fast moving average period",
                constraints={"minimum": 1, "maximum": 252},
            ),
            ParamSchema(
                name="slow_period",
                param_type="integer",
                required=True,
                description="Slow moving average period",
                constraints={"minimum": 1, "maximum": 252},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Fast MA crosses above slow MA (golden cross)",
        examples=[{"fast_period": 5, "slow_period": 20}],
        required_columns=["ma_{fast_period}", "ma_{slow_period}"],
        required_tables=["daily_bars"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    ConditionSpec(
        condition_type="ma_death_cross",
        category=ConditionCategory.EXIT,
        params=[
            ParamSchema(
                name="fast_period",
                param_type="integer",
                required=True,
                description="Fast moving average period",
                constraints={"minimum": 1, "maximum": 252},
            ),
            ParamSchema(
                name="slow_period",
                param_type="integer",
                required=True,
                description="Slow moving average period",
                constraints={"minimum": 1, "maximum": 252},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Fast MA crosses below slow MA (death cross)",
        examples=[{"fast_period": 5, "slow_period": 20}],
        required_columns=["ma_{fast_period}", "ma_{slow_period}"],
        required_tables=["daily_bars"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    ConditionSpec(
        condition_type="price_cross_ma",
        category=ConditionCategory.ENTRY,
        params=[
            ParamSchema(
                name="timeframe",
                param_type="string",
                required=True,
                description="Price timeframe",
                constraints={"enum": ["D1", "W1", "M1"]},
            ),
            ParamSchema(
                name="ma_period",
                param_type="integer",
                required=True,
                description="Moving average period",
                constraints={"minimum": 1, "maximum": 252},
            ),
            ParamSchema(
                name="direction",
                param_type="string",
                required=True,
                description="Cross direction",
                constraints={"enum": ["above", "below"]},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Price crosses above/below a moving average",
        examples=[{"timeframe": "D1", "ma_period": 20, "direction": "above"}],
        required_columns=["close_{timeframe_lower}", "ma_{ma_period}_{timeframe_lower}"],
        required_tables=["daily_bars"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    # -- State Conditions -------------------------------------------------
    ConditionSpec(
        condition_type="state_hex_in",
        category=ConditionCategory.ENTRY,
        params=[
            ParamSchema(
                name="timeframe",
                param_type="string",
                required=True,
                description="State cube timeframe",
                constraints={"enum": ["MN1", "W1", "D1"]},
            ),
            ParamSchema(
                name="values",
                param_type="array",
                required=True,
                description="Allowed hex state values",
                constraints={"minItems": 1},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="State hex value is in the allowed set",
        examples=[{"timeframe": "D1", "values": ["0x01", "0x02"]}],
        required_columns=["state_hex_{timeframe_lower}"],
        required_tables=["state_cube"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    ConditionSpec(
        condition_type="state_ef_count",
        category=ConditionCategory.ENTRY,
        params=[
            ParamSchema(
                name="operator",
                param_type="string",
                required=True,
                description="Comparison operator",
                constraints={"enum": [">", "<", ">=", "<=", "=="]},
            ),
            ParamSchema(
                name="value",
                param_type="integer",
                required=True,
                description="EF count threshold",
                constraints={"minimum": 0, "maximum": 10},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="EF (Expansion Factor) count comparison",
        examples=[{"operator": ">=", "value": 3}],
        required_columns=["ef_count"],
        required_tables=["state_cube"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    # -- Volume Conditions ------------------------------------------------
    ConditionSpec(
        condition_type="volume_ratio",
        category=ConditionCategory.ENTRY,
        params=[
            ParamSchema(
                name="lookback",
                param_type="integer",
                required=True,
                description="Lookback period for average volume",
                constraints={"minimum": 1, "maximum": 60},
            ),
            ParamSchema(
                name="operator",
                param_type="string",
                required=True,
                description="Comparison operator",
                constraints={"enum": [">", "<", ">=", "<=", "=="]},
            ),
            ParamSchema(
                name="value",
                param_type="number",
                required=True,
                description="Volume ratio threshold",
                constraints={"minimum": 0.0},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Volume ratio compared to lookback average",
        examples=[{"lookback": 20, "operator": ">", "value": 1.5}],
        required_columns=["volume", "volume_ma_{lookback}"],
        required_tables=["daily_bars"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    # -- Industry Filters -------------------------------------------------
    ConditionSpec(
        condition_type="industry_include",
        category=ConditionCategory.FILTER,
        params=[
            ParamSchema(
                name="values",
                param_type="array",
                required=True,
                description="Industries to include",
                constraints={"minItems": 1},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Stock industry is in the include list",
        examples=[{"values": ["电子", "医药生物"]}],
        required_columns=["industry"],
        required_tables=["stock_info"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    ConditionSpec(
        condition_type="industry_exclude",
        category=ConditionCategory.FILTER,
        params=[
            ParamSchema(
                name="values",
                param_type="array",
                required=True,
                description="Industries to exclude",
                constraints={"minItems": 1},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Stock industry is NOT in the exclude list",
        examples=[{"values": ["银行", "房地产"]}],
        required_columns=["industry"],
        required_tables=["stock_info"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    # -- Risk Conditions --------------------------------------------------
    ConditionSpec(
        condition_type="stop_loss_pct",
        category=ConditionCategory.EXIT,
        params=[
            ParamSchema(
                name="value",
                param_type="number",
                required=True,
                description="Stop loss percentage (0-1)",
                constraints={"minimum": 0.0, "maximum": 1.0},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Exit when loss exceeds specified percentage",
        examples=[{"value": 0.08}],
        required_columns=["close"],
        required_tables=["daily_bars"],
        context_requirements=[ContextRequirement.POSITION],
        preview_support=PreviewSupport.REQUIRES_BACKTEST_CONTEXT,
        preview_notes="Stop loss requires position context (entry_price). Preview returns estimated hit count based on price distribution.",
    ),
    ConditionSpec(
        condition_type="take_profit_pct",
        category=ConditionCategory.EXIT,
        params=[
            ParamSchema(
                name="value",
                param_type="number",
                required=True,
                description="Take profit percentage (0-1)",
                constraints={"minimum": 0.0, "maximum": 1.0},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Exit when profit exceeds specified percentage",
        examples=[{"value": 0.15}],
        required_columns=["close"],
        required_tables=["daily_bars"],
        context_requirements=[ContextRequirement.POSITION],
        preview_support=PreviewSupport.REQUIRES_BACKTEST_CONTEXT,
        preview_notes="Take profit requires position context (entry_price). Preview returns estimated hit count based on price distribution.",
    ),
    # -- Market Filters ---------------------------------------------------
    ConditionSpec(
        condition_type="limit_up_filter",
        category=ConditionCategory.FILTER,
        params=[
            ParamSchema(
                name="allow",
                param_type="boolean",
                required=True,
                description="Whether to allow limit-up stocks",
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Filter limit-up (涨停) stocks",
        examples=[{"allow": False}],
        required_columns=["is_limit_up"],
        required_tables=["daily_bars"],
        context_requirements=[ContextRequirement.MARKET_STATE],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    # =====================================================================
    # SQX-INSPIRED MODULE EXPANSION (Phase 1)
    # =====================================================================
    # -- Oscillator Entry Conditions --------------------------------------
    ConditionSpec(
        condition_type="rsi_threshold",
        category=ConditionCategory.ENTRY,
        params=[
            ParamSchema(
                name="period",
                param_type="integer",
                required=True,
                description="RSI calculation period",
                constraints={"minimum": 2, "maximum": 60},
            ),
            ParamSchema(
                name="operator",
                param_type="string",
                required=True,
                description="Comparison operator",
                constraints={"enum": [">", "<", ">=", "<="]},
            ),
            ParamSchema(
                name="value",
                param_type="number",
                required=True,
                description="RSI threshold value",
                constraints={"minimum": 0.0, "maximum": 100.0},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="RSI crosses above/below threshold (e.g. RSI > 70 overbought, RSI < 30 oversold)",
        examples=[{"period": 14, "operator": "<", "value": 30}],
        required_columns=["rsi_{period}"],
        required_tables=["daily_bars"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    ConditionSpec(
        condition_type="macd_cross",
        category=ConditionCategory.ENTRY,
        params=[
            ParamSchema(
                name="fast",
                param_type="integer",
                required=True,
                description="Fast EMA period",
                default=12,
                constraints={"minimum": 2, "maximum": 60},
            ),
            ParamSchema(
                name="slow",
                param_type="integer",
                required=True,
                description="Slow EMA period",
                default=26,
                constraints={"minimum": 5, "maximum": 120},
            ),
            ParamSchema(
                name="signal",
                param_type="integer",
                required=True,
                description="Signal line period",
                default=9,
                constraints={"minimum": 2, "maximum": 60},
            ),
            ParamSchema(
                name="direction",
                param_type="string",
                required=True,
                description="Cross direction",
                constraints={"enum": ["bullish", "bearish"]},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="MACD line crosses above/below signal line",
        examples=[{"fast": 12, "slow": 26, "signal": 9, "direction": "bullish"}],
        required_columns=["macd_{fast}_{slow}", "macd_signal_{fast}_{slow}_{signal}"],
        required_tables=["daily_bars"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    ConditionSpec(
        condition_type="bollinger_breakout",
        category=ConditionCategory.ENTRY,
        params=[
            ParamSchema(
                name="period",
                param_type="integer",
                required=True,
                description="Bollinger Bands period",
                default=20,
                constraints={"minimum": 5, "maximum": 60},
            ),
            ParamSchema(
                name="std_dev",
                param_type="number",
                required=True,
                description="Standard deviation multiplier",
                default=2.0,
                constraints={"minimum": 0.5, "maximum": 5.0},
            ),
            ParamSchema(
                name="direction",
                param_type="string",
                required=True,
                description="Breakout direction",
                constraints={"enum": ["upper", "lower"]},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Price breaks above upper or below lower Bollinger Band",
        examples=[{"period": 20, "std_dev": 2.0, "direction": "upper"}],
        required_columns=["close", "bb_upper_{period}_{std_dev}", "bb_lower_{period}_{std_dev}"],
        required_tables=["daily_bars"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    # -- Trend/MA Variants ------------------------------------------------
    ConditionSpec(
        condition_type="ma_bullish_alignment",
        category=ConditionCategory.ENTRY,
        params=[
            ParamSchema(
                name="ma_periods",
                param_type="array",
                required=True,
                description="MA periods in ascending order (e.g. [5, 10, 20])",
                constraints={"minItems": 2},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Multiple MAs in bullish alignment (short > medium > long)",
        examples=[{"ma_periods": [5, 10, 20]}],
        required_columns=["ma_{ma_periods[0]}", "ma_{ma_periods[1]}", "ma_{ma_periods[2]}"],
        required_tables=["daily_bars"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    ConditionSpec(
        condition_type="price_above_ma",
        category=ConditionCategory.ENTRY,
        params=[
            ParamSchema(
                name="ma_period",
                param_type="integer",
                required=True,
                description="Moving average period",
                constraints={"minimum": 1, "maximum": 252},
            ),
            ParamSchema(
                name="consecutive_bars",
                param_type="integer",
                required=False,
                default=1,
                description="Minimum consecutive bars above MA",
                constraints={"minimum": 1, "maximum": 20},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Price has been above MA for N consecutive bars",
        examples=[{"ma_period": 20, "consecutive_bars": 3}],
        required_columns=["close", "ma_{ma_period}"],
        required_tables=["daily_bars"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    # -- Advanced Exit Conditions -----------------------------------------
    ConditionSpec(
        condition_type="atr_trailing_stop",
        category=ConditionCategory.EXIT,
        params=[
            ParamSchema(
                name="atr_period",
                param_type="integer",
                required=True,
                description="ATR calculation period",
                default=14,
                constraints={"minimum": 5, "maximum": 60},
            ),
            ParamSchema(
                name="multiplier",
                param_type="number",
                required=True,
                description="ATR multiplier for stop distance",
                default=2.0,
                constraints={"minimum": 0.5, "maximum": 5.0},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Trailing stop based on ATR (Chandelier-style)",
        examples=[{"atr_period": 14, "multiplier": 2.0}],
        required_columns=["close", "high", "low", "atr_{atr_period}"],
        required_tables=["daily_bars"],
        context_requirements=[ContextRequirement.POSITION],
        preview_support=PreviewSupport.REQUIRES_BACKTEST_CONTEXT,
        preview_notes="ATR trailing stop requires position context (entry_price, highest_since_entry).",
    ),
    ConditionSpec(
        condition_type="exit_after_bars",
        category=ConditionCategory.EXIT,
        params=[
            ParamSchema(
                name="max_bars",
                param_type="integer",
                required=True,
                description="Maximum bars to hold position",
                constraints={"minimum": 1, "maximum": 252},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Exit after holding position for N bars (time stop)",
        examples=[{"max_bars": 20}],
        required_columns=["bars_since_entry"],
        required_tables=["positions"],
        context_requirements=[ContextRequirement.POSITION],
        preview_support=PreviewSupport.REQUIRES_BACKTEST_CONTEXT,
        preview_notes="Requires position context to count bars since entry.",
    ),
    ConditionSpec(
        condition_type="indicator_reversal_exit",
        category=ConditionCategory.EXIT,
        params=[
            ParamSchema(
                name="indicator",
                param_type="string",
                required=True,
                description="Indicator name (rsi, macd, cci)",
                constraints={"enum": ["rsi", "macd", "cci"]},
            ),
            ParamSchema(
                name="period",
                param_type="integer",
                required=True,
                description="Indicator period",
                constraints={"minimum": 2, "maximum": 60},
            ),
            ParamSchema(
                name="direction",
                param_type="string",
                required=True,
                description="Reversal direction (from overbought/oversold)",
                constraints={"enum": ["overbought", "oversold"]},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Exit when indicator reverses from extreme (e.g. RSI exits overbought)",
        examples=[{"indicator": "rsi", "period": 14, "direction": "overbought"}],
        required_columns=["{indicator}_{period}"],
        required_tables=["daily_bars"],
        context_requirements=[ContextRequirement.POSITION],
        preview_support=PreviewSupport.REQUIRES_BACKTEST_CONTEXT,
    ),
    # -- Enhanced Filter Conditions ---------------------------------------
    ConditionSpec(
        condition_type="liquidity_filter",
        category=ConditionCategory.FILTER,
        params=[
            ParamSchema(
                name="min_turnover",
                param_type="number",
                required=True,
                description="Minimum daily turnover (10k CNY)",
                default=1000,
                constraints={"minimum": 100, "maximum": 100000},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Filter stocks with daily turnover below threshold",
        examples=[{"min_turnover": 1000}],
        required_columns=["amount"],
        required_tables=["daily_bars"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    ConditionSpec(
        condition_type="volatility_filter",
        category=ConditionCategory.FILTER,
        params=[
            ParamSchema(
                name="atr_period",
                param_type="integer",
                required=True,
                description="ATR period for volatility measurement",
                default=14,
                constraints={"minimum": 5, "maximum": 60},
            ),
            ParamSchema(
                name="operator",
                param_type="string",
                required=True,
                description="Comparison operator",
                constraints={"enum": [">", "<", ">=", "<="]},
            ),
            ParamSchema(
                name="threshold_pct",
                param_type="number",
                required=True,
                description="ATR as percentage of close price threshold",
                default=0.02,
                constraints={"minimum": 0.001, "maximum": 0.5},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Filter by volatility level (ATR/close ratio)",
        examples=[{"atr_period": 14, "operator": ">", "threshold_pct": 0.02}],
        required_columns=["close", "atr_{atr_period}"],
        required_tables=["daily_bars"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    ConditionSpec(
        condition_type="time_filter",
        category=ConditionCategory.FILTER,
        params=[
            ParamSchema(
                name="month_range",
                param_type="array",
                required=False,
                description="Allowed months (1-12), empty means all",
            ),
            ParamSchema(
                name="day_of_week",
                param_type="array",
                required=False,
                description="Allowed days (1=Mon-5=Fri), empty means all",
            ),
            ParamSchema(
                name="exclude_holidays",
                param_type="boolean",
                required=False,
                default=True,
                description="Exclude known Chinese market holidays",
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Filter by trading time windows (month, day-of-week)",
        examples=[{"month_range": [3, 4, 5], "exclude_holidays": True}],
        required_columns=["date", "month", "day_of_week"],
        required_tables=["daily_bars"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    ConditionSpec(
        condition_type="st_new_stock_filter",
        category=ConditionCategory.FILTER,
        params=[
            ParamSchema(
                name="exclude_st",
                param_type="boolean",
                required=True,
                default=True,
                description="Exclude ST/*ST stocks",
            ),
            ParamSchema(
                name="max_listing_days",
                param_type="integer",
                required=False,
                default=60,
                description="Exclude stocks listed within N days (new stock filter)",
                constraints={"minimum": 0, "maximum": 365},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Filter out ST stocks and newly listed stocks",
        examples=[{"exclude_st": True, "max_listing_days": 60}],
        required_columns=["is_st", "listing_date", "days_since_listing"],
        required_tables=["stock_info"],
        preview_support=PreviewSupport.FULLY_SUPPORTED,
    ),
    # -- Risk / Money Management ------------------------------------------
    ConditionSpec(
        condition_type="max_position_pct",
        category=ConditionCategory.FILTER,
        params=[
            ParamSchema(
                name="value",
                param_type="number",
                required=True,
                description="Maximum position size as percentage of portfolio (0-1)",
                default=0.20,
                constraints={"minimum": 0.01, "maximum": 1.0},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Maximum single position percentage (red-line enforced)",
        examples=[{"value": 0.20}],
        required_columns=[],
        required_tables=[],
        context_requirements=[ContextRequirement.PORTFOLIO],
        preview_support=PreviewSupport.UNSUPPORTED,
        preview_notes="Position sizing requires portfolio context. Enforced by red-line validator.",
    ),
    ConditionSpec(
        condition_type="max_drawdown_stop",
        category=ConditionCategory.EXIT,
        params=[
            ParamSchema(
                name="value",
                param_type="number",
                required=True,
                description="Maximum portfolio drawdown percentage (0-1)",
                default=0.10,
                constraints={"minimum": 0.01, "maximum": 0.5},
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="Emergency stop when portfolio drawdown exceeds threshold",
        examples=[{"value": 0.10}],
        required_columns=["portfolio_equity", "portfolio_peak"],
        required_tables=["portfolio"],
        context_requirements=[ContextRequirement.PORTFOLIO],
        preview_support=PreviewSupport.REQUIRES_BACKTEST_CONTEXT,
        preview_notes="Portfolio-level stop requires backtest context.",
    ),
]
