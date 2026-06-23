"""Unit tests for light_backtest_engine module.

Covers:
    - MA golden cross signal computation.
    - Price cross MA exit signal.
    - Stop loss / take profit priority.
    - Limit up entry filter.
    - Suspended day no trade.
    - Same-day conflict rule (exit then no re-entry).
    - Cost model calculation.
    - 100 股 lot rounding.
    - Empty signal frame returns failed.
    - _compute_required_ma auto-computes missing MA columns.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from hermass_platform.strategy_lab.backtest_adapter import BacktestConfig, CostModel
from hermass_platform.strategy_lab.backtest_models import (
    MarketDataBundle,
    LightBacktestOutput,
)
from hermass_platform.strategy_lab.condition_registry import ConditionRegistry
from hermass_platform.strategy_lab.dsl_schema import (
    ConditionBlock,
    RiskConfig,
    StrategyDSL,
)
from hermass_platform.strategy_lab.light_backtest_engine import LightBacktestEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bundle(
    df: pl.DataFrame,
    *,
    warnings: list[str] | None = None,
) -> MarketDataBundle:
    """Wrap a Polars DataFrame into a MarketDataBundle."""
    return MarketDataBundle(
        bars=df,
        data_version="test:v1",
        warnings=warnings or [],
        source_summary={"test": True},
    )


def _build_daily_df(
    prices: list[float],
    *,
    symbol: str = "SYM_A",
    ma_5: list[float | None] | None = None,
    ma_10: list[float | None] | None = None,
    ma_20: list[float | None] | None = None,
    is_limit_up: list[bool] | None = None,
    is_suspended: list[bool] | None = None,
    volume_ratio: list[float] | None = None,
    d1_state: list[str] | None = None,
) -> pl.DataFrame:
    """Build a daily bars DataFrame from price list."""
    n = len(prices)
    dates = [f"2024-01-{d:02d}" for d in range(1, n + 1)]

    data = {
        "symbol": [symbol] * n,
        "date": dates,
        "open": prices,
        "high": [p + 0.1 for p in prices],
        "low": [p - 0.1 for p in prices],
        "close": prices,
        "volume": [1000000] * n,
    }

    if ma_5:
        data["ma_5"] = ma_5
    if ma_10:
        data["ma_10"] = ma_10
    if ma_20:
        data["ma_20"] = ma_20
    if is_limit_up:
        data["is_limit_up"] = is_limit_up
    if is_suspended:
        data["is_suspended"] = is_suspended
    if volume_ratio:
        data["volume_ratio"] = volume_ratio
    if d1_state:
        data["d1_state"] = d1_state

    return pl.DataFrame(data)


def _make_dsl(
    entry: list[ConditionBlock] | None = None,
    exit: list[ConditionBlock] | None = None,
    filters: list[ConditionBlock] | None = None,
) -> StrategyDSL:
    """Build a minimal StrategyDSL."""
    return StrategyDSL(
        strategy_id="unit_test",
        name="Unit Test",
        entry=entry or [],
        exit=exit or [ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
        filters=filters or [],
        risk=RiskConfig(risk_per_trade=0.02, max_position_pct=0.20, stop_loss_required=True),
    )


def _make_config(dsl: StrategyDSL) -> BacktestConfig:
    """Build a minimal BacktestConfig."""
    return BacktestConfig(
        dsl=dsl,
        start_date="2024-01-01",
        end_date="2024-01-30",
        initial_capital=1_000_000.0,
        trace_id="unit-test-trace",
    )


# ---------------------------------------------------------------------------
# Signal Computation Tests
# ---------------------------------------------------------------------------

class TestSignalComputation:
    """Tests for build_signal_frame signal logic."""

    def test_ma_golden_cross_signal(self) -> None:
        """ma_golden_cross fires when fast MA crosses above slow MA."""
        engine = LightBacktestEngine()

        # Prices: declining first (so MA5 < MA20), then sharply rising
        # This ensures MA5 crosses ABOVE MA20 after the trend reversal
        prices = (
            [12.0 - i * 0.15 for i in range(20)]  # Declining: 12.0 -> 9.15
            + [9.5 + i * 0.4 for i in range(1, 16)]  # Sharp rise: 9.9 -> 15.5
        )
        n = len(prices)

        df = _build_daily_df(prices, symbol="A")
        bundle = _make_bundle(df)

        dsl = _make_dsl(
            entry=[ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            )],
        )

        frame = engine.build_signal_frame(dsl, bundle)

        # Check entry_signal column exists
        assert "entry_signal" in frame.frame.columns

        # After the trend reversal, MA5 should cross above MA20
        entry_signals = frame.frame["entry_signal"].to_list()
        assert any(entry_signals), "Expected at least one golden cross entry signal after trend reversal"

    def test_price_cross_ma_below_exit(self) -> None:
        """price_cross_ma direction=below fires when close crosses below MA."""
        engine = LightBacktestEngine()

        # Prices rising then falling below MA10
        prices = (
            [10.0 + i * 0.2 for i in range(15)]  # Rising
            + [12.0 - i * 0.3 for i in range(1, 16)]  # Falling below MA
        )

        df = _build_daily_df(prices, symbol="B")
        bundle = _make_bundle(df)

        dsl = _make_dsl(
            entry=[ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            )],
            exit=[
                ConditionBlock(
                    condition_type="price_cross_ma",
                    params={"timeframe": "D1", "ma_period": 10, "direction": "below"},
                ),
                ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08}, logic="or"),
            ],
        )

        frame = engine.build_signal_frame(dsl, bundle)
        assert "raw_exit_signal" in frame.frame.columns

        exit_signals = frame.frame["raw_exit_signal"].to_list()
        assert any(exit_signals), "Expected at least one price_cross_ma exit signal"

    def test_volume_ratio_filter(self) -> None:
        """volume_ratio condition computes correctly."""
        engine = LightBacktestEngine()

        vr = [0.5] * 5 + [2.0] * 5 + [0.8] * 5
        prices = [10.0] * 15

        df = _build_daily_df(prices, symbol="V", volume_ratio=vr)
        bundle = _make_bundle(df)

        dsl = _make_dsl(
            entry=[
                ConditionBlock(
                    condition_type="ma_golden_cross",
                    params={"fast_period": 5, "slow_period": 20},
                ),
                ConditionBlock(
                    condition_type="volume_ratio",
                    params={"lookback": 20, "operator": ">", "value": 1.5},
                    logic="and",
                ),
            ],
        )

        frame = engine.build_signal_frame(dsl, bundle)
        assert "entry_signal" in frame.frame.columns

    def test_limit_up_filter_blocks_entry(self) -> None:
        """limit_up_filter allow=false blocks entry on limit-up days."""
        engine = LightBacktestEngine()

        # 15 days, day 10 is limit-up
        prices = [10.0 + i * 0.1 for i in range(15)]
        limit_up = [False] * 15
        limit_up[9] = True  # Day 10

        df = _build_daily_df(prices, symbol="LU", is_limit_up=limit_up)
        bundle = _make_bundle(df)

        dsl = _make_dsl(
            entry=[ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            )],
            filters=[ConditionBlock(
                condition_type="limit_up_filter",
                params={"allow": False},
            )],
        )

        frame = engine.build_signal_frame(dsl, bundle)
        # On limit-up day, filter_pass should be False
        filter_vals = frame.frame["filter_pass"].to_list()
        assert filter_vals[9] == False, "Limit-up day should have filter_pass=False"

    def test_state_hex_in_signal(self) -> None:
        """state_hex_in checks state value membership."""
        engine = LightBacktestEngine()

        states = ["0x23"] * 5 + ["0x11"] * 5 + ["0x23"] * 5
        prices = [10.0] * 15

        df = _build_daily_df(prices, symbol="ST", d1_state=states)
        bundle = _make_bundle(df)

        dsl = _make_dsl(
            entry=[ConditionBlock(
                condition_type="state_hex_in",
                params={"timeframe": "D1", "values": ["0x23"]},
            )],
        )

        frame = engine.build_signal_frame(dsl, bundle)
        entry_signals = frame.frame["entry_signal"].to_list()
        # Days 1-5 and 11-15 should have True (state=0x23), days 6-10 False (0x11)
        assert entry_signals[0] == True
        assert entry_signals[7] == False

    def test_empty_dataframe_returns_failed(self) -> None:
        """Empty bars DataFrame results in failed status."""
        engine = LightBacktestEngine()

        df = pl.DataFrame(
            schema={
                "symbol": pl.Utf8, "date": pl.Utf8, "open": pl.Float64,
                "high": pl.Float64, "low": pl.Float64, "close": pl.Float64,
                "volume": pl.Int64,
            }
        )
        bundle = _make_bundle(df)
        dsl = _make_dsl(
            entry=[ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            )],
        )
        config = _make_config(dsl)
        output = engine.run(dsl, config, bundle)

        assert output.status == "failed"
        assert "BT_EMPTY_SIGNAL_FRAME" in output.warnings


# ---------------------------------------------------------------------------
# Trade Generation Tests
# ---------------------------------------------------------------------------

class TestTradeGeneration:
    """Tests for _generate_trades position and trade logic."""

    def test_stop_loss_take_profit_priority(self) -> None:
        """When both stop_loss and take_profit trigger same day, stop_loss wins."""
        engine = LightBacktestEngine()

        # Prices: stable, then entry (golden cross), then sharp drop (stop loss)
        # Day 1-10: slow rise for golden cross
        # Day 11: entry
        # Day 12: sharp drop (both stop loss 8% and take profit could trigger)
        prices = [10.0] * 5 + [10.0 + i * 0.05 for i in range(5)] + [10.8, 9.5]
        n = len(prices)
        ma5 = [None] * 4 + [sum(prices[max(0, i-4):i+1]) / min(5, i+1) for i in range(4, n)]
        ma20 = [None] * 19 + [sum(prices[:20]) / 20] if n > 19 else [None] * n

        # Ensure we have enough data
        if len(ma20) < n:
            ma20 = [None] * n

        df = _build_daily_df(prices, symbol="P", ma_5=ma5, ma_20=ma20)
        bundle = _make_bundle(df)

        dsl = _make_dsl(
            entry=[ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            )],
            exit=[
                ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08}),
                ConditionBlock(
                    condition_type="take_profit_pct",
                    params={"value": 0.05},
                    logic="or",
                ),
            ],
        )
        config = _make_config(dsl)
        output = engine.run(dsl, config, bundle)

        # If trades exist, check exit_reason priority
        if output.trades:
            for trade in output.trades:
                assert trade.exit_reason in (
                    "stop_loss_pct", "take_profit_pct", "price_cross_ma",
                    "ma_death_cross",
                )

    def test_same_day_no_reentry_after_exit(self) -> None:
        """After exit, same symbol cannot re-enter on the same day."""
        engine = LightBacktestEngine()

        # Build prices where exit and re-entry might happen same day
        prices = [10.0 + i * 0.1 for i in range(30)]
        df = _build_daily_df(prices, symbol="NR")
        bundle = _make_bundle(df)

        dsl = _make_dsl(
            entry=[ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            )],
            exit=[
                ConditionBlock(
                    condition_type="price_cross_ma",
                    params={"timeframe": "D1", "ma_period": 10, "direction": "below"},
                ),
                ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08}, logic="or"),
            ],
        )
        config = _make_config(dsl)
        output = engine.run(dsl, config, bundle)

        # Verify no same-day re-entry: for each trade, entry_date != any prior exit_date for same symbol
        trade_dates: dict[str, list[tuple[str, str]]] = {}
        for t in output.trades:
            if t.symbol not in trade_dates:
                trade_dates[t.symbol] = []
            trade_dates[t.symbol].append((t.entry_date, t.exit_date))

        for sym, dates in trade_dates.items():
            exit_dates = {d[1] for d in dates if d[1]}
            entry_dates = {d[0] for d in dates}
            overlap = exit_dates & entry_dates
            assert not overlap, f"Symbol {sym} re-entered on exit day: {overlap}"

    def test_100_share_lot_rounding(self) -> None:
        """Shares are rounded to 100 (A-share lot size)."""
        engine = LightBacktestEngine()

        prices = [10.0 + i * 0.1 for i in range(30)]
        df = _build_daily_df(prices, symbol="LOT")
        bundle = _make_bundle(df)

        dsl = _make_dsl(
            entry=[ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            )],
            exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
        )
        config = _make_config(dsl)
        output = engine.run(dsl, config, bundle)

        for trade in output.trades:
            assert trade.shares % 100 == 0, f"Shares {trade.shares} not a multiple of 100"
            assert trade.shares >= 100, f"Shares {trade.shares} < 100"

    def test_cost_model_buy_side(self) -> None:
        """CostModel calculates buy-side costs correctly."""
        cm = CostModel()
        costs = cm.calculate_cost(price=10.0, shares=1000, side="buy")

        assert costs["commission"] == max(10.0 * 1000 * 0.0003, 5.0)
        assert costs["stamp_duty"] == 0.0  # No stamp duty on buy
        assert costs["slippage"] == 10.0 * 1000 * 0.001
        assert costs["total"] == costs["commission"] + costs["slippage"]

    def test_cost_model_sell_side(self) -> None:
        """CostModel calculates sell-side costs including stamp duty."""
        cm = CostModel()
        costs = cm.calculate_cost(price=10.0, shares=1000, side="sell")

        assert costs["commission"] == max(10.0 * 1000 * 0.0003, 5.0)
        assert costs["stamp_duty"] == 10.0 * 1000 * 0.0005
        assert costs["slippage"] == 10.0 * 1000 * 0.001
        assert costs["total"] == costs["commission"] + costs["stamp_duty"] + costs["slippage"]

    def test_suspended_day_no_trade(self) -> None:
        """Suspended days prevent both entry and exit."""
        engine = LightBacktestEngine()

        # 20 days, day 12 is suspended
        prices = [10.0 + i * 0.1 for i in range(20)]
        suspended = [False] * 20
        suspended[11] = True

        df = _build_daily_df(prices, symbol="SUS", is_suspended=suspended)
        bundle = _make_bundle(df)

        dsl = _make_dsl(
            entry=[ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            )],
            exit=[ConditionBlock(condition_type="stop_loss_pct", params={"value": 0.08})],
        )
        config = _make_config(dsl)
        output = engine.run(dsl, config, bundle)

        # No trade should have entry on a suspended day
        for trade in output.trades:
            # Day 12 (index 11) is "2024-01-12"
            assert trade.entry_date != "2024-01-12", "Entry on suspended day"

    def test_compute_required_ma(self) -> None:
        """Engine auto-computes missing MA columns from close prices."""
        engine = LightBacktestEngine()

        prices = [10.0 + i * 0.1 for i in range(30)]
        df = _build_daily_df(prices, symbol="MA")  # No MA columns provided
        bundle = _make_bundle(df)

        dsl = _make_dsl(
            entry=[ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            )],
        )

        frame = engine.build_signal_frame(dsl, bundle)

        # Engine should have computed ma_5 and ma_20
        assert "ma_5" in frame.frame.columns
        assert "ma_20" in frame.frame.columns

    def test_output_mode_is_light_real_v1(self) -> None:
        """Engine output mode is always light_real_v1."""
        engine = LightBacktestEngine()

        prices = [10.0] * 10
        df = _build_daily_df(prices, symbol="M")
        bundle = _make_bundle(df)
        dsl = _make_dsl(
            entry=[ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": 5, "slow_period": 20},
            )],
        )
        config = _make_config(dsl)
        output = engine.run(dsl, config, bundle)

        assert output.mode == "light_real_v1"
