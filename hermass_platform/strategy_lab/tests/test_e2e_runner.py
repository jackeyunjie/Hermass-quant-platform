"""Tests for e2e_runner.py - MVP sample execution."""

from __future__ import annotations

import os
import tempfile

import pytest

from hermass_platform.strategy_lab.e2e_runner import (
    NLToDSLParser,
    run_mvp_e2e_sample,
)
from hermass_platform.strategy_lab.storage import StrategyLabStorage


@pytest.fixture
def db_paths() -> tuple[str, str]:
    audit_path = tempfile.mktemp(suffix="-audit.duckdb")
    storage_path = tempfile.mktemp(suffix="-storage.duckdb")
    yield audit_path, storage_path
    for path in (audit_path, storage_path):
        try:
            os.unlink(path)
        except OSError:
            pass


FROZEN_SAMPLES = [
    (
        "sample_ma_5_20_stop_8",
        "MA5上穿MA20买入，跌破MA10卖出，止损8%",
        ["ma_golden_cross"],
        ["price_cross_ma", "stop_loss_pct"],
    ),
    (
        "sample_state_volume_stop_8_take_15",
        "D1状态属于0x21或0x23，成交量放大到20日均量1.5倍以上买入，止损8%，止盈15%",
        ["state_hex_in", "volume_ratio"],
        ["stop_loss_pct", "take_profit_pct"],
    ),
    (
        "sample_ma_state_limit_filter",
        "MA5上穿MA20且D1状态EF数量不少于2时买入，排除涨停股票，跌破MA10或止损8%卖出",
        ["ma_golden_cross", "state_ef_count"],
        ["price_cross_ma", "stop_loss_pct"],
    ),
]


class TestNLToDSLParser:
    @pytest.mark.parametrize(
        "strategy_id,natural_language,entry_types,exit_types", FROZEN_SAMPLES
    )
    def test_parses_frozen_samples(
        self,
        strategy_id: str,
        natural_language: str,
        entry_types: list[str],
        exit_types: list[str],
    ) -> None:
        dsl = NLToDSLParser().parse(natural_language, strategy_id)
        assert dsl.strategy_id == strategy_id
        assert [c.condition_type for c in dsl.entry] == entry_types
        assert [c.condition_type for c in dsl.exit] == exit_types
        assert dsl.has_condition_type("stop_loss_pct")
        assert dsl.risk.max_position_pct == 0.20

    def test_preserves_over_position_for_red_line_validation(self) -> None:
        dsl = NLToDSLParser().parse(
            "MA5上穿MA20买入，跌破MA10卖出，止损8%，仓位30%",
            "over_position",
        )
        assert dsl.risk.max_position_pct == 0.30


class TestRunMvpE2ESample:
    @pytest.mark.parametrize(
        "strategy_id,natural_language,entry_types,exit_types", FROZEN_SAMPLES
    )
    def test_frozen_samples_run_full_audited_chain(
        self,
        db_paths: tuple[str, str],
        strategy_id: str,
        natural_language: str,
        entry_types: list[str],
        exit_types: list[str],
    ) -> None:
        audit_path, storage_path = db_paths
        result = run_mvp_e2e_sample(
            natural_language,
            strategy_id,
            trace_id=f"trace-{strategy_id}",
            audit_db_path=audit_path,
            storage_db_path=storage_path,
        )

        assert result.status == "partial"
        assert result.stage_reached == "complete"
        assert result.dsl is not None
        assert result.validation is not None
        assert result.validation.passed is True
        assert result.red_line_result["passed"] is True
        assert result.preview is not None
        assert result.preview.overall.overall_status == "partial"
        assert result.backtest is not None
        assert result.backtest.status == "partial"
        assert result.backtest_mode == "light_stub"
        assert result.backtest.metrics.annual_return == 0.0
        assert result.backtest.metrics.profit_factor == 0.0
        assert result.backtest.metrics.trade_count == 0

        assert [r["operation"] for r in result.audit_records] == [
            "generation",
            "validation",
            "preview",
            "backtest",
        ]
        assert all(r["trace_id"] == f"trace-{strategy_id}" for r in result.audit_records)

        storage = StrategyLabStorage(storage_path)
        backtest = storage.get_backtest(f"trace-{strategy_id}")
        assert backtest is not None
        assert backtest.metrics["_mode"] == "light_stub"
        assert backtest.dsl_snapshot is not None
        assert backtest.dsl_snapshot["strategy_id"] == strategy_id

    def test_missing_stop_loss_fails_at_validation_and_skips_later_steps(
        self, db_paths: tuple[str, str]
    ) -> None:
        audit_path, storage_path = db_paths
        result = run_mvp_e2e_sample(
            "MA5上穿MA20买入，跌破MA10卖出",
            "missing_stop_loss",
            trace_id="trace-missing-stop",
            audit_db_path=audit_path,
            storage_db_path=storage_path,
        )

        assert result.status == "failed"
        assert result.stage_reached == "validation"
        assert result.validation is not None
        assert result.validation.passed is False
        assert "RL_EXIT_MUST_HAVE_STOP_LOSS" in result.red_line_result["triggered_rules"]
        assert result.preview is None
        assert result.backtest is None
        assert [r["operation"] for r in result.audit_records] == [
            "generation",
            "validation",
        ]
        assert result.problem_items

    def test_over_position_fails_red_line_and_skips_later_steps(
        self, db_paths: tuple[str, str]
    ) -> None:
        audit_path, storage_path = db_paths
        result = run_mvp_e2e_sample(
            "MA5上穿MA20买入，跌破MA10卖出，止损8%，仓位30%",
            "over_position",
            trace_id="trace-over-position",
            audit_db_path=audit_path,
            storage_db_path=storage_path,
        )

        assert result.status == "failed"
        assert result.stage_reached == "validation"
        assert result.validation is not None
        assert result.validation.passed is False
        assert "RL_MAX_POSITION" in result.red_line_result["triggered_rules"]
        assert result.preview is None
        assert result.backtest is None
        assert [r["operation"] for r in result.audit_records] == [
            "generation",
            "validation",
        ]
