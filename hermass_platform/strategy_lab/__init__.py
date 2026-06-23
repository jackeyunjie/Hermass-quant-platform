"""Strategy Lab - DSL Engine for Hermass Quant Platform.

Provides:
    - DSL v2 Schema (Pydantic models)
    - Condition Registry (type-safe condition registration)
    - Condition Translator (DSL -> DuckDB SQL / Polars)
    - DSL Validator (semantic + red-line validation)
    - DSL Generator (LLM output -> DSL conversion, stub)
    - Backtest Adapter (DSL -> BacktestConfig, Phase 2 real light engine)
    - Light Backtest Engine (Polars hot path)
    - Backtest Data Provider (DuckDB data loading)
    - Backtest Metrics (performance metric computation)
    - Backtest Evidence (trade record and event evidence construction)
"""

from .dsl_schema import (
    ConditionBlock,
    ConditionLogic,
    Direction,
    ExecutionConfig,
    EvaluationConfig,
    Hypothesis,
    Metadata,
    Provenance,
    RiskConfig,
    StrategyDSL,
)
from .condition_registry import (
    ConditionCategory,
    ConditionRegistry,
    ConditionSpec,
    ParamSchema,
    TranslatorDialect,
    ValidationResult as RegistryValidationResult,
)
from .condition_translator import (
    TranslationResult,
    translate_condition,
    translate_strategy_where,
)
from .dsl_validator import (
    RedLineResult,
    ValidationError,
    ValidationLevel,
    ValidationResult as DSLValidationResult,
    ValidationWarning,
    validate_dsl,
)
from .backtest_models import (
    EquityPoint,
    LightBacktestOutput,
    MarketDataBundle,
    MarketDataRequest,
    SignalFrame,
    TradeSummary,
)
from .backtest_data_provider import DuckDBBacktestDataProvider
from .light_backtest_engine import LightBacktestEngine
from .backtest_metrics import compute_light_metrics
from .backtest_evidence import build_trade_event_evidence, build_trade_records

__all__ = [
    # Schema
    "ConditionBlock",
    "ConditionLogic",
    "Direction",
    "ExecutionConfig",
    "EvaluationConfig",
    "Hypothesis",
    "Metadata",
    "Provenance",
    "RiskConfig",
    "StrategyDSL",
    # Registry
    "ConditionCategory",
    "ConditionRegistry",
    "ConditionSpec",
    "ParamSchema",
    "TranslatorDialect",
    "RegistryValidationResult",
    # Translator
    "TranslationResult",
    "translate_condition",
    "translate_strategy_where",
    # Validator
    "RedLineResult",
    "ValidationError",
    "ValidationLevel",
    "DSLValidationResult",
    "ValidationWarning",
    "validate_dsl",
    # Backtest Models
    "EquityPoint",
    "LightBacktestOutput",
    "MarketDataBundle",
    "MarketDataRequest",
    "SignalFrame",
    "TradeSummary",
    # Backtest Engine
    "DuckDBBacktestDataProvider",
    "LightBacktestEngine",
    "compute_light_metrics",
    "build_trade_event_evidence",
    "build_trade_records",
]
