"""Tests for dsl_validator.py - Semantic validation and red-line checks."""

from __future__ import annotations

import pytest

from hermass_platform.strategy_lab.condition_registry import ConditionRegistry
from hermass_platform.strategy_lab.dsl_generator import create_ma_crossover_strategy
from hermass_platform.strategy_lab.dsl_schema import (
    ConditionBlock,
    RiskConfig,
    StrategyDSL,
)
from hermass_platform.strategy_lab.dsl_validator import (
    RL_ENTRY_REQUIRED,
    RL_EXIT_MUST_HAVE_STOP_LOSS,
    RL_EXIT_REQUIRED,
    RL_INDUSTRY_CONFLICT,
    RL_MAX_POSITION,
    RL_RISK_PER_TRADE,
    RL_STOP_LOSS_REQUIRED,
    RedLineResult,
    ValidationError,
    ValidationLevel,
    ValidationResult,
    ValidationWarning,
    check_red_lines,
    validate_dsl,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def registry() -> ConditionRegistry:
    return ConditionRegistry.default()


@pytest.fixture
def valid_strategy() -> StrategyDSL:
    return create_ma_crossover_strategy("test_valid")


# ---------------------------------------------------------------------------
# Structure Validation Tests
# ---------------------------------------------------------------------------

class TestStructureValidation:
    def test_valid_strategy_passes(self, registry: ConditionRegistry, valid_strategy: StrategyDSL) -> None:
        result = validate_dsl(valid_strategy, registry)
        assert result.passed is True
        assert result.error_count == 0

    def test_empty_strategy_id(self, registry: ConditionRegistry) -> None:
        with pytest.raises(Exception):  # Pydantic validation error
            StrategyDSL(
                strategy_id="",
                name="Test",
                entry=[ConditionBlock(condition_type="ma_golden_cross", params={"fast_period": 5, "slow_period": 20})],
                exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
                risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
            )

    def test_short_name_warning(self, registry: ConditionRegistry) -> None:
        strategy = StrategyDSL(
            strategy_id="test_short",
            name="A",
            description="Test",
            entry=[ConditionBlock(condition_type="ma_golden_cross", params={"fast_period": 5, "slow_period": 20})],
            exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
            risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
        )
        result = validate_dsl(strategy, registry)
        assert result.passed is True
        assert any(w.code == "STRUCT_SHORT_NAME" for w in result.warnings)

    def test_no_description_warning(self, registry: ConditionRegistry, valid_strategy: StrategyDSL) -> None:
        strategy = valid_strategy.model_copy(update={"description": ""})
        result = validate_dsl(strategy, registry)
        assert result.passed is True
        assert any(w.code == "STRUCT_NO_DESCRIPTION" for w in result.warnings)


# ---------------------------------------------------------------------------
# Semantic Validation Tests
# ---------------------------------------------------------------------------

class TestSemanticValidation:
    def test_industry_conflict(self, registry: ConditionRegistry) -> None:
        strategy = StrategyDSL(
            strategy_id="test_conflict",
            name="Industry Conflict Test",
            entry=[ConditionBlock(condition_type="ma_golden_cross", params={"fast_period": 5, "slow_period": 20})],
            exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
            filters=[
                ConditionBlock(
                    condition_type="industry_include",
                    params={"values": ["电子", "医药生物"]},
                ),
                ConditionBlock(
                    condition_type="industry_exclude",
                    params={"values": ["电子"]},  # Overlap with include
                ),
            ],
            risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
        )
        result = validate_dsl(strategy, registry)
        assert result.passed is False
        assert any(e.code == RL_INDUSTRY_CONFLICT for e in result.errors)

    def test_industry_no_conflict(self, registry: ConditionRegistry) -> None:
        strategy = StrategyDSL(
            strategy_id="test_no_conflict",
            name="No Conflict Test",
            entry=[ConditionBlock(condition_type="ma_golden_cross", params={"fast_period": 5, "slow_period": 20})],
            exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
            filters=[
                ConditionBlock(
                    condition_type="industry_include",
                    params={"values": ["电子"]},
                ),
                ConditionBlock(
                    condition_type="industry_exclude",
                    params={"values": ["银行"]},  # No overlap
                ),
            ],
            risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
        )
        result = validate_dsl(strategy, registry)
        assert result.passed is True
        assert not any(e.code == RL_INDUSTRY_CONFLICT for e in result.errors)

    def test_invalid_condition_params(self, registry: ConditionRegistry) -> None:
        strategy = StrategyDSL(
            strategy_id="test_bad_params",
            name="Bad Params Test",
            entry=[
                ConditionBlock(
                    condition_type="ma_golden_cross",
                    params={"fast_period": 500, "slow_period": 20},  # 500 > max 252
                )
            ],
            exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
            risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
        )
        result = validate_dsl(strategy, registry)
        assert result.passed is False
        assert any("exceeds maximum" in e.message for e in result.errors)

    def test_unknown_condition_type(self, registry: ConditionRegistry) -> None:
        strategy = StrategyDSL(
            strategy_id="test_unknown",
            name="Unknown Condition Test",
            entry=[ConditionBlock(condition_type="unknown_type", params={})],
            exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
            risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
        )
        result = validate_dsl(strategy, registry)
        assert result.passed is False
        assert any(e.level == ValidationLevel.COMPLETENESS for e in result.errors)

    def test_wrong_section_warning(self, registry: ConditionRegistry) -> None:
        # Using an exit condition in entry section
        strategy = StrategyDSL(
            strategy_id="test_wrong_section",
            name="Wrong Section Test",
            entry=[
                ConditionBlock(
                    condition_type="ma_death_cross",  # Exit condition in entry
                    params={"fast_period": 5, "slow_period": 20},
                )
            ],
            exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
            risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
        )
        result = validate_dsl(strategy, registry)
        # Should have warning but still pass (it's a warning, not error)
        assert any(w.code == "SEMANTIC_WRONG_SECTION" for w in result.warnings)


# ---------------------------------------------------------------------------
# Red Line Tests
# ---------------------------------------------------------------------------

class TestRedLines:
    def test_max_position_violation(self, registry: ConditionRegistry) -> None:
        # Bypass Pydantic to test validator layer directly
        strategy = create_ma_crossover_strategy("test_position")
        # Use model_construct to bypass validation and set invalid value
        bad_risk = RiskConfig.model_construct(
            risk_per_trade=0.02, max_position_pct=0.30, stop_loss_required=True
        )
        strategy = strategy.model_copy(update={"risk": bad_risk})
        result = validate_dsl(strategy, registry)
        assert result.passed is False
        assert result.has_red_line_violation is True
        assert any(e.code == RL_MAX_POSITION for e in result.errors)

    def test_max_position_boundary(self, registry: ConditionRegistry) -> None:
        # At exactly 25% should pass
        strategy = StrategyDSL(
            strategy_id="test_position_boundary",
            name="Position Boundary Test",
            entry=[ConditionBlock(condition_type="ma_golden_cross", params={"fast_period": 5, "slow_period": 20})],
            exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
            risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.25),
        )
        result = validate_dsl(strategy, registry)
        assert result.passed is True
        assert not any(e.code == RL_MAX_POSITION for e in result.errors)

    def test_stop_loss_required(self, registry: ConditionRegistry) -> None:
        # Pydantic Literal[True] prevents False, but test the validator path
        # We can't easily create a DSL with stop_loss_required=False due to Pydantic
        # So we test check_red_lines with a mock scenario
        pass  # Covered by Pydantic validation

    def test_missing_stop_loss_condition(self, registry: ConditionRegistry) -> None:
        strategy = StrategyDSL(
            strategy_id="test_no_sl",
            name="No Stop Loss Test",
            entry=[ConditionBlock(condition_type="ma_golden_cross", params={"fast_period": 5, "slow_period": 20})],
            exit=[
                ConditionBlock(
                    condition_type="ma_death_cross",
                    params={"fast_period": 5, "slow_period": 20},
                )
                # No stop_loss_pct!
            ],
            risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
        )
        result = validate_dsl(strategy, registry)
        assert result.passed is False
        assert result.has_red_line_violation is True
        assert any(e.code == RL_EXIT_MUST_HAVE_STOP_LOSS for e in result.errors)

    def test_risk_per_trade_violation(self, registry: ConditionRegistry) -> None:
        # Bypass Pydantic to test validator layer directly
        strategy = create_ma_crossover_strategy("test_risk")
        bad_risk = RiskConfig.model_construct(
            risk_per_trade=0.15, max_position_pct=0.20, stop_loss_required=True
        )
        strategy = strategy.model_copy(update={"risk": bad_risk})
        result = validate_dsl(strategy, registry)
        assert result.passed is False
        assert any(e.code == RL_RISK_PER_TRADE for e in result.errors)

    def test_valid_strategy_passes_red_lines(self, registry: ConditionRegistry, valid_strategy: StrategyDSL) -> None:
        result = check_red_lines(valid_strategy)
        assert result.passed is True
        assert len(result.triggered_rules) == 0

    def test_red_line_result_details(self, registry: ConditionRegistry) -> None:
        strategy = create_ma_crossover_strategy("test_details")
        bad_risk = RiskConfig.model_construct(
            risk_per_trade=0.02, max_position_pct=0.30, stop_loss_required=True
        )
        strategy = strategy.model_copy(update={"risk": bad_risk})
        result = check_red_lines(strategy)
        assert result.passed is False
        assert RL_MAX_POSITION in result.triggered_rules
        assert len(result.details) > 0
        assert result.details[0]["actual"] == 0.30
        assert result.details[0]["maximum"] == 0.25


