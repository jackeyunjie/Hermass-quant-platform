"""Tests for preview_service.py - PreviewService and MockDataProvider."""

from __future__ import annotations

import pytest

from hermass_platform.strategy_lab.condition_registry import (
    ConditionRegistry,
    PreviewSupport,
)
from hermass_platform.strategy_lab.dsl_generator import create_ma_crossover_strategy
from hermass_platform.strategy_lab.dsl_schema import ConditionBlock, RiskConfig, StrategyDSL
from hermass_platform.strategy_lab.dsl_validator import ValidationLevel
from hermass_platform.strategy_lab.preview_service import (
    MockDataProvider,
    PreviewConfig,
    PreviewService,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def registry() -> ConditionRegistry:
    return ConditionRegistry.default()


@pytest.fixture
def service(registry: ConditionRegistry) -> PreviewService:
    config = PreviewConfig(registry=registry)
    return PreviewService(config)


@pytest.fixture
def valid_dsl() -> StrategyDSL:
    return create_ma_crossover_strategy("test_preview")


@pytest.fixture
def dsl_without_stop_loss() -> StrategyDSL:
    """DSL missing stop_loss - will fail red-line check."""
    return StrategyDSL(
        strategy_id="no_stop_loss",
        name="No Stop Loss Strategy",
        entry=[
            ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            )
        ],
        exit=[
            ConditionBlock(
                condition_type="ma_death_cross",
                params={"fast_period": 5, "slow_period": 20},
            )
        ],
        risk=RiskConfig(
            risk_per_trade=0.02,
            max_position_pct=0.20,
        ),
    )


@pytest.fixture
def dsl_with_unsupported_condition() -> StrategyDSL:
    """DSL with an unsupported condition type."""
    # Register a mock unsupported condition
    from hermass_platform.strategy_lab.condition_registry import (
        ConditionSpec,
        ConditionCategory,
        ContextRequirement,
        ParamSchema,
        TranslatorDialect,
    )
    reg = ConditionRegistry()
    reg.register(
        ConditionSpec(
            condition_type="unsupported_custom",
            category=ConditionCategory.ENTRY,
            params=[ParamSchema(name="x", param_type="integer", required=True)],
            translator=TranslatorDialect.BOTH,
            preview_support=PreviewSupport.UNSUPPORTED,
        )
    )

    dsl = StrategyDSL(
        strategy_id="unsupported_test",
        name="Unsupported Strategy",
        entry=[
            ConditionBlock(
                condition_type="unsupported_custom",
                params={"x": 1},
            )
        ],
        exit=[
            ConditionBlock(
                condition_type="stop_loss_pct",
                params={"value": 0.08},
            )
        ],
        risk=RiskConfig(
            risk_per_trade=0.02,
            max_position_pct=0.20,
        ),
    )
    return dsl, reg


# ---------------------------------------------------------------------------
# MockDataProvider Tests
# ---------------------------------------------------------------------------

class TestMockDataProvider:
    def test_estimate_hits_known_condition(self) -> None:
        provider = MockDataProvider()
        hits = provider.estimate_hits(
            "ma_golden_cross",
            {"fast_period": 5, "slow_period": 20},
            PreviewSupport.FULLY_SUPPORTED,
        )
        assert hits == 42

    def test_estimate_hits_unknown_condition(self) -> None:
        provider = MockDataProvider()
        hits = provider.estimate_hits(
            "unknown_condition",
            {},
            PreviewSupport.FULLY_SUPPORTED,
        )
        assert hits == 10  # Default fallback

    def test_estimate_stop_loss(self) -> None:
        provider = MockDataProvider()
        hits = provider.estimate_hits(
            "stop_loss_pct",
            {"value": 0.08},
            PreviewSupport.REQUIRES_BACKTEST_CONTEXT,
        )
        assert hits is not None
        assert hits > 0
        # 0.08 * 1.5 = 0.12, 3000 * 0.12 = 360
        assert hits == 360

    def test_estimate_take_profit(self) -> None:
        provider = MockDataProvider()
        hits = provider.estimate_hits(
            "take_profit_pct",
            {"value": 0.15},
            PreviewSupport.REQUIRES_BACKTEST_CONTEXT,
        )
        assert hits is not None
        assert hits > 0
        # 0.5 - 0.15 = 0.35, 3000 * 0.35 = 1050
        assert hits == 1050

    def test_unsupported_returns_none(self) -> None:
        provider = MockDataProvider()
        hits = provider.estimate_hits(
            "some_cond",
            {},
            PreviewSupport.UNSUPPORTED,
        )
        assert hits is None


# ---------------------------------------------------------------------------
# PreviewService Tests
# ---------------------------------------------------------------------------

