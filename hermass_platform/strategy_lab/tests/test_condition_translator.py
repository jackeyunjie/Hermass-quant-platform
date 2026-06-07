"""Tests for condition_translator.py - DSL to SQL/Polars translation."""

from __future__ import annotations

import pytest

from hermass_platform.strategy_lab.condition_registry import ConditionRegistry
from hermass_platform.strategy_lab.condition_translator import (
    TranslationResult,
    translate_condition,
    translate_strategy_where,
    _combine_duckdb,
    _combine_polars,
)
from hermass_platform.strategy_lab.dsl_schema import ConditionBlock, StrategyDSL
from hermass_platform.strategy_lab.dsl_generator import create_ma_crossover_strategy


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def registry() -> ConditionRegistry:
    return ConditionRegistry.default()


@pytest.fixture
def ma_crossover_dsl() -> StrategyDSL:
    return create_ma_crossover_strategy("test_ma")


# ---------------------------------------------------------------------------
# Combine Helpers Tests
# ---------------------------------------------------------------------------

class TestCombineHelpers:
    def test_combine_duckdb_single(self) -> None:
        result = _combine_duckdb(["col > 5"], ["and"])
        assert result == "col > 5"

    def test_combine_duckdb_multiple_and(self) -> None:
        result = _combine_duckdb(["col > 5", "col < 10"], ["and", "and"])
        assert "AND" in result
        assert "(col > 5)" in result
        assert "(col < 10)" in result

    def test_combine_duckdb_multiple_or(self) -> None:
        result = _combine_duckdb(["a = 1", "b = 2"], ["and", "or"])
        assert "OR" in result

    def test_combine_duckdb_empty(self) -> None:
        result = _combine_duckdb([], [])
        assert result == "1=1"

    def test_combine_polars_single(self) -> None:
        result = _combine_polars(['pl.col("a") > 5'], ["and"])
        assert result == 'pl.col("a") > 5'

    def test_combine_polars_multiple(self) -> None:
        result = _combine_polars(
            ['pl.col("a") > 5', 'pl.col("b") < 10'],
            ["and", "and"],
        )
        assert "&" in result

    def test_combine_polars_empty(self) -> None:
        result = _combine_polars([], [])
        assert result == "pl.lit(True)"


# ---------------------------------------------------------------------------
# MA Golden Cross Tests
# ---------------------------------------------------------------------------