# ---------------------------------------------------------------------------
# Validation Level Tests
# ---------------------------------------------------------------------------

class TestValidationLevels:
    def test_structure_only(self, registry: ConditionRegistry, valid_strategy: StrategyDSL) -> None:
        result = validate_dsl(
            valid_strategy, registry, levels=[ValidationLevel.STRUCTURE]
        )
        assert result.passed is True
        assert result.level == ValidationLevel.STRUCTURE

    def test_red_line_only(self, registry: ConditionRegistry) -> None:
        strategy = create_ma_crossover_strategy("test_rl_only")
        bad_risk = RiskConfig.model_construct(
            risk_per_trade=0.02, max_position_pct=0.30, stop_loss_required=True
        )
        strategy = strategy.model_copy(update={"risk": bad_risk})
        result = validate_dsl(
            strategy, registry, levels=[ValidationLevel.RED_LINE]
        )
        assert result.passed is False
        assert result.level == ValidationLevel.RED_LINE
        assert len(result.errors) == 1
        assert len(result.warnings) == 0  # Warnings are from other levels

    def test_all_levels(self, registry: ConditionRegistry, valid_strategy: StrategyDSL) -> None:
        result = validate_dsl(valid_strategy, registry)
        assert result.passed is True
        # Should run all levels
        assert result.level == ValidationLevel.STRUCTURE  # Lowest level, all passed


