"""Backtest Evidence - Trade record and event evidence construction.

Builds normalized trade records and trade event evidence dicts suitable
for storage via StrategyLabStorage. Separated from the engine main flow
for testability and clarity.

Design constraints:
    - Pure functions; no storage I/O.
    - Output dicts match storage.py column contracts.
    - All evidence includes triggered_conditions, timeframe_states,
      and indicator_snapshot per the contract.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from .dsl_schema import ConditionBlock, StrategyDSL


# ---------------------------------------------------------------------------
# Trade Records
# ---------------------------------------------------------------------------

def build_trade_records(
    signal_frame: pl.DataFrame,
    dsl: StrategyDSL,
    trace_id: str,
) -> list[dict[str, Any]]:
    """Build trade records from a completed signal frame.

    Extracts closed trades (where exit_date is not null) and open trades
    from the signal frame.

    Args:
        signal_frame: Completed signal frame with trade_id, entry_date,
            entry_price, exit_date, exit_price, shares, pnl, pnl_pct,
            exit_reason, entry_cost, exit_cost, total_cost columns.
        dsl: Strategy DSL for strategy_id.
        trace_id: Audit trace ID.

    Returns:
        List of dicts compatible with StrategyLabStorage.save_trade_record().
    """
    records: list[dict[str, Any]] = []

    if signal_frame.is_empty():
        return records

    # Required columns check
    required = [
        "trade_id", "symbol", "entry_date", "entry_price",
        "shares", "exit_date", "exit_price", "pnl", "pnl_pct",
        "exit_reason",
    ]
    missing = [c for c in required if c not in signal_frame.columns]
    if missing:
        return records

    # Only process rows that belong to a trade. This avoids converting the
    # entire multi-million row signal frame into Python dicts.
    trade_rows = signal_frame.filter(
        pl.col("trade_id").is_not_null() & (pl.col("trade_id") != "")
    )
    rows = trade_rows.to_dicts()
    seen_trade_ids: set[str] = set()

    for row in rows:
        tid = row.get("trade_id")
        if not tid or tid == "":
            continue
        if tid in seen_trade_ids:
            continue

        # Only process rows that have entry data
        entry_date = row.get("entry_date")
        if not entry_date or entry_date == "":
            continue

        seen_trade_ids.add(tid)

        exit_date = row.get("exit_date")
        is_closed = exit_date is not None and exit_date != ""

        record: dict[str, Any] = {
            "trade_id": str(tid),
            "strategy_id": dsl.strategy_id,
            "trace_id": trace_id,
            "symbol": row.get("symbol", ""),
            "side": "long",
            "status": "closed" if is_closed else "open",
            "entry_time": str(entry_date),
            "entry_price": row.get("entry_price"),
            "exit_time": str(exit_date) if is_closed else None,
            "exit_price": row.get("exit_price") if is_closed else None,
            "quantity": row.get("shares"),
            "pnl": row.get("pnl") if is_closed else None,
            "pnl_pct": row.get("pnl_pct") if is_closed else None,
        }
        records.append(record)

    return records


# ---------------------------------------------------------------------------
# Trade Event Evidence
# ---------------------------------------------------------------------------

def build_trade_event_evidence(
    signal_frame: pl.DataFrame,
    dsl: StrategyDSL,
    trace_id: str,
) -> list[dict[str, Any]]:
    """Build trade event evidence from a completed signal frame.

    For each trade, generates:
    - One ``entry`` event at the entry date.
    - One exit event at the exit date (type depends on exit_reason):
        - stop_loss_pct -> event_type="stop_loss"
        - take_profit_pct -> event_type="take_profit"
        - others -> event_type="exit"
    - If exit was blocked (e.g. limit_down), event_type="hold".

    Args:
        signal_frame: Completed signal frame with all trade columns
            plus indicator/state columns from the original data.
        dsl: Strategy DSL for condition metadata.
        trace_id: Audit trace ID.

    Returns:
        List of dicts compatible with
        StrategyLabStorage.save_trade_event_evidence().
    """
    events: list[dict[str, Any]] = []

    if signal_frame.is_empty():
        return events

    required = ["trade_id", "symbol", "entry_date", "entry_price"]
    missing = [c for c in required if c not in signal_frame.columns]
    if missing:
        return events

    # Only process rows that belong to a trade.
    trade_rows = signal_frame.filter(
        pl.col("trade_id").is_not_null() & (pl.col("trade_id") != "")
    )
    rows = trade_rows.to_dicts()
    seen_entries: set[tuple[str, str]] = set()
    seen_exits: set[tuple[str, str]] = set()

    for row in rows:
        tid = row.get("trade_id")
        if not tid or tid == "":
            continue

        symbol = row.get("symbol", "")
        entry_date = row.get("entry_date")
        if not entry_date or entry_date == "":
            continue

        # Build indicator snapshot and timeframe states from the row
        indicator_snapshot = _extract_indicator_snapshot(row)
        timeframe_states = _extract_timeframe_states(row)

        # Entry event (one per trade)
        entry_key = (str(tid), str(entry_date))
        if entry_key not in seen_entries:
            seen_entries.add(entry_key)

            entry_conditions = _build_triggered_conditions(
                dsl.entry, "entry", row
            )
            filter_conditions = _build_triggered_conditions(
                dsl.filters, "filters", row
            )
            triggered = entry_conditions + filter_conditions

            events.append({
                "trade_id": str(tid),
                "strategy_id": dsl.strategy_id,
                "trace_id": trace_id,
                "symbol": symbol,
                "event_type": "entry",
                "event_time": str(entry_date),
                "price": row.get("entry_price"),
                "timeframe_states": timeframe_states,
                "indicator_snapshot": indicator_snapshot,
                "triggered_conditions": triggered,
                "notes": "",
            })

        # Exit event (one per closed trade)
        exit_date = row.get("exit_date")
        if exit_date and exit_date != "":
            exit_key = (str(tid), str(exit_date))
            if exit_key not in seen_exits:
                seen_exits.add(exit_key)

                exit_reason = row.get("exit_reason", "")
                event_type = _exit_reason_to_event_type(exit_reason)

                # Check for blocked exit
                blocked = row.get("blocked_exit_reason")
                if blocked and blocked != "":
                    event_type = "hold"
                    notes = f"blocked_exit: {blocked}"
                else:
                    notes = ""

                exit_conditions = _build_triggered_conditions(
                    dsl.exit, "exit", row
                )

                # Rebuild indicator snapshot at exit time
                exit_indicator = _extract_indicator_snapshot(row, prefix="exit_")
                if not exit_indicator:
                    exit_indicator = indicator_snapshot

                events.append({
                    "trade_id": str(tid),
                    "strategy_id": dsl.strategy_id,
                    "trace_id": trace_id,
                    "symbol": symbol,
                    "event_type": event_type,
                    "event_time": str(exit_date),
                    "price": row.get("exit_price"),
                    "timeframe_states": timeframe_states,
                    "indicator_snapshot": exit_indicator,
                    "triggered_conditions": exit_conditions,
                    "notes": notes,
                })

    return events


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _exit_reason_to_event_type(exit_reason: str) -> str:
    """Map exit reason to storage event type."""
    mapping = {
        "stop_loss_pct": "stop_loss",
        "take_profit_pct": "take_profit",
        "price_cross_ma": "exit",
        "ma_death_cross": "exit",
    }
    return mapping.get(exit_reason, "exit")


def _extract_indicator_snapshot(
    row: dict[str, Any],
    prefix: str = "",
) -> dict[str, Any]:
    """Extract indicator snapshot from a signal frame row.

    Looks for common indicator columns and builds the D1 snapshot.
    """
    snapshot: dict[str, Any] = {}
    indicator_keys = [
        "close", "open", "high", "low", "volume",
        "ma_5", "ma_10", "ma_20", "ma_60",
        "volume_ratio", "atr_14",
        "is_limit_up", "is_limit_down", "is_suspended",
    ]

    for key in indicator_keys:
        lookup_key = f"{prefix}{key}" if prefix else key
        if lookup_key in row and row[lookup_key] is not None:
            snapshot[key] = row[lookup_key]
        elif key in row and row[key] is not None:
            snapshot[key] = row[key]

    return {"D1": snapshot} if snapshot else {}


def _extract_timeframe_states(row: dict[str, Any]) -> dict[str, Any]:
    """Extract timeframe state values from a signal frame row."""
    states: dict[str, Any] = {}

    for tf in ["D1", "W1", "MN1"]:
        for col_name in [f"{tf.lower()}_state", f"state_hex_{tf.lower()}"]:
            if col_name in row and row[col_name] is not None:
                states[tf] = row[col_name]
                break

    return states


def _build_triggered_conditions(
    conditions: list[ConditionBlock],
    section: str,
    row: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build triggered_conditions list for evidence.

    Each condition in the DSL section is recorded with its params,
    logic, weight, and the signal value from the current row.
    """
    triggered: list[dict[str, Any]] = []

    for cond in conditions:
        # Determine signal value based on condition type
        signal_value = _get_signal_value(cond.condition_type, section, row)

        triggered.append({
            "section": section,
            "condition_type": cond.condition_type,
            "params": cond.params,
            "logic": cond.logic,
            "weight": cond.weight,
            "signal_value": signal_value,
        })

    return triggered


def _get_signal_value(
    condition_type: str,
    section: str,
    row: dict[str, Any],
) -> bool:
    """Determine whether a condition was triggered from the row data."""
    if section == "entry":
        return bool(row.get("entry_signal", False))
    elif section == "exit":
        if condition_type == "stop_loss_pct":
            return bool(row.get("stop_loss_signal", False))
        elif condition_type == "take_profit_pct":
            return bool(row.get("take_profit_signal", False))
        return bool(row.get("raw_exit_signal", False))
    elif section == "filters":
        return bool(row.get("filter_pass", True))
    return False
