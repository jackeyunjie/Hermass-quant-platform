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
    def test_init_schema_creates_three_tables(self, storage: StrategyLabStorage) -> None:
        con = storage._connect()
        tables = con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        names = {t[0] for t in tables}
        assert "user_strategies" in names
        assert "strategy_versions" in names
        assert "strategy_backtests" in names


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