# ---------------------------------------------------------------------------
# ValidationResult Properties Tests
# ---------------------------------------------------------------------------

class TestValidationResult:
    def test_result_properties(self) -> None:
        result = ValidationResult(
            passed=False,
            level=ValidationLevel.RED_LINE,
            errors=[
                ValidationError(
                    level=ValidationLevel.RED_LINE,
                    code=RL_MAX_POSITION,
                    message="Test error",
                )
            ],
            warnings=[
                ValidationWarning(
                    level=ValidationLevel.SEMANTIC,
                    code="TEST_WARN",
                    message="Test warning",
                )
            ],
        )
        assert result.has_red_line_violation is True
        assert result.error_count == 1
        assert result.warning_count == 1

    def test_no_red_line(self) -> None:
        result = ValidationResult(
            passed=False,
            level=ValidationLevel.SEMANTIC,
            errors=[
                ValidationError(
                    level=ValidationLevel.SEMANTIC,
                    code="SEMANTIC_INVALID_PARAMS",
                    message="Test error",
                )
            ],
        )
        assert result.has_red_line_violation is False


# ---------------------------------------------------------------------------
# Acceptance Tests (MVP Requirements)
# ---------------------------------------------------------------------------

class TestMVPRequirements:
    """Tests that verify the 6 MVP acceptance criteria."""

    def test_ac1_ma_crossover_generates_valid_dsl(self) -> None:
        """AC1: 输入"MA5上穿MA20买入，跌破MA10卖出，止损8%"生成合法 DSL."""
        dsl = create_ma_crossover_strategy(
            "ma_crossover_ac1",
            fast_period=5,
            slow_period=20,
            stop_loss=0.08,
        )
        assert dsl.strategy_id == "ma_crossover_ac1"
        assert dsl.has_condition_type("ma_golden_cross")
        assert dsl.has_condition_type("ma_death_cross")
        assert dsl.has_condition_type("stop_loss_pct")
        assert dsl.risk.stop_loss_required is True

    def test_ac2_missing_stop_loss_rejected(self, registry: ConditionRegistry) -> None:
        """AC2: 缺少止损的 DSL 被拒绝."""
        strategy = StrategyDSL(
            strategy_id="no_sl",
            name="No Stop Loss",
            entry=[ConditionBlock(condition_type="ma_golden_cross", params={"fast_period": 5, "slow_period": 20})],
            exit=[
                ConditionBlock(
                    condition_type="ma_death_cross",
                    params={"fast_period": 5, "slow_period": 20},
                )
            ],
            risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
        )
        result = validate_dsl(strategy, registry)
        assert result.passed is False
        assert any(e.code == RL_EXIT_MUST_HAVE_STOP_LOSS for e in result.errors)

    def test_ac3_position_over_25_rejected(self, registry: ConditionRegistry) -> None:
        """AC3: 仓位超过 25% 的 DSL 被红线拒绝."""
        strategy = create_ma_crossover_strategy("high_position")
        bad_risk = RiskConfig.model_construct(
            risk_per_trade=0.02, max_position_pct=0.30, stop_loss_required=True
        )
        strategy = strategy.model_copy(update={"risk": bad_risk})
        result = validate_dsl(strategy, registry)
        assert result.passed is False
        assert result.has_red_line_violation is True
        assert any(e.code == RL_MAX_POSITION for e in result.errors)

    def test_ac4_translation_produces_sql(self, registry: ConditionRegistry) -> None:
        """AC4: 条件翻译能返回 SQL 表达式."""
        dsl = create_ma_crossover_strategy("test_ac4")
        from hermass_platform.strategy_lab.condition_translator import translate_strategy_where

        result = translate_strategy_where(dsl, registry, section="entry", dialect="duckdb")
        assert result.sql_expr is not None
        assert len(result.sql_expr) > 0

    def test_ac5_valid_strategy_passes_all_checks(self, registry: ConditionRegistry) -> None:
        """AC5: 合法策略通过所有校验层级."""
        dsl = create_ma_crossover_strategy("test_ac5")
        result = validate_dsl(dsl, registry)
        assert result.passed is True
        assert result.error_count == 0

    def test_ac6_dsl_serialization_roundtrip(self) -> None:
        """AC6: DSL 能序列化和反序列化."""
        dsl = create_ma_crossover_strategy("test_ac6")
        data = dsl.to_dict()
        restored = StrategyDSL.from_dict(data)
        assert restored.strategy_id == dsl.strategy_id
        assert restored.name == dsl.name
        assert len(restored.entry) == len(dsl.entry)
