"""Tests for storage.py - StrategyLabStorage."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from hermass_platform.strategy_lab.storage import StrategyLabStorage


@pytest.fixture
def db_path() -> str:
    path = tempfile.mktemp(suffix=".duckdb")
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def storage(db_path: str) -> StrategyLabStorage:
    s = StrategyLabStorage(db_path)
    s.init_schema()
    return s


class TestStorageSchema:
    def test_init_schema_creates_strategy_and_trade_tables(
        self, storage: StrategyLabStorage
    ) -> None:
        con = storage._connect()
        tables = con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        names = {t[0] for t in tables}
        assert "user_strategies" in names
        assert "strategy_versions" in names
        assert "strategy_backtests" in names
        assert "strategy_trades" in names
        assert "strategy_trade_events" in names


class TestSaveAndRetrieve:
    def test_save_strategy_version(self, storage: StrategyLabStorage) -> None:
        dsl = {"name": "Test Strategy", "description": "A test"}
        storage.save_strategy_version(
            strategy_id="test_1",
            dsl=dsl,
            trace_id="trace-1",
            input_hash="abc123",
            output_hash="def456",
        )
        versions = storage.get_strategy_versions("test_1")
        assert len(versions) == 1
        assert versions[0].strategy_id == "test_1"
        assert versions[0].trace_id == "trace-1"
        assert versions[0].input_hash == "abc123"
        assert versions[0].output_hash == "def456"
        assert versions[0].dsl == dsl

    def test_save_multiple_versions(self, storage: StrategyLabStorage) -> None:
        for i in range(3):
            storage.save_strategy_version(
                strategy_id="multi_v",
                dsl={"version": i},
                trace_id=f"trace-{i}",
                input_hash=f"in{i}",
                output_hash=f"out{i}",
            )
        versions = storage.get_strategy_versions("multi_v")
        assert len(versions) == 3

    def test_save_backtest_result(self, storage: StrategyLabStorage) -> None:
        storage.save_strategy_version(
            strategy_id="bt_1",
            dsl={"name": "BT"},
            trace_id="trace-bt",
            input_hash="in",
            output_hash="out",
        )
        storage.save_backtest_result(
            strategy_id="bt_1",
            trace_id="trace-bt",
            status="success",
            metrics={"total_return": 0.12, "sharpe_ratio": 1.5},
            dsl_snapshot={"name": "BT"},
        )
        bt = storage.get_backtest("trace-bt")
        assert bt is not None
        assert bt.strategy_id == "bt_1"
        assert bt.status == "success"
        assert bt.metrics["total_return"] == 0.12
        assert bt.dsl_snapshot == {"name": "BT"}

    def test_get_backtest_missing(self, storage: StrategyLabStorage) -> None:
        bt = storage.get_backtest("nonexistent")
        assert bt is None

    def test_json_roundtrip(self, storage: StrategyLabStorage) -> None:
        dsl = {"nested": {"key": [1, 2, 3]}, "unicode": "中文"}
        storage.save_strategy_version(
            strategy_id="json_test",
            dsl=dsl,
            trace_id="t-json",
            input_hash="h1",
            output_hash="h2",
        )
        versions = storage.get_strategy_versions("json_test")
        assert len(versions) == 1
        assert versions[0].dsl == dsl

    def test_backtest_json_roundtrip(self, storage: StrategyLabStorage) -> None:
        storage.save_strategy_version(
            strategy_id="json_bt",
            dsl={},
            trace_id="t-bt",
            input_hash="h1",
            output_hash="h2",
        )
        metrics = {"total_return": 0.05, "nested": {"a": True}}
        storage.save_backtest_result(
            strategy_id="json_bt",
            trace_id="t-bt",
            status="partial",
            metrics=metrics,
        )
        bt = storage.get_backtest("t-bt")
        assert bt is not None
        assert bt.metrics == metrics

    def test_save_trade_record_and_event_evidence(self, storage: StrategyLabStorage) -> None:
        storage.save_strategy_version(
            strategy_id="trade_strategy",
            dsl={"name": "Trade Evidence Strategy"},
            trace_id="trace-trade",
            input_hash="in-trade",
            output_hash="out-trade",
        )
        storage.save_trade_record(
            trade_id="trade-001",
            strategy_id="trade_strategy",
            trace_id="trace-trade",
            symbol="000001.SZ",
            side="long",
            status="closed",
            entry_time="2026-06-01 09:30:00",
            entry_price=10.0,
            exit_time="2026-06-05 14:55:00",
            exit_price=10.8,
            quantity=1000,
            pnl=800.0,
            pnl_pct=0.08,
        )
        storage.save_trade_event_evidence(
            trade_id="trade-001",
            strategy_id="trade_strategy",
            trace_id="trace-trade",
            symbol="000001.SZ",
            event_type="entry",
            event_time="2026-06-01 09:30:00",
            price=10.0,
            timeframe_states={
                "MN1": "0x11",
                "W1": "0x21",
                "D1": "0x23",
                "H4": "0x31",
                "H1": "0x32",
            },
            indicator_snapshot={
                "D1": {
                    "ma_5": 9.8,
                    "ma_20": 9.6,
                    "volume_ratio_20": 1.7,
                    "atr_14": 0.42,
                },
                "H1": {"rsi_14": 58.0},
            },
            triggered_conditions=[
                {
                    "condition_type": "ma_golden_cross",
                    "params": {"fast_period": 5, "slow_period": 20},
                    "section": "entry",
                }
            ],
            notes="entry snapshot",
        )
        storage.save_trade_event_evidence(
            trade_id="trade-001",
            strategy_id="trade_strategy",
            trace_id="trace-trade",
            symbol="000001.SZ",
            event_type="exit",
            event_time="2026-06-05 14:55:00",
            price=10.8,
            timeframe_states={"D1": "0x24", "H1": "0x12"},
            indicator_snapshot={"D1": {"close": 10.8, "ma_10": 10.9}},
            triggered_conditions=[
                {
                    "condition_type": "price_cross_ma",
                    "params": {"ma_period": 10, "direction": "below"},
                    "section": "exit",
                }
            ],
            notes="exit snapshot",
        )

        trades = storage.list_trades(strategy_id="trade_strategy")
        assert len(trades) == 1
        assert trades[0].trade_id == "trade-001"
        assert trades[0].symbol == "000001.SZ"
        assert trades[0].status == "closed"
        assert trades[0].pnl_pct == 0.08

        by_trace = storage.list_trades(trace_id="trace-trade")
        assert len(by_trace) == 1
        assert by_trace[0].strategy_id == "trade_strategy"

        events = storage.list_trade_events("trade-001")
        assert [event.event_type for event in events] == ["entry", "exit"]
        assert events[0].timeframe_states["MN1"] == "0x11"
        assert events[0].indicator_snapshot["D1"]["volume_ratio_20"] == 1.7
        assert events[0].triggered_conditions[0]["condition_type"] == "ma_golden_cross"
        assert events[1].timeframe_states["D1"] == "0x24"

    def test_trade_record_upsert(self, storage: StrategyLabStorage) -> None:
        storage.save_strategy_version(
            strategy_id="upsert_strategy",
            dsl={"name": "Upsert Strategy"},
            trace_id="trace-upsert",
            input_hash="in-upsert",
            output_hash="out-upsert",
        )
        storage.save_trade_record(
            trade_id="trade-upsert",
            strategy_id="upsert_strategy",
            trace_id="trace-upsert",
            symbol="000002.SZ",
            side="long",
            status="open",
            entry_time="2026-06-01 09:30:00",
            entry_price=20.0,
        )
        storage.save_trade_record(
            trade_id="trade-upsert",
            strategy_id="upsert_strategy",
            trace_id="trace-upsert",
            symbol="000002.SZ",
            side="long",
            status="closed",
            entry_time="2026-06-01 09:30:00",
            entry_price=20.0,
            exit_time="2026-06-02 14:55:00",
            exit_price=19.0,
            pnl=-1000.0,
            pnl_pct=-0.05,
        )

        trades = storage.list_trades(strategy_id="upsert_strategy")
        assert len(trades) == 1
        assert trades[0].status == "closed"
        assert trades[0].exit_price == 19.0
        assert trades[0].pnl_pct == -0.05
