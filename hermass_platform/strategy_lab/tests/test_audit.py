"""Tests for audit.py - StrategyAuditLogger."""

from __future__ import annotations

import os
import tempfile

import pytest

from hermass_platform.strategy_lab.audit import StrategyAuditLogger


@pytest.fixture
def db_path() -> str:
    path = tempfile.mktemp(suffix=".duckdb")
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def logger(db_path: str) -> StrategyAuditLogger:
    log = StrategyAuditLogger(db_path)
    log.init_schema()
    return log


class TestAuditSchema:
    def test_init_schema_creates_table(self, logger: StrategyAuditLogger) -> None:
        con = logger._connect()
        tables = con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        names = {t[0] for t in tables}
        assert "strategy_audit_log" in names


class TestLogOperations:
    def test_log_preview(self, logger: StrategyAuditLogger) -> None:
        logger.log_preview(
            trace_id="trace-1",
            strategy_id="strat_1",
            dsl_version="strategy_dsl_v2",
            input_payload={"dsl": {"a": 1}},
            output_payload={"hits": 42},
            red_line_result={"passed": True},
        )
        records = logger.list_by_trace_id("trace-1")
        assert len(records) == 1
        assert records[0].trace_id == "trace-1"
        assert records[0].operation == "preview"
        assert records[0].strategy_id == "strat_1"
        assert records[0].dsl_version == "strategy_dsl_v2"
        assert records[0].red_line_result == {"passed": True}
        assert records[0].input_hash != ""
        assert records[0].output_hash != ""

    def test_log_validation(self, logger: StrategyAuditLogger) -> None:
        logger.log_validation(
            trace_id="trace-v",
            strategy_id="strat_v",
            dsl_version="strategy_dsl_v2",
            input_payload={"dsl": {"a": 1}},
            output_payload={"passed": False},
            red_line_result={"passed": False, "triggered": ["RL_MAX_POSITION"]},
        )
        records = logger.list_by_trace_id("trace-v")
        assert len(records) == 1
        assert records[0].operation == "validation"
        assert records[0].red_line_result["passed"] is False

    def test_multiple_operations_same_trace(self, logger: StrategyAuditLogger) -> None:
        logger.log_generation(
            trace_id="trace-multi",
            strategy_id="strat_m",
            dsl_version="strategy_dsl_v2",
            input_payload={"nl": "买入"},
            output_payload={"dsl": {}},
        )
        logger.log_validation(
            trace_id="trace-multi",
            strategy_id="strat_m",
            dsl_version="strategy_dsl_v2",
            input_payload={"dsl": {}},
            output_payload={"passed": True},
            red_line_result={"passed": True},
        )
        logger.log_preview(
            trace_id="trace-multi",
            strategy_id="strat_m",
            dsl_version="strategy_dsl_v2",
            input_payload={"dsl": {}},
            output_payload={"hits": 10},
            red_line_result={"passed": True},
        )
        records = logger.list_by_trace_id("trace-multi")
        assert len(records) == 3
        ops = [r.operation for r in records]
        assert ops == ["generation", "validation", "preview"]

    def test_input_hash_stable(self, logger: StrategyAuditLogger) -> None:
        payload = {"dsl": {"entry": [{"type": "ma_golden_cross"}]}}
        logger.log_preview(
            trace_id="t-hash",
            strategy_id="s1",
            dsl_version="v2",
            input_payload=payload,
            output_payload={"hits": 5},
        )
        logger.log_preview(
            trace_id="t-hash2",
            strategy_id="s2",
            dsl_version="v2",
            input_payload=payload,
            output_payload={"hits": 5},
        )
        r1 = logger.list_by_trace_id("t-hash")
        r2 = logger.list_by_trace_id("t-hash2")
        assert r1[0].input_hash == r2[0].input_hash

    def test_input_hash_differs_for_different_dsl(self, logger: StrategyAuditLogger) -> None:
        logger.log_preview(
            trace_id="t-diff1",
            strategy_id="s1",
            dsl_version="v2",
            input_payload={"dsl": {"a": 1}},
            output_payload={"hits": 5},
        )
        logger.log_preview(
            trace_id="t-diff2",
            strategy_id="s1",
            dsl_version="v2",
            input_payload={"dsl": {"a": 2}},
            output_payload={"hits": 5},
        )
        r1 = logger.list_by_trace_id("t-diff1")
        r2 = logger.list_by_trace_id("t-diff2")
        assert r1[0].input_hash != r2[0].input_hash

    def test_list_by_trace_id_empty(self, logger: StrategyAuditLogger) -> None:
        records = logger.list_by_trace_id("nonexistent")
        assert records == []
