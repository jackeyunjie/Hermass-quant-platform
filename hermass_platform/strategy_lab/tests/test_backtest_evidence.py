"""Unit tests for backtest_evidence module.

Covers:
    - build_trade_records extracts closed and open trades.
    - build_trade_event_evidence generates entry + exit events.
    - Exit reason to event_type mapping (stop_loss, take_profit, exit).
    - Blocked exit produces hold event.
    - Indicator snapshot extraction.
    - Timeframe states extraction.
    - Triggered conditions structure.
    - Empty signal frame returns empty lists.
"""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest

from hermass_platform.strategy_lab.backtest_evidence import (
    build_trade_event_evidence,
    build_trade_records,
    _exit_reason_to_event_type,
    _extract_indicator_snapshot,
    _extract_timeframe_states,
    _build_triggered_conditions,
)
from hermass_platform.strategy_lab.dsl_schema import (
    ConditionBlock,
    RiskConfig,
    StrategyDSL,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dsl(
    entry: list[ConditionBlock] | None = None,
    exit: list[ConditionBlock] | None = None,
    filters: list[ConditionBlock] | None = None,
) -> StrategyDSL:
    return StrategyDSL(
        strategy_id="ev_test",
        name="Evidence Test",
        entry=entry or [
            ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            )
        ],
        exit=exit or [
            ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08}),
            ConditionBlock(
                condition_type="price_cross_ma",
                params={"timeframe": "D1", "ma_period": 10, "direction": "below"},
                logic="or",
            ),
        ],
        filters=filters or [],
        risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20, stop_loss_required=True),
    )


def _build_signal_frame_with_trades() -> pl.DataFrame:
    """Build a minimal signal frame with one closed and one open trade."""
    rows = [
        {
            "symbol": "A",
            "date": "2024-01-05",
            "open": 10.0,
            "high": 10.2,
            "low": 9.8,
            "close": 10.1,
            "volume": 1000000,
            "trade_id": "trace1:A:2024-01-05:1",
            "entry_date": "2024-01-05",
            "entry_price": 10.11,  # close * (1 + slippage)
            "shares": 1000,
            "exit_date": "2024-01-12",
            "exit_price": 9.29,  # close * (1 - slippage)
            "pnl": -830.0,
            "pnl_pct": -0.082,
            "exit_reason": "stop_loss_pct",
            "entry_signal": True,
            "filter_pass": True,
            "raw_exit_signal": False,
            "stop_loss_signal": True,
            "take_profit_signal": False,
            "position": True,
            "ma_5": 10.0,
            "ma_10": 9.9,
            "ma_20": 9.8,
            "volume_ratio": 1.5,
            "is_limit_up": False,
            "is_limit_down": False,
            "d1_state": "0x23",
            "w1_state": "0x21",
            "mn1_state": "0x11",
        },
        {
            "symbol": "B",
            "date": "2024-01-08",
            "open": 20.0,
            "high": 20.5,
            "low": 19.5,
            "close": 20.2,
            "volume": 500000,
            "trade_id": "trace1:B:2024-01-08:2",
            "entry_date": "2024-01-08",
            "entry_price": 20.22,
            "shares": 500,
            "exit_date": None,
            "exit_price": None,
            "pnl": None,
            "pnl_pct": None,
            "exit_reason": "",
            "entry_signal": True,
            "filter_pass": True,
            "raw_exit_signal": False,
            "stop_loss_signal": False,
            "take_profit_signal": False,
            "position": True,
            "ma_5": 20.0,
            "ma_10": 19.8,
            "volume_ratio": 1.2,
            "is_limit_up": False,
            "is_limit_down": False,
            "d1_state": "0x32",
        },
    ]
    return pl.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tests: build_trade_records
# ---------------------------------------------------------------------------

