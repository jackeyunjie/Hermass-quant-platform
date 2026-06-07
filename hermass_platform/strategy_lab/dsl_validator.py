"""DSL Validator - Semantic validation and red-line checks.

Validation levels:
    1. STRUCTURE: JSON Schema / Pydantic structural validation
    2. SEMANTIC: Condition compatibility, mutual exclusivity
    3. RED_LINE: Risk guardrails (position limits, stop loss, etc.)
    4. COMPLETENESS: Executability check (all conditions registered)

Usage:
    result = validate_dsl(dsl, registry)
    if not result.passed:
        for error in result.errors:
            print(error.message)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .condition_registry import ConditionCategory, ConditionRegistry
from .dsl_schema import StrategyDSL


# ---------------------------------------------------------------------------
# Enums and Data Classes
# ---------------------------------------------------------------------------

class ValidationLevel(str, Enum):
    """Validation severity levels."""

    STRUCTURE = "structure"
    SEMANTIC = "semantic"
    RED_LINE = "red_line"
    COMPLETENESS = "completeness"


@dataclass(frozen=True)
class ValidationError:
    """A single validation error."""

    level: ValidationLevel
    code: str
    message: str
    path: str = ""  # JSON path to the offending field
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationWarning:
    """A non-fatal validation warning."""

    level: ValidationLevel
    code: str
    message: str
    path: str = ""
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Complete validation result."""

    passed: bool
    level: ValidationLevel
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationWarning] = field(default_factory=list)

    @property
    def has_red_line_violation(self) -> bool:
        """Check if any red-line rules were triggered."""
        return any(e.level == ValidationLevel.RED_LINE for e in self.errors)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


@dataclass
class RedLineResult:
    """Result of red-line checks specifically."""

    passed: bool
    triggered_rules: list[str] = field(default_factory=list)
    details: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Red Line Rules
# ---------------------------------------------------------------------------

# Rule identifiers
RL_MAX_POSITION = "RL_MAX_POSITION"
RL_STOP_LOSS_REQUIRED = "RL_STOP_LOSS_REQUIRED"
RL_ENTRY_REQUIRED = "RL_ENTRY_REQUIRED"
RL_EXIT_REQUIRED = "RL_EXIT_REQUIRED"
RL_EXIT_MUST_HAVE_STOP_LOSS = "RL_EXIT_MUST_HAVE_STOP_LOSS"
RL_INDUSTRY_CONFLICT = "RL_INDUSTRY_CONFLICT"
RL_RISK_PER_TRADE = "RL_RISK_PER_TRADE"


# ---------------------------------------------------------------------------
# Main Validation Function
# ---------------------------------------------------------------------------

def validate_dsl(
    dsl: StrategyDSL,
    registry: ConditionRegistry | None = None,
    levels: list[ValidationLevel] | None = None,
) -> ValidationResult:
    """Validate a StrategyDSL instance at specified levels.

    Args:
        dsl: The strategy DSL to validate.
        registry: Condition registry for completeness checks. Uses default if None.
        levels: Validation levels to run. Defaults to all levels.

    Returns:
        ValidationResult with all errors and warnings.
    """
    if levels is None:
        levels = list(ValidationLevel)

    if registry is None:
        registry = ConditionRegistry.default()

    errors: list[ValidationError] = []
    warnings: list[ValidationWarning] = []

    # -- STRUCTURE: Already enforced by Pydantic, but double-check --------
    if ValidationLevel.STRUCTURE in levels:
        _validate_structure(dsl, errors, warnings)

    # -- SEMANTIC: Condition compatibility --------------------------------
    if ValidationLevel.SEMANTIC in levels:
        _validate_semantic(dsl, registry, errors, warnings)

    # -- RED_LINE: Risk guardrails ----------------------------------------
    if ValidationLevel.RED_LINE in levels:
        _validate_red_lines(dsl, errors, warnings)

    # -- COMPLETENESS: All conditions registered --------------------------
    if ValidationLevel.COMPLETENESS in levels:
        _validate_completeness(dsl, registry, errors, warnings)

    passed = len(errors) == 0
    # Determine the highest failed level
    failed_levels = [e.level for e in errors]
    if failed_levels:
        # Order matters: structure < semantic < red_line < completeness
        level_priority = {
            ValidationLevel.STRUCTURE: 0,
            ValidationLevel.SEMANTIC: 1,
            ValidationLevel.RED_LINE: 2,
            ValidationLevel.COMPLETENESS: 3,
        }
        highest_level = max(failed_levels, key=lambda x: level_priority[x])
    else:
        highest_level = ValidationLevel.STRUCTURE

    return ValidationResult(
        passed=passed,
        level=highest_level,
        errors=errors,
        warnings=warnings,
    )


