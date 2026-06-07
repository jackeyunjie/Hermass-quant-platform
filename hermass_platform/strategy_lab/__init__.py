"""Strategy Lab - DSL Engine for Hermass Quant Platform.

Provides:
    - DSL v2 Schema (Pydantic models)
    - Condition Registry (type-safe condition registration)
    - Condition Translator (DSL -> DuckDB SQL / Polars)
    - DSL Validator (semantic + red-line validation)
    - DSL Generator (LLM output -> DSL conversion, stub)
    - Backtest Adapter (DSL -> BacktestConfig, stub)
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
]