class TestBuildTradeRecords:
    """Tests for build_trade_records."""

    def test_extracts_closed_and_open_trades(self) -> None:
        """Both closed and open trades are extracted."""
        frame = _build_signal_frame_with_trades()
        dsl = _make_dsl()
        records = build_trade_records(frame, dsl, "trace1")

        assert len(records) == 2

        closed = [r for r in records if r["status"] == "closed"]
        open_trades = [r for r in records if r["status"] == "open"]
        assert len(closed) == 1
        assert len(open_trades) == 1

    def test_closed_trade_has_pnl(self) -> None:
        """Closed trade record has pnl and pnl_pct."""
        frame = _build_signal_frame_with_trades()
        dsl = _make_dsl()
        records = build_trade_records(frame, dsl, "trace1")

        closed = [r for r in records if r["status"] == "closed"][0]
        assert closed["pnl"] is not None
        assert closed["pnl_pct"] is not None
        assert closed["exit_price"] is not None

    def test_open_trade_no_pnl(self) -> None:
        """Open trade record has no pnl or exit data."""
        frame = _build_signal_frame_with_trades()
        dsl = _make_dsl()
        records = build_trade_records(frame, dsl, "trace1")

        open_trade = [r for r in records if r["status"] == "open"][0]
        assert open_trade["pnl"] is None
        assert open_trade["exit_time"] is None

    def test_trade_record_fields(self) -> None:
        """Trade record has all required fields."""
        frame = _build_signal_frame_with_trades()
        dsl = _make_dsl()
        records = build_trade_records(frame, dsl, "trace1")

        for record in records:
            assert "trade_id" in record
            assert "strategy_id" in record
            assert "trace_id" in record
            assert "symbol" in record
            assert "side" in record
            assert record["side"] == "long"
            assert record["trace_id"] == "trace1"
            assert record["strategy_id"] == "ev_test"

    def test_empty_signal_frame(self) -> None:
        """Empty signal frame returns empty list."""
        frame = pl.DataFrame(
            schema={
                "trade_id": pl.Utf8, "symbol": pl.Utf8,
                "entry_date": pl.Utf8, "entry_price": pl.Float64,
                "shares": pl.Int64, "exit_date": pl.Utf8,
                "exit_price": pl.Float64, "pnl": pl.Float64,
                "pnl_pct": pl.Float64, "exit_reason": pl.Utf8,
            }
        )
        dsl = _make_dsl()
        records = build_trade_records(frame, dsl, "trace1")
        assert records == []

    def test_deduplicates_trade_ids(self) -> None:
        """Same trade_id across multiple rows only produces one record."""
        # Two rows with same trade_id (entry row + holding row)
        rows = [
            {
                "symbol": "A", "date": "2024-01-05",
                "trade_id": "t1", "entry_date": "2024-01-05",
                "entry_price": 10.0, "shares": 100,
                "exit_date": None, "exit_price": None,
                "pnl": None, "pnl_pct": None, "exit_reason": "",
            },
            {
                "symbol": "A", "date": "2024-01-06",
                "trade_id": "t1", "entry_date": "2024-01-05",
                "entry_price": 10.0, "shares": 100,
                "exit_date": None, "exit_price": None,
                "pnl": None, "pnl_pct": None, "exit_reason": "",
            },
        ]
        frame = pl.DataFrame(rows)
        dsl = _make_dsl()
        records = build_trade_records(frame, dsl, "t1")
        assert len(records) == 1


# ---------------------------------------------------------------------------
# Tests: build_trade_event_evidence
# ---------------------------------------------------------------------------