def check_red_lines(dsl: StrategyDSL) -> RedLineResult:
    """Run only red-line checks and return a focused result.

    This is a convenience function for quick risk checks.
    """
    errors: list[ValidationError] = []
    warnings: list[ValidationWarning] = []
    _validate_red_lines(dsl, errors, warnings)

    triggered = [e.code for e in errors]
    details = [e.detail for e in errors]

    return RedLineResult(
        passed=len(errors) == 0,
        triggered_rules=triggered,
        details=details,
    )


# ---------------------------------------------------------------------------
# Validation Implementations
# ---------------------------------------------------------------------------


def _validate_structure(
    dsl: StrategyDSL,
    errors: list[ValidationError],
    warnings: list[ValidationWarning],
) -> None:
    """Validate structural constraints beyond Pydantic."""
    # Check strategy_id format (Pydantic regex handles most, but double-check)
    if not dsl.strategy_id:
        errors.append(
            ValidationError(
                level=ValidationLevel.STRUCTURE,
                code="STRUCT_EMPTY_ID",
                message="strategy_id must not be empty",
                path="strategy_id",
            )
        )

    # Check name is meaningful
    if len(dsl.name.strip()) < 2:
        warnings.append(
            ValidationWarning(
                level=ValidationLevel.STRUCTURE,
                code="STRUCT_SHORT_NAME",
                message="Strategy name is very short (minimum 2 characters recommended)",
                path="name",
            )
        )

    # Check description presence
    if not dsl.description:
        warnings.append(
            ValidationWarning(
                level=ValidationLevel.STRUCTURE,
                code="STRUCT_NO_DESCRIPTION",
                message="Strategy has no description - recommended for audit trail",
                path="description",
            )
        )


def _validate_semantic(
    dsl: StrategyDSL,
    registry: ConditionRegistry,
    errors: list[ValidationError],
    warnings: list[ValidationWarning],
) -> None:
    """Validate semantic constraints (condition compatibility)."""
    all_conditions = dsl.get_all_conditions()

    # Check for duplicate condition types with conflicting params
    condition_types: dict[str, list[dict]] = {}
    for cond in all_conditions:
        ct = cond.condition_type
        if ct not in condition_types:
            condition_types[ct] = []
        condition_types[ct].append(cond.params)

    # Industry include/exclude conflict
    has_include = "industry_include" in condition_types
    has_exclude = "industry_exclude" in condition_types
    if has_include and has_exclude:
        include_values = set()
        exclude_values = set()
        for cond in all_conditions:
            if cond.condition_type == "industry_include":
                include_values.update(cond.params.get("values", []))
            elif cond.condition_type == "industry_exclude":
                exclude_values.update(cond.params.get("values", []))

        overlap = include_values & exclude_values
        if overlap:
            errors.append(
                ValidationError(
                    level=ValidationLevel.SEMANTIC,
                    code=RL_INDUSTRY_CONFLICT,
                    message=(
                        f"Industry conflict: industries {sorted(overlap)} "
                        f"appear in both include and exclude lists"
                    ),
                    path="filters",
                    detail={"overlap": sorted(overlap)},
                )
            )

    # Check condition parameters against registry
    for cond in all_conditions:
        if registry.has(cond.condition_type):
            result = registry.validate_params(cond.condition_type, cond.params)
            if not result.valid:
                for err_msg in result.errors:
                    errors.append(
                        ValidationError(
                            level=ValidationLevel.SEMANTIC,
                            code="SEMANTIC_INVALID_PARAMS",
                            message=f"Condition '{cond.condition_type}': {err_msg}",
                            path=f"conditions.{cond.condition_type}",
                            detail={"params": cond.params, "error": err_msg},
                        )
                    )
            for warn_msg in result.warnings:
                warnings.append(
                    ValidationWarning(
                        level=ValidationLevel.SEMANTIC,
                        code="SEMANTIC_PARAM_WARNING",
                        message=f"Condition '{cond.condition_type}': {warn_msg}",
                        path=f"conditions.{cond.condition_type}",
                    )
                )

    # Validate condition categories match their sections
    for i, cond in enumerate(dsl.entry):
        if registry.has(cond.condition_type):
            spec = registry.get(cond.condition_type)
            if spec.category == ConditionCategory.EXIT:
                warnings.append(
                    ValidationWarning(
                        level=ValidationLevel.SEMANTIC,
                        code="SEMANTIC_WRONG_SECTION",
                        message=(
                            f"Condition '{cond.condition_type}' is categorized as "
                            f"'{spec.category.value}' but used in entry section"
                        ),
                        path=f"entry[{i}]",
                    )
                )

    for i, cond in enumerate(dsl.exit):
        if registry.has(cond.condition_type):
            spec = registry.get(cond.condition_type)
            if spec.category == ConditionCategory.ENTRY:
                warnings.append(
                    ValidationWarning(
                        level=ValidationLevel.SEMANTIC,
                        code="SEMANTIC_WRONG_SECTION",
                        message=(
                            f"Condition '{cond.condition_type}' is categorized as "
                            f"'{spec.category.value}' but used in exit section"
                        ),
                        path=f"exit[{i}]",
                    )
                )