class TestPreviewService:
    def test_preview_valid_dsl(self, service: PreviewService, valid_dsl: StrategyDSL) -> None:
        response = service.preview(valid_dsl, trace_id="test-1")
        assert response.trace_id == "test-1"
        assert len(response.errors) == 0
        assert response.overall.overall_status in ("success", "partial")

    def test_preview_returns_sections(self, service: PreviewService, valid_dsl: StrategyDSL) -> None:
        response = service.preview(valid_dsl)
        assert len(response.sections) > 0

        # Should have entry and exit sections
        section_names = [s.section for s in response.sections]
        assert "entry" in section_names
        assert "exit" in section_names

    def test_preview_entry_conditions(self, service: PreviewService, valid_dsl: StrategyDSL) -> None:
        response = service.preview(valid_dsl)
        entry_section = next(s for s in response.sections if s.section == "entry")
        assert len(entry_section.conditions) > 0

        cond = entry_section.conditions[0]
        assert cond.condition_type == "ma_golden_cross"
        assert cond.preview_support == PreviewSupport.FULLY_SUPPORTED.value
        assert cond.estimated_hits is not None

    def test_preview_exit_with_stop_loss(self, service: PreviewService, valid_dsl: StrategyDSL) -> None:
        response = service.preview(valid_dsl)
        exit_section = next(s for s in response.sections if s.section == "exit")

        # Find stop_loss condition
        stop_loss = next(
            (c for c in exit_section.conditions if c.condition_type == "stop_loss_pct"),
            None,
        )
        assert stop_loss is not None
        assert stop_loss.preview_support == PreviewSupport.REQUIRES_BACKTEST_CONTEXT.value
        assert stop_loss.has_context_required is True
        assert stop_loss.estimated_hits is not None

    def test_stop_loss_does_not_block_preview(self, service: PreviewService, valid_dsl: StrategyDSL) -> None:
        """stop_loss_pct must NOT cause overall preview failure."""
        response = service.preview(valid_dsl)
        assert response.overall.overall_status != "failed"
        assert len(response.errors) == 0

    def test_preview_overall_partial_when_context_required(
        self, service: PreviewService, valid_dsl: StrategyDSL
    ) -> None:
        response = service.preview(valid_dsl)
        # valid_dsl has stop_loss_pct which requires context
        assert response.overall.overall_status == "partial"
        assert response.overall.sections_with_context_required > 0

    def test_red_line_failure_blocks_preview(
        self, service: PreviewService, dsl_without_stop_loss: StrategyDSL
    ) -> None:
        response = service.preview(dsl_without_stop_loss)
        assert response.overall.overall_status == "failed"
        assert len(response.errors) > 0
        assert "Red line" in str(response.errors) or "validation failed" in str(response.errors).lower()

    def test_unsupported_condition_fails_preview(
        self, service: PreviewService, dsl_with_unsupported_condition
    ) -> None:
        dsl, reg = dsl_with_unsupported_condition
        config = PreviewConfig(registry=reg)
        svc = PreviewService(config)
        response = svc.preview(dsl)
        assert response.overall.overall_status == "failed"
        assert any("unsupported" in e.lower() for e in response.errors)

    def test_preview_condition_sql_no_select_star(
        self, service: PreviewService, valid_dsl: StrategyDSL
    ) -> None:
        """SQL preview must not contain SELECT *."""
        for cond in valid_dsl.get_all_conditions():
            sql = service.preview_condition_sql(cond)
            if sql is not None:
                assert "SELECT *" not in sql.upper()
                assert "SELECT" not in sql.upper()  # Should be WHERE fragment only

    def test_preview_condition_sql_returns_fragment(
        self, service: PreviewService
    ) -> None:
        cond = ConditionBlock(
            condition_type="ma_golden_cross",
            params={"fast_period": 5, "slow_period": 20},
        )
        sql = service.preview_condition_sql(cond)
        assert sql is not None
        assert "ma_5" in sql
        assert "ma_20" in sql

    def test_mock_preview_deterministic(
        self, service: PreviewService, valid_dsl: StrategyDSL
    ) -> None:
        """Mock preview should return same results for same input."""
        resp1 = service.preview(valid_dsl, data_source="mock")
        resp2 = service.preview(valid_dsl, data_source="mock")

        assert resp1.overall.overall_status == resp2.overall.overall_status
        assert len(resp1.sections) == len(resp2.sections)

        for s1, s2 in zip(resp1.sections, resp2.sections):
            assert s1.section == s2.section
            assert s1.total_estimated_hits == s2.total_estimated_hits

    def test_trace_id_passed_through(self, service: PreviewService, valid_dsl: StrategyDSL) -> None:
        response = service.preview(valid_dsl, trace_id="my-trace-123")
        assert response.trace_id == "my-trace-123"

    def test_input_hash_computed(self, service: PreviewService, valid_dsl: StrategyDSL) -> None:
        response = service.preview(valid_dsl, trace_id="t1")
        assert response.input_hash != ""
        assert len(response.input_hash) == 16  # SHA-256 truncated

    def test_input_hash_depends_on_dsl_not_trace_id(
        self, service: PreviewService, valid_dsl: StrategyDSL
    ) -> None:
        resp1 = service.preview(valid_dsl, trace_id="trace-a")
        resp2 = service.preview(valid_dsl, trace_id="trace-b")
        assert resp1.input_hash == resp2.input_hash

    def test_duckdb_data_source_fallback(
        self, service: PreviewService, valid_dsl: StrategyDSL
    ) -> None:
        """DuckDB preview should fall back to mock estimates (stub behavior)."""
        response = service.preview(valid_dsl, data_source="duckdb")
        assert response.overall.overall_status != "failed"
        assert len(response.sections) > 0
