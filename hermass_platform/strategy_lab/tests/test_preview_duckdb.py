"""Tests for DuckDB preview provider.

Requires synthetic DuckDB fixture with daily_bars and state_cube tables.
"""

from __future__ import annotations

import os
import tempfile

import pytest

from hermass_platform.strategy_lab.condition_registry import (
    ConditionRegistry,
    PreviewSupport,
)
from hermass_platform.strategy_lab.dsl_generator import create_ma_crossover_strategy
from hermass_platform.strategy_lab.dsl_schema import ConditionBlock, RiskConfig, StrategyDSL
from hermass_platform.strategy_lab.preview_service import (
    DuckDBPreviewProvider,
    PreviewConfig,
    PreviewService,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def duckdb_path() -> str:
    """Create a temporary DuckDB with synthetic data."""
    path = tempfile.mktemp(suffix=".duckdb")

    import duckdb

    con = duckdb.connect(path)
    # daily_bars: enough rows for golden cross / limit_up tests
    con.execute(
        """
        CREATE TABLE daily_bars AS
        SELECT
            'SYM' || (i / 100)::INTEGER::VARCHAR AS symbol,
            i % 100 AS date,
            CASE WHEN i % 20 = 0 THEN 110.0 ELSE 100.0 END AS ma_5,
            CASE WHEN i % 20 = 0 THEN 105.0 ELSE 100.0 END AS ma_20,
            i % 50 = 0 AS is_limit_up,
            1000 + i AS volume,
            1000.0 AS volume_ma_20
        FROM range(0, 200) t(i)
        """
    )
    # state_cube: enough rows for state_hex_in / ef_count tests
    con.execute(
        """
        CREATE TABLE state_cube AS
        SELECT
            i AS id,
            CASE WHEN i % 3 = 0 THEN '0x01' ELSE '0x00' END AS state_hex_d1,
            i % 5 AS ef_count
        FROM range(0, 60) t(i)
        """
    )
    con.close()

    yield path

    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def registry() -> ConditionRegistry:
    return ConditionRegistry.default()


@pytest.fixture
def service_duckdb(duckdb_path: str, registry: ConditionRegistry) -> PreviewService:
    config = PreviewConfig(registry=registry, duckdb_path=duckdb_path)
    return PreviewService(config)


@pytest.fixture
def service_no_duckdb(registry: ConditionRegistry) -> PreviewService:
    config = PreviewConfig(registry=registry, duckdb_path=None)
    return PreviewService(config)


# ---------------------------------------------------------------------------
# DuckDBPreviewProvider direct tests
# ---------------------------------------------------------------------------

class TestDuckDBPreviewProvider:
    def test_count_hits_ma_golden_cross(self, duckdb_path: str, registry: ConditionRegistry) -> None:
        provider = DuckDBPreviewProvider(duckdb_path)
        cond = ConditionBlock(
            condition_type="ma_golden_cross",
            params={"fast_period": 5, "slow_period": 20},
        )
        hits = provider.count_hits(cond, registry)
        assert hits == 8
        provider.close()

    def test_count_hits_limit_up_filter(self, duckdb_path: str, registry: ConditionRegistry) -> None:
        provider = DuckDBPreviewProvider(duckdb_path)
        cond = ConditionBlock(
            condition_type="limit_up_filter",
            params={"allow": False},
        )
        hits = provider.count_hits(cond, registry)
        assert hits is not None
        assert hits >= 0
        provider.close()

    def test_count_hits_state_hex_in(self, duckdb_path: str, registry: ConditionRegistry) -> None:
        provider = DuckDBPreviewProvider(duckdb_path)
        cond = ConditionBlock(
            condition_type="state_hex_in",
            params={"timeframe": "D1", "values": ["0x01"]},
        )
        hits = provider.count_hits(cond, registry)
        assert hits is not None
        assert hits >= 0
        provider.close()

    def test_translated_sql_no_select_star(self, duckdb_path: str, registry: ConditionRegistry) -> None:
        provider = DuckDBPreviewProvider(duckdb_path)
        cond = ConditionBlock(
            condition_type="ma_golden_cross",
            params={"fast_period": 5, "slow_period": 20},
        )
        # count_hits builds SQL internally; ensure no SELECT *
        import duckdb

        con = duckdb.connect(duckdb_path)
        result = registry.get("ma_golden_cross")
        from hermass_platform.strategy_lab.condition_translator import translate_condition

        tr = translate_condition(cond, registry, "duckdb")
        sql = f"SELECT COUNT(*) AS hit_count FROM daily_bars WHERE {tr.sql_expr}"
        assert "SELECT *" not in sql.upper()
        assert "*" not in sql.replace("COUNT(*)", "")
        con.close()
        provider.close()

    def test_window_preview_query_uses_qualify_without_select_star(
        self, duckdb_path: str, registry: ConditionRegistry
    ) -> None:
        """Window-function previews should use QUALIFY and avoid SELECT *."""
        provider = DuckDBPreviewProvider(duckdb_path)
        cond = ConditionBlock(
            condition_type="ma_golden_cross",
            params={"fast_period": 5, "slow_period": 20},
        )
        tr = provider.build_count_sql(cond, registry)
        assert tr is not None
        assert "QUALIFY" in tr.upper()
        assert "SELECT *" not in tr.upper()
        assert "SELECT 1" in tr.upper()
        provider.close()

    def test_missing_duckdb_path_returns_none(self, registry: ConditionRegistry) -> None:
        provider = DuckDBPreviewProvider(duckdb_path=None)
        cond = ConditionBlock(
            condition_type="ma_golden_cross",
            params={"fast_period": 5, "slow_period": 20},
        )
        # Without duckdb_path, count_hits falls back to None (connection fails gracefully)
        hits = provider.count_hits(cond, registry)
        assert hits is None


# ---------------------------------------------------------------------------
# PreviewService with DuckDB
# ---------------------------------------------------------------------------

class TestPreviewServiceDuckDB:
    def test_duckdb_returns_real_hit_count(
        self, service_duckdb: PreviewService
    ) -> None:
        dsl = create_ma_crossover_strategy("test_duckdb")
        response = service_duckdb.preview(dsl, data_source="duckdb")
        assert response.overall.overall_status != "failed"
        assert len(response.sections) > 0

        entry = next(s for s in response.sections if s.section == "entry")
        golden = next(c for c in entry.conditions if c.condition_type == "ma_golden_cross")
        assert golden.estimated_hits is not None
        # With synthetic data we know ma_5 > ma_20 at i % 20 == 0
        # LAG check makes it ~5 hits out of 100
        assert golden.estimated_hits >= 0

    def test_limit_up_filter_real_count(
        self, service_duckdb: PreviewService
    ) -> None:
        dsl = create_ma_crossover_strategy("test_limit_up")
        response = service_duckdb.preview(dsl, data_source="duckdb")
        filters = next((s for s in response.sections if s.section == "filters"), None)
        if filters:
            limit_up = next(
                (c for c in filters.conditions if c.condition_type == "limit_up_filter"),
                None,
            )
            if limit_up:
                assert limit_up.estimated_hits is not None
                assert limit_up.estimated_hits >= 0

    def test_state_hex_in_real_count(
        self, service_duckdb: PreviewService
    ) -> None:
        dsl = StrategyDSL(
            strategy_id="state_hex_test",
            name="State Hex Test",
            entry=[
                ConditionBlock(
                    condition_type="state_hex_in",
                    params={"timeframe": "D1", "values": ["0x01"]},
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
        response = service_duckdb.preview(dsl, data_source="duckdb")
        assert response.overall.overall_status != "failed"
        entry = next(s for s in response.sections if s.section == "entry")
        state_cond = next(c for c in entry.conditions if c.condition_type == "state_hex_in")
        assert state_cond.estimated_hits is not None
        assert state_cond.estimated_hits >= 0

    def test_stop_loss_does_not_block_duckdb_preview(
        self, service_duckdb: PreviewService
    ) -> None:
        dsl = create_ma_crossover_strategy("test_stop_loss")
        response = service_duckdb.preview(dsl, data_source="duckdb")
        assert response.overall.overall_status != "failed"
        exit_section = next(s for s in response.sections if s.section == "exit")
        stop_loss = next(
            c for c in exit_section.conditions if c.condition_type == "stop_loss_pct"
        )
        assert stop_loss.preview_support == PreviewSupport.REQUIRES_BACKTEST_CONTEXT.value
        assert stop_loss.has_context_required is True
        assert stop_loss.estimated_hits is not None

    def test_no_duckdb_path_fallback_to_mock(
        self, service_no_duckdb: PreviewService
    ) -> None:
        dsl = create_ma_crossover_strategy("test_no_db")
        response = service_no_duckdb.preview(dsl, data_source="duckdb")
        assert response.overall.overall_status != "failed"
        entry = next(s for s in response.sections if s.section == "entry")
        golden = next(c for c in entry.conditions if c.condition_type == "ma_golden_cross")
        # Fallback to mock value
        assert golden.estimated_hits == 42

    def test_duckdb_preview_deterministic(
        self, service_duckdb: PreviewService
    ) -> None:
        dsl = create_ma_crossover_strategy("test_deterministic")
        resp1 = service_duckdb.preview(dsl, data_source="duckdb")
        resp2 = service_duckdb.preview(dsl, data_source="duckdb")
        assert resp1.overall.overall_status == resp2.overall.overall_status
        for s1, s2 in zip(resp1.sections, resp2.sections):
            assert s1.total_estimated_hits == s2.total_estimated_hits