def _validate_red_lines(
    dsl: StrategyDSL,
    errors: list[ValidationError],
    warnings: list[ValidationWarning],
) -> None:
    """Validate red-line risk guardrails."""
    risk = dsl.risk

    # RL-1: Max position <= 25%
    if risk.max_position_pct > 0.25:
        errors.append(
            ValidationError(
                level=ValidationLevel.RED_LINE,
                code=RL_MAX_POSITION,
                message=(
                    f"Red line violated: max_position_pct ({risk.max_position_pct}) "
                    f"exceeds maximum allowed (0.25)"
                ),
                path="risk.max_position_pct",
                detail={
                    "actual": risk.max_position_pct,
                    "maximum": 0.25,
                },
            )
        )

    # RL-2: Stop loss required
    if not risk.stop_loss_required:
        errors.append(
            ValidationError(
                level=ValidationLevel.RED_LINE,
                code=RL_STOP_LOSS_REQUIRED,
                message="Red line violated: stop_loss_required must be True",
                path="risk.stop_loss_required",
            )
        )

    # RL-3: Entry must have at least one condition
    if not dsl.entry:
        errors.append(
            ValidationError(
                level=ValidationLevel.RED_LINE,
                code=RL_ENTRY_REQUIRED,
                message="Red line violated: strategy must have at least one entry condition",
                path="entry",
            )
        )

    # RL-4: Exit must have at least one condition
    if not dsl.exit:
        errors.append(
            ValidationError(
                level=ValidationLevel.RED_LINE,
                code=RL_EXIT_REQUIRED,
                message="Red line violated: strategy must have at least one exit condition",
                path="exit",
            )
        )

    # RL-5: Exit must contain a stop_loss condition
    has_stop_loss = dsl.has_condition_type("stop_loss_pct")
    if not has_stop_loss:
        errors.append(
            ValidationError(
                level=ValidationLevel.RED_LINE,
                code=RL_EXIT_MUST_HAVE_STOP_LOSS,
                message=(
                    "Red line violated: exit conditions must include "
                    "a stop_loss_pct condition"
                ),
                path="exit",
            )
        )

    # RL-6: Risk per trade sanity check
    if risk.risk_per_trade > 0.10:
        errors.append(
            ValidationError(
                level=ValidationLevel.RED_LINE,
                code=RL_RISK_PER_TRADE,
                message=(
                    f"Red line violated: risk_per_trade ({risk.risk_per_trade}) "
                    f"exceeds maximum allowed (0.10)"
                ),
                path="risk.risk_per_trade",
                detail={
                    "actual": risk.risk_per_trade,
                    "maximum": 0.10,
                },
            )
        )


def _validate_completeness(
    dsl: StrategyDSL,
    registry: ConditionRegistry,
    errors: list[ValidationError],
    warnings: list[ValidationWarning],
) -> None:
    """Validate that all conditions are registered and translatable."""
    all_conditions = dsl.get_all_conditions()

    for cond in all_conditions:
        if not registry.has(cond.condition_type):
            errors.append(
                ValidationError(
                    level=ValidationLevel.COMPLETENESS,
                    code="COMPLETENESS_UNKNOWN_CONDITION",
                    message=(
                        f"Condition type '{cond.condition_type}' is not registered. "
                        f"Available types: {sorted(registry._registry.keys())}"
                    ),
                    path=f"conditions.{cond.condition_type}",
                    detail={
                        "unknown_type": cond.condition_type,
                        "registered_types": sorted(registry._registry.keys()),
                    },
                )
            )