class TestBuildTradeEventEvidence:
    """Tests for build_trade_event_evidence."""

    def test_generates_entry_and_exit_events(self) -> None:
        """Closed trade produces one entry + one exit event."""
        frame = _build_signal_frame_with_trades()
        dsl = _make_dsl()
        events = build_trade_event_evidence(frame, dsl, "trace1")

        entry_events = [e for e in events if e["event_type"] == "entry"]
        # Exit events include stop_loss, take_profit, exit, hold
        exit_events = [e for e in events if e["event_type"] in ("exit", "stop_loss", "take_profit", "hold")]

        assert len(entry_events) == 2  # Both trades have entry
        assert len(exit_events) == 1   # Only closed trade has exit

    def test_stop_loss_event_type(self) -> None:
        """Stop loss exit_reason produces event_type='stop_loss'."""
        frame = _build_signal_frame_with_trades()
        dsl = _make_dsl()
        events = build_trade_event_evidence(frame, dsl, "trace1")

        stop_events = [e for e in events if e["event_type"] == "stop_loss"]
        assert len(stop_events) == 1
        assert stop_events[0]["trade_id"] == "trace1:A:2024-01-05:1"

    def test_blocked_exit_produces_hold(self) -> None:
        """Blocked exit (e.g. limit_down) produces event_type='hold'."""
        rows = [{
            "symbol": "X", "date": "2024-01-10",
            "open": 10.0, "high": 10.2, "low": 9.8, "close": 10.0,
            "volume": 100000,
            "trade_id": "t1", "entry_date": "2024-01-05",
            "entry_price": 10.5, "shares": 100,
            "exit_date": "2024-01-10", "exit_price": 9.49,
            "pnl": -110.0, "pnl_pct": -0.10,
            "exit_reason": "stop_loss_pct",
            "blocked_exit_reason": "limit_down_blocked_stop_loss_pct",
            "entry_signal": True, "filter_pass": True,
            "stop_loss_signal": True, "take_profit_signal": False,
            "raw_exit_signal": False,
        }]
        frame = pl.DataFrame(rows)
        dsl = _make_dsl()
        events = build_trade_event_evidence(frame, dsl, "trace1")

        hold_events = [e for e in events if e["event_type"] == "hold"]
        assert len(hold_events) == 1
        assert "blocked_exit" in hold_events[0]["notes"]

    def test_event_has_triggered_conditions(self) -> None:
        """Events include triggered_conditions from DSL."""
        frame = _build_signal_frame_with_trades()
        dsl = _make_dsl()
        events = build_trade_event_evidence(frame, dsl, "trace1")

        entry_events = [e for e in events if e["event_type"] == "entry"]
        assert len(entry_events) > 0

        for event in entry_events:
            assert "triggered_conditions" in event
            tc = event["triggered_conditions"]
            assert isinstance(tc, list)
            if tc:
                assert "section" in tc[0]
                assert "condition_type" in tc[0]
                assert "params" in tc[0]

    def test_event_has_indicator_snapshot(self) -> None:
        """Events include indicator_snapshot with D1 data."""
        frame = _build_signal_frame_with_trades()
        dsl = _make_dsl()
        events = build_trade_event_evidence(frame, dsl, "trace1")

        assert len(events) > 0
        for event in events:
            assert "indicator_snapshot" in event

    def test_event_has_timeframe_states(self) -> None:
        """Events include timeframe_states (D1, W1, MN1)."""
        frame = _build_signal_frame_with_trades()
        dsl = _make_dsl()
        events = build_trade_event_evidence(frame, dsl, "trace1")

        # At least one event should have D1 state
        d1_found = any(
            "D1" in e.get("timeframe_states", {})
            for e in events
        )
        assert d1_found, "Expected D1 state in at least one event"

    def test_empty_frame_returns_empty(self) -> None:
        """Empty signal frame returns empty event list."""
        frame = pl.DataFrame(
            schema={"trade_id": pl.Utf8, "symbol": pl.Utf8, "entry_date": pl.Utf8, "entry_price": pl.Float64}
        )
        dsl = _make_dsl()
        events = build_trade_event_evidence(frame, dsl, "trace1")
        assert events == []


# ---------------------------------------------------------------------------
# Tests: Helper Functions
# ---------------------------------------------------------------------------

class TestHelperFunctions:
    """Tests for internal helper functions."""

    def test_exit_reason_to_event_type_stop_loss(self) -> None:
        assert _exit_reason_to_event_type("stop_loss_pct") == "stop_loss"

    def test_exit_reason_to_event_type_take_profit(self) -> None:
        assert _exit_reason_to_event_type("take_profit_pct") == "take_profit"

    def test_exit_reason_to_event_type_price_cross(self) -> None:
        assert _exit_reason_to_event_type("price_cross_ma") == "exit"

    def test_exit_reason_to_event_type_death_cross(self) -> None:
        assert _exit_reason_to_event_type("ma_death_cross") == "exit"

    def test_exit_reason_to_event_type_unknown(self) -> None:
        assert _exit_reason_to_event_type("unknown_reason") == "exit"

    def test_extract_indicator_snapshot(self) -> None:
        row: dict[str, Any] = {
            "close": 10.5, "ma_5": 10.3, "volume": 100000,
            "is_limit_up": False,
        }
        snapshot = _extract_indicator_snapshot(row)
        assert "D1" in snapshot
        assert snapshot["D1"]["close"] == 10.5
        assert snapshot["D1"]["ma_5"] == 10.3

    def test_extract_indicator_snapshot_empty(self) -> None:
        snapshot = _extract_indicator_snapshot({"unrelated": 42})
        assert snapshot == {}

    def test_extract_timeframe_states(self) -> None:
        row: dict[str, Any] = {
            "d1_state": "0x23",
            "w1_state": "0x21",
            "mn1_state": "0x11",
        }
        states = _extract_timeframe_states(row)
        assert states["D1"] == "0x23"
        assert states["W1"] == "0x21"
        assert states["MN1"] == "0x11"

    def test_extract_timeframe_states_missing(self) -> None:
        states = _extract_timeframe_states({"no_state": True})
        assert states == {}

    def test_build_triggered_conditions(self) -> None:
        conditions = [
            ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            ),
        ]
        row: dict[str, Any] = {"entry_signal": True}
        result = _build_triggered_conditions(conditions, "entry", row)

        assert len(result) == 1
        assert result[0]["section"] == "entry"
        assert result[0]["condition_type"] == "ma_golden_cross"
        assert result[0]["signal_value"] == True