class TestMAGoldenCross:
    def test_duckdb_translation(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="ma_golden_cross",
            params={"fast_period": 5, "slow_period": 20},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "ma_5" in result.sql_expr
        assert "ma_20" in result.sql_expr
        assert "LAG" in result.sql_expr
        assert ">" in result.sql_expr
        assert "<=" in result.sql_expr

    def test_polars_translation(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="ma_golden_cross",
            params={"fast_period": 5, "slow_period": 20},
        )
        result = translate_condition(cond, registry, "polars")

        assert result.polars_expr is not None
        assert "pl.col" in result.polars_expr
        assert "ma_5" in result.polars_expr
        assert "ma_20" in result.polars_expr
        assert "shift(1)" in result.polars_expr

    def test_required_columns(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="ma_golden_cross",
            params={"fast_period": 5, "slow_period": 20},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert "ma_5" in result.required_columns
        assert "ma_20" in result.required_columns
        assert "daily_bars" in result.required_tables


# ---------------------------------------------------------------------------
# MA Death Cross Tests
# ---------------------------------------------------------------------------

class TestMADeathCross:
    def test_duckdb_translation(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="ma_death_cross",
            params={"fast_period": 10, "slow_period": 30},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "ma_10" in result.sql_expr
        assert "ma_30" in result.sql_expr
        assert "<" in result.sql_expr
        assert ">=" in result.sql_expr


# ---------------------------------------------------------------------------
# Price Cross MA Tests
# ---------------------------------------------------------------------------

class TestPriceCrossMA:
    def test_above_duckdb(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="price_cross_ma",
            params={"timeframe": "D1", "ma_period": 20, "direction": "above"},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "close_d1" in result.sql_expr
        assert "ma_20_d1" in result.sql_expr
        assert ">" in result.sql_expr

    def test_below_duckdb(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="price_cross_ma",
            params={"timeframe": "D1", "ma_period": 20, "direction": "below"},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "<" in result.sql_expr
        assert ">=" in result.sql_expr


# ---------------------------------------------------------------------------
# State Conditions Tests
# ---------------------------------------------------------------------------

class TestStateConditions:
    def test_state_hex_in_duckdb(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="state_hex_in",
            params={"timeframe": "D1", "values": ["0x01", "0x02"]},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "state_hex_d1" in result.sql_expr
        assert "IN" in result.sql_expr
        assert "'0x01'" in result.sql_expr
        assert "'0x02'" in result.sql_expr

    def test_state_hex_in_polars(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="state_hex_in",
            params={"timeframe": "D1", "values": ["0x01", "0x02"]},
        )
        result = translate_condition(cond, registry, "polars")

        assert result.polars_expr is not None
        assert "is_in" in result.polars_expr
        assert "0x01" in result.polars_expr

    def test_state_ef_count(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="state_ef_count",
            params={"operator": ">=", "value": 3},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "ef_count >= 3" in result.sql_expr


# ---------------------------------------------------------------------------
# Volume Conditions Tests
# ---------------------------------------------------------------------------

class TestVolumeConditions:
    def test_volume_ratio_duckdb(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="volume_ratio",
            params={"lookback": 20, "operator": ">", "value": 1.5},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "volume" in result.sql_expr
        assert "volume_ma_20" in result.sql_expr
        assert "> 1.5" in result.sql_expr
        assert "NULLIF" in result.sql_expr

    def test_volume_ratio_polars(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="volume_ratio",
            params={"lookback": 20, "operator": ">", "value": 1.5},
        )
        result = translate_condition(cond, registry, "polars")

        assert result.polars_expr is not None
        assert "cast(pl.Float64)" in result.polars_expr
        assert "replace(0, None)" in result.polars_expr


# ---------------------------------------------------------------------------
# Industry Filter Tests
# ---------------------------------------------------------------------------

class TestIndustryFilters:
    def test_industry_include_duckdb(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="industry_include",
            params={"values": ["电子", "医药生物"]},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "industry IN" in result.sql_expr
        assert "'电子'" in result.sql_expr
        assert "'医药生物'" in result.sql_expr

    def test_industry_exclude_duckdb(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="industry_exclude",
            params={"values": ["银行", "房地产"]},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "industry NOT IN" in result.sql_expr

    def test_industry_exclude_polars(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="industry_exclude",
            params={"values": ["银行"]},
        )
        result = translate_condition(cond, registry, "polars")

        assert result.polars_expr is not None
        assert "~pl.col" in result.polars_expr  # negation


# ---------------------------------------------------------------------------
# Risk Conditions Tests
# ---------------------------------------------------------------------------

class TestRiskConditions:
    def test_stop_loss_pct_duckdb(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="stop_loss_pct",
            params={"value": 0.08},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "close <= entry_price * 0.92" in result.sql_expr

    def test_stop_loss_pct_polars(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="stop_loss_pct",
            params={"value": 0.08},
        )
        result = translate_condition(cond, registry, "polars")

        assert result.polars_expr is not None
        assert "entry_price" in result.polars_expr
        assert "0.92" in result.polars_expr

    def test_take_profit_pct_duckdb(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="take_profit_pct",
            params={"value": 0.15},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "close >= entry_price * 1.15" in result.sql_expr


# ---------------------------------------------------------------------------
# Market Filter Tests
# ---------------------------------------------------------------------------

class TestMarketFilters:
    def test_limit_up_filter_allow_false_duckdb(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="limit_up_filter",
            params={"allow": False},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "is_limit_up = FALSE" in result.sql_expr

    def test_limit_up_filter_allow_true_duckdb(self, registry: ConditionRegistry) -> None:
        cond = ConditionBlock(
            condition_type="limit_up_filter",
            params={"allow": True},
        )
        result = translate_condition(cond, registry, "duckdb")

        assert result.sql_expr is not None
        assert "is_limit_up = TRUE" in result.sql_expr


# ---------------------------------------------------------------------------
# Strategy Section Translation Tests
# ---------------------------------------------------------------------------

class TestStrategySectionTranslation:
    def test_translate_entry_section(self, registry: ConditionRegistry, ma_crossover_dsl: StrategyDSL) -> None:
        result = translate_strategy_where(
            ma_crossover_dsl, registry, section="entry", dialect="duckdb"
        )

        assert result.sql_expr is not None
        assert "ma_5" in result.sql_expr
        assert "ma_20" in result.sql_expr
        assert "ma_golden_cross" not in result.sql_expr  # Should be translated

    def test_translate_exit_section(self, registry: ConditionRegistry, ma_crossover_dsl: StrategyDSL) -> None:
        result = translate_strategy_where(
            ma_crossover_dsl, registry, section="exit", dialect="duckdb"
        )

        assert result.sql_expr is not None
        assert "ma_death_cross" not in result.sql_expr
        # Should contain both death cross and stop loss
        assert "ma_5" in result.sql_expr or "entry_price" in result.sql_expr

    def test_translate_filters_section(self, registry: ConditionRegistry, ma_crossover_dsl: StrategyDSL) -> None:
        result = translate_strategy_where(
            ma_crossover_dsl, registry, section="filters", dialect="duckdb"
        )

        assert result.sql_expr is not None
        assert "is_limit_up" in result.sql_expr

    def test_translate_empty_section(self, registry: ConditionRegistry) -> None:
        # Create DSL with no filters
        dsl = create_ma_crossover_strategy("test_no_filters")
        dsl = dsl.model_copy(update={"filters": []})

        result = translate_strategy_where(
            dsl, registry, section="filters", dialect="duckdb"
        )

        assert result.sql_expr == "1=1"

    def test_required_columns_aggregation(self, registry: ConditionRegistry, ma_crossover_dsl: StrategyDSL) -> None:
        result = translate_strategy_where(
            ma_crossover_dsl, registry, section="entry", dialect="duckdb"
        )

        assert len(result.required_columns) > 0
        assert len(result.required_tables) > 0


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------

class TestTranslationErrors:
    def test_unknown_condition_type(self, registry: ConditionRegistry) -> None:
        # First register a condition without a translator to trigger ValueError
        from hermass_platform.strategy_lab.condition_registry import ConditionSpec, ConditionCategory, TranslatorDialect, ParamSchema
        spec = ConditionSpec(
            condition_type="untranslated_cond",
            category=ConditionCategory.ENTRY,
            params=[ParamSchema(name="x", param_type="integer", required=True)],
            translator=TranslatorDialect.BOTH,
        )
        registry.register(spec)
        cond = ConditionBlock(
            condition_type="untranslated_cond",
            params={"x": 1},
        )
        with pytest.raises(ValueError, match="No translator implemented"):
            translate_condition(cond, registry, "duckdb")

    def test_unregistered_condition_type(self, registry: ConditionRegistry) -> None:
        # This should fail at registry.get() level
        cond = ConditionBlock(
            condition_type="totally_unknown",
            params={},
        )
        with pytest.raises(KeyError, match="Unknown condition type"):
            translate_condition(cond, registry, "duckdb")

    def test_translation_result_immutable(self) -> None:
        result = TranslationResult(
            sql_expr="test",
            polars_expr=None,
            required_columns=["col1"],
            required_tables=["table1"],
        )
        # Frozen dataclass should not allow mutation
        with pytest.raises(AttributeError):
            result.sql_expr = "new_value"
