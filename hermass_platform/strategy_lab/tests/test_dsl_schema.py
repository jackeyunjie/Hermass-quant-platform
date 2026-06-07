"""Tests for dsl_schema.py - Pydantic v2 model validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hermass_platform.strategy_lab.dsl_schema import (
    ConditionBlock,
    ExecutionConfig,
    EvaluationConfig,
    Hypothesis,
    Metadata,
    Provenance,
    RiskConfig,
    StrategyDSL,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_risk_config() -> RiskConfig:
    return RiskConfig(
        risk_per_trade=0.02,
        max_position_pct=0.20,
        stop_loss_required=True,
    )


@pytest.fixture
def valid_condition_entry() -> ConditionBlock:
    return ConditionBlock(
        condition_type="ma_golden_cross",
        params={"fast_period": 5, "slow_period": 20},
    )


@pytest.fixture
def valid_condition_exit_sl() -> ConditionBlock:
    return ConditionBlock(
        condition_type="stop_loss_pct",
        params={"value": 0.08},
        logic="or",
    )


@pytest.fixture
def valid_strategy(
    valid_condition_entry: ConditionBlock,
    valid_condition_exit_sl: ConditionBlock,
    valid_risk_config: RiskConfig,
) -> StrategyDSL:
    return StrategyDSL(
        strategy_id="test_ma_cross",
        name="测试MA交叉策略",
        description="MA5上穿MA20买入，止损8%",
        entry=[valid_condition_entry],
        exit=[
            ConditionBlock(
                condition_type="ma_death_cross",
                params={"fast_period": 5, "slow_period": 20},
            ),
            valid_condition_exit_sl,
        ],
        filters=[
            ConditionBlock(
                condition_type="limit_up_filter",
                params={"allow": False},
            )
        ],
        risk=valid_risk_config,
    )


# ---------------------------------------------------------------------------
# RiskConfig Tests
# ---------------------------------------------------------------------------

class TestRiskConfig:
    def test_valid_risk_config(self) -> None:
        risk = RiskConfig(
            risk_per_trade=0.02,
            max_position_pct=0.20,
            stop_loss_required=True,
        )
        assert risk.risk_per_trade == 0.02
        assert risk.max_position_pct == 0.20
        assert risk.stop_loss_required is True

    def test_risk_per_trade_boundary(self) -> None:
        # At upper boundary
        risk = RiskConfig(risk_per_trade=0.10, max_position_pct=0.20)
        assert risk.risk_per_trade == 0.10

        # Above upper boundary
        with pytest.raises(ValidationError):
            RiskConfig(risk_per_trade=0.11, max_position_pct=0.20)

    def test_max_position_boundary(self) -> None:
        # At upper boundary (25%)
        risk = RiskConfig(risk_per_trade=0.02, max_position_pct=0.25)
        assert risk.max_position_pct == 0.25

        # Above upper boundary
        with pytest.raises(ValidationError):
            RiskConfig(risk_per_trade=0.02, max_position_pct=0.26)

    def test_stop_loss_must_be_true(self) -> None:
        # Pydantic Literal[True] enforces this
        with pytest.raises(ValidationError):
            RiskConfig(risk_per_trade=0.02, max_position_pct=0.20, stop_loss_required=False)  # type: ignore


# ---------------------------------------------------------------------------
# ConditionBlock Tests
# ---------------------------------------------------------------------------

class TestConditionBlock:
    def test_valid_condition(self) -> None:
        cond = ConditionBlock(
            condition_type="ma_golden_cross",
            params={"fast_period": 5, "slow_period": 20},
        )
        assert cond.condition_type == "ma_golden_cross"
        assert cond.logic == "and"
        assert cond.weight == 1.0

    def test_condition_type_validation(self) -> None:
        # Empty condition type
        with pytest.raises(ValidationError):
            ConditionBlock(condition_type="", params={})

        # Invalid characters
        with pytest.raises(ValidationError):
            ConditionBlock(condition_type="ma-golden-cross", params={})

    def test_weight_bounds(self) -> None:
        # Weight above 1.0
        with pytest.raises(ValidationError):
            ConditionBlock(
                condition_type="test",
                params={},
                weight=1.5,
            )

        # Weight below 0.0
        with pytest.raises(ValidationError):
            ConditionBlock(
                condition_type="test",
                params={},
                weight=-0.1,
            )

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ConditionBlock(
                condition_type="test",
                params={},
                unknown_field="value",
            )


# ---------------------------------------------------------------------------
# StrategyDSL Tests
# ---------------------------------------------------------------------------

class TestStrategyDSL:
    def test_valid_strategy(self, valid_strategy: StrategyDSL) -> None:
        assert valid_strategy.strategy_id == "test_ma_cross"
        assert valid_strategy.name == "测试MA交叉策略"
        assert valid_strategy.schema_version == "strategy_dsl_v2"
        assert len(valid_strategy.entry) == 1
        assert len(valid_strategy.exit) == 2
        assert len(valid_strategy.filters) == 1

    def test_strategy_id_format(self) -> None:
        # Valid IDs
        StrategyDSL(
            strategy_id="valid_id_123",
            name="Test",
            entry=[ConditionBlock(condition_type="test", params={})],
            exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
            risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
        )

        # Invalid: starts with digit
        with pytest.raises(ValidationError):
            StrategyDSL(
                strategy_id="123_invalid",
                name="Test",
                entry=[ConditionBlock(condition_type="test", params={})],
                exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
                risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
            )

        # Invalid: contains uppercase
        with pytest.raises(ValidationError):
            StrategyDSL(
                strategy_id="Invalid_ID",
                name="Test",
                entry=[ConditionBlock(condition_type="test", params={})],
                exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
                risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
            )

    def test_name_max_length(self) -> None:
        with pytest.raises(ValidationError):
            StrategyDSL(
                strategy_id="test",
                name="x" * 65,
                entry=[ConditionBlock(condition_type="test", params={})],
                exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
                risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
            )

    def test_entry_required(self) -> None:
        with pytest.raises(ValidationError):
            StrategyDSL(
                strategy_id="test",
                name="Test",
                entry=[],
                exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
                risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
            )

    def test_exit_required(self) -> None:
        with pytest.raises(ValidationError):
            StrategyDSL(
                strategy_id="test",
                name="Test",
                entry=[ConditionBlock(condition_type="test", params={})],
                exit=[],
                risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
            )

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            StrategyDSL(
                strategy_id="test",
                name="Test",
                entry=[ConditionBlock(condition_type="test", params={})],
                exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
                risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20),
                unknown_field="value",
            )

    def test_serialization(self, valid_strategy: StrategyDSL) -> None:
        # To dict
        data = valid_strategy.to_dict()
        assert data["strategy_id"] == "test_ma_cross"
        assert data["schema_version"] == "strategy_dsl_v2"

        # To JSON
        json_str = valid_strategy.to_json()
        assert "test_ma_cross" in json_str

        # Round-trip
        restored = StrategyDSL.from_dict(data)
        assert restored.strategy_id == valid_strategy.strategy_id
        assert restored.name == valid_strategy.name

    def test_get_all_conditions(self, valid_strategy: StrategyDSL) -> None:
        all_conds = valid_strategy.get_all_conditions()
        assert len(all_conds) == 4  # 1 entry + 2 exit + 1 filter

    def test_has_condition_type(self, valid_strategy: StrategyDSL) -> None:
        assert valid_strategy.has_condition_type("ma_golden_cross") is True
        assert valid_strategy.has_condition_type("volume_ratio") is False

    def test_get_conditions_by_type(self, valid_strategy: StrategyDSL) -> None:
        sl_conds = valid_strategy.get_conditions_by_type("stop_loss_pct")
        assert len(sl_conds) == 1
        assert sl_conds[0].params["value"] == 0.08


# ---------------------------------------------------------------------------
# Sub-model Tests
# ---------------------------------------------------------------------------

class TestSubModels:
    def test_hypothesis(self) -> None:
        h = Hypothesis(summary="测试假设", market_regime=["bull", "consolidation"])
        assert h.summary == "测试假设"
        assert len(h.market_regime) == 2

    def test_execution_config(self) -> None:
        ec = ExecutionConfig()
        assert ec.mode == "paper"
        assert ec.human_confirm_required is True

    def test_evaluation_config(self) -> None:
        ev = EvaluationConfig()
        assert ev.walk_forward_required is True
        assert ev.min_oos_trades == 10

    def test_provenance(self) -> None:
        p = Provenance(created_by="user_123", source_message_id="msg_456")
        assert p.created_by == "user_123"

    def test_metadata(self) -> None:
        m = Metadata(author="test_user", tags=["ma", "trend"])
        assert m.author == "test_user"
        assert "ma" in m.tags
