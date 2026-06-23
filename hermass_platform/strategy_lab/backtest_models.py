"""Backtest Models - Internal dataclass contracts for Light Backtest v1.

These models define the internal data flow between provider, engine, and
storage layers. They are NOT part of the public API (see api_models.py).

Design constraints:
    - Frozen dataclasses for immutability.
    - No business logic; pure data containers.
    - Polars DataFrame for tabular data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import polars as pl


# ---------------------------------------------------------------------------
# Data Provider Contracts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MarketDataRequest:
    """Request to load market data from DuckDB.

    Attributes:
        start_date: Inclusive start date (YYYY-MM-DD).
        end_date: Inclusive end date (YYYY-MM-DD).
        required_columns: Columns that MUST exist in the loaded data.
        universe: Optional list of symbols to filter. None = all.
        include_state: Whether to join state_cube data.
    """

    start_date: str
    end_date: str
    required_columns: list[str]
    universe: list[str] | None = None
    include_state: bool = True


@dataclass(frozen=True)
class MarketDataBundle:
    """Loaded and normalized market data bundle.

    Attributes:
        bars: Polars DataFrame with daily OHLCV + indicators + state.
        data_version: Identifier for data freshness tracking.
        warnings: Data quality warnings (missing columns, gaps, etc.).
        source_summary: Metadata about data sources (row counts, date range).
    """

    bars: pl.DataFrame
    data_version: str
    warnings: list[str]
    source_summary: dict[str, Any]


# ---------------------------------------------------------------------------
# Signal Frame Contract
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SignalFrame:
    """Intermediate signal computation result.

    The signal frame is the core data structure produced by the engine's
    signal computation phase. It contains per-symbol per-date rows with
    entry/exit/filter signals before position and trade generation.

    Required columns in ``frame``:
        symbol, date, open, high, low, close,
        entry_signal, filter_pass, raw_exit_signal,
        stop_loss_signal, take_profit_signal,
        exit_signal, exit_reason,
        position, entry_price, shares, trade_id,
        daily_return, portfolio_value
    """

    frame: pl.DataFrame
    required_columns: list[str]
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Backtest Execution Contracts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TradeSummary:
    """Summary of a single closed trade.

    Attributes:
        trade_id: Unique trade identifier.
        symbol: Stock symbol.
        side: Always "long" for MVP.
        entry_date: Entry date string.
        entry_price: Entry fill price.
        exit_date: Exit date string.
        exit_price: Exit fill price.
        shares: Number of shares.
        pnl: Profit/loss in RMB.
        pnl_pct: Profit/loss percentage.
        exit_reason: Why the trade was closed.
        entry_cost: Buy-side transaction cost.
        exit_cost: Sell-side transaction cost.
        total_cost: Total transaction cost.
    """

    trade_id: str
    symbol: str
    side: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    shares: int
    pnl: float
    pnl_pct: float
    exit_reason: str
    entry_cost: float = 0.0
    exit_cost: float = 0.0
    total_cost: float = 0.0


@dataclass(frozen=True)
class EquityPoint:
    """Single day in the portfolio equity curve."""

    date: str
    portfolio_value: float
    daily_return: float


@dataclass
class LightBacktestOutput:
    """Complete output from LightBacktestEngine.run().

    This is the engine's return value before adapter wrapping.
    """

    mode: str = "light_real_v1"
    status: str = "success"
    metrics: dict[str, float | int | None] = field(default_factory=dict)
    trades: list[TradeSummary] = field(default_factory=list)
    daily_curve: list[EquityPoint] = field(default_factory=list)
    signal_frame: pl.DataFrame | None = None
    warnings: list[str] = field(default_factory=list)
    data_version: str | None = None
    elapsed_seconds: float = 0.0
    state_breakdown: dict[str, Any] = field(default_factory=dict)
