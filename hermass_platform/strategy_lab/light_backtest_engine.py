"""Light Backtest Engine - Polars-based deterministic backtest execution.

This module is the hot path for Phase 2 Light Backtest v1. It uses Polars
for vectorized signal computation and row-by-row position/trade generation.

Architecture:
    1. build_signal_frame() - vectorized Polars signal computation
    2. _generate_trades() - row-by-row position and trade logic
    3. _compute_equity() - portfolio value and daily return curve
    4. run() - orchestrate all phases and return LightBacktestOutput

Design constraints:
    - DSL is the only strategy expression.
    - No LLM-generated or Python strategy code execution.
    - Long-only daily-bar backtest.
    - Deterministic: same input always produces same output.
"""

from __future__ import annotations

import time
from typing import Any

import polars as pl

from .backtest_adapter import BacktestConfig, CostModel
from .backtest_models import (
    EquityPoint,
    LightBacktestOutput,
    MarketDataBundle,
    SignalFrame,
    TradeSummary,
)
from .condition_registry import ConditionRegistry
from .dsl_schema import ConditionBlock, StrategyDSL


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class LightBacktestEngine:
    """Deterministic Polars-based Light Backtest engine.

    Args:
        registry: ConditionRegistry for parameter validation.
        cost_model: CostModel for transaction costs. Defaults to A-share.
    """

    def __init__(
        self,
        registry: ConditionRegistry | None = None,
        cost_model: CostModel | None = None,
    ) -> None:
        self.registry = registry or ConditionRegistry.default()
        self.cost_model = cost_model or CostModel()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        dsl: StrategyDSL,
        config: BacktestConfig,
        data: MarketDataBundle,
    ) -> LightBacktestOutput:
        """Run a complete Light Backtest.

        Steps:
            1. Compute signals (Polars vectorized).
            2. Generate positions and trades (row-by-row).
            3. Compute equity curve.
            4. Compute metrics.
            5. Return LightBacktestOutput.
        """
        t0 = time.time()
        warnings: list[str] = list(data.warnings)

        # Step 1: Signal frame
        signal_frame = self.build_signal_frame(dsl, data)
        warnings.extend(signal_frame.warnings)

        if signal_frame.frame.is_empty():
            return LightBacktestOutput(
                mode="light_real_v1",
                status="failed",
                warnings=warnings + ["BT_EMPTY_SIGNAL_FRAME"],
                data_version=data.data_version,
                elapsed_seconds=time.time() - t0,
            )

        # Step 2: Generate trades
        completed_frame, trades = self._generate_trades(
            signal_frame.frame, dsl, config
        )

        # Step 3: Equity curve
        daily_curve = self._compute_equity(completed_frame, config.initial_capital)

        # Step 4: Metrics
        trades_df = self._trades_to_dataframe(trades)
        from .backtest_metrics import compute_light_metrics

        metrics = compute_light_metrics(daily_curve, trades_df, config.initial_capital)

        # Step 5: Build output
        equity_points = [
            EquityPoint(
                date=str(row["date"]),
                portfolio_value=row["portfolio_value"],
                daily_return=row["daily_return"],
            )
            for row in daily_curve.to_dicts()
        ]

        elapsed = time.time() - t0
        status = "success" if trades else "partial"
        if not trades:
            warnings.append("BT_NO_TRADES_GENERATED")

        return LightBacktestOutput(
            mode="light_real_v1",
            status=status,
            metrics=metrics,
            trades=trades,
            daily_curve=equity_points,
            signal_frame=completed_frame,
            warnings=warnings,
            data_version=data.data_version,
            elapsed_seconds=elapsed,
        )

    def build_signal_frame(
        self,
        dsl: StrategyDSL,
        data: MarketDataBundle,
    ) -> SignalFrame:
        """Compute entry/exit/filter signals using Polars vectorized ops.

        Returns a SignalFrame with per-symbol per-date boolean signal columns.
        """
        warnings: list[str] = []
        df = data.bars.clone()

        # Ensure sorted by date, then symbol for correct multi-symbol
        # portfolio valuation and daily return semantics.
        df = df.sort(["date", "symbol"])

        # Compute MA columns needed by DSL conditions
        df = self._compute_required_ma(df, dsl)

        # Initialize signal columns
        df = df.with_columns([
            pl.lit(False).alias("entry_signal"),
            pl.lit(True).alias("filter_pass"),
            pl.lit(False).alias("raw_exit_signal"),
            pl.lit(False).alias("stop_loss_signal"),
            pl.lit(False).alias("take_profit_signal"),
        ])

        # Compute entry signals
        entry_mask = self._compute_section_signals(dsl.entry, df, "entry")
        if entry_mask is not None:
            df = df.with_columns(entry_mask.alias("entry_signal"))

        # Compute filter signals
        filter_mask = self._compute_section_signals(dsl.filters, df, "filters")
        if filter_mask is not None:
            df = df.with_columns(filter_mask.alias("filter_pass"))

        # Compute exit signals (excluding stop_loss/take_profit which need position context)
        exit_conditions = [
            c for c in dsl.exit
            if c.condition_type not in ("stop_loss_pct", "take_profit_pct")
        ]
        exit_mask = self._compute_section_signals(exit_conditions, df, "exit")
        if exit_mask is not None:
            df = df.with_columns(exit_mask.alias("raw_exit_signal"))

        # Compute stop_loss and take_profit signals (these are placeholder;
        # actual trigger requires position context in _generate_trades)
        df = df.with_columns([
            pl.lit(False).alias("stop_loss_signal"),
            pl.lit(False).alias("take_profit_signal"),
        ])

        # Mark required columns
        required = [
            "symbol", "date", "open", "high", "low", "close",
            "entry_signal", "filter_pass", "raw_exit_signal",
            "stop_loss_signal", "take_profit_signal",
        ]

        return SignalFrame(
            frame=df,
            required_columns=required,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Signal Computation
    # ------------------------------------------------------------------

    def _compute_section_signals(
        self,
        conditions: list[ConditionBlock],
        df: pl.DataFrame,
        section: str,
    ) -> pl.Expr | None:
        """Compute combined boolean signal for a DSL section.

        Conditions are combined using their ``logic`` field:
        - First condition is the base.
        - Subsequent conditions use ``and`` (&) or ``or`` (|).
        """
        if not conditions:
            return None

        combined: pl.Expr | None = None

        for i, cond in enumerate(conditions):
            signal_expr = self._compute_condition_signal(cond, df, section)
            if signal_expr is None:
                continue

            if combined is None:
                combined = signal_expr
            else:
                if cond.logic == "or":
                    combined = combined | signal_expr
                else:
                    combined = combined & signal_expr

        return combined

    def _compute_condition_signal(
        self,
        cond: ConditionBlock,
        df: pl.DataFrame,
        section: str,
    ) -> pl.Expr | None:
        """Compute signal expression for a single condition.

        Returns None if the condition cannot be computed (missing columns).
        """
        ct = cond.condition_type
        params = cond.params

        if ct == "ma_golden_cross":
            return self._signal_ma_golden_cross(df, params)
        elif ct == "ma_death_cross":
            return self._signal_ma_death_cross(df, params)
        elif ct == "price_cross_ma":
            return self._signal_price_cross_ma(df, params)
        elif ct == "stop_loss_pct":
            # Requires position context; handled in _generate_trades
            return None
        elif ct == "take_profit_pct":
            return None
        elif ct == "state_hex_in":
            return self._signal_state_hex_in(df, params)
        elif ct == "volume_ratio":
            return self._signal_volume_ratio(df, params)
        elif ct == "limit_up_filter":
            return self._signal_limit_up_filter(df, params)
        elif ct == "state_ef_count":
            return self._signal_state_ef_count(df, params)
        else:
            return None

    def _signal_ma_golden_cross(
        self, df: pl.DataFrame, params: dict[str, Any]
    ) -> pl.Expr:
        """ma_fast[t] > ma_slow[t] AND ma_fast[t-1] <= ma_slow[t-1]"""
        fast = params["fast_period"]
        slow = params["slow_period"]
        fast_col = f"ma_{fast}"
        slow_col = f"ma_{slow}"

        # Ensure columns exist
        if fast_col not in df.columns or slow_col not in df.columns:
            return pl.lit(False)

        curr_cross = pl.col(fast_col) > pl.col(slow_col)
        prev_fast = pl.col(fast_col).shift(1).over("symbol")
        prev_slow = pl.col(slow_col).shift(1).over("symbol")
        prev_not_cross = (prev_fast <= prev_slow).fill_null(False)

        return curr_cross & prev_not_cross

    def _signal_ma_death_cross(
        self, df: pl.DataFrame, params: dict[str, Any]
    ) -> pl.Expr:
        """ma_fast[t] < ma_slow[t] AND ma_fast[t-1] >= ma_slow[t-1]"""
        fast = params["fast_period"]
        slow = params["slow_period"]
        fast_col = f"ma_{fast}"
        slow_col = f"ma_{slow}"

        if fast_col not in df.columns or slow_col not in df.columns:
            return pl.lit(False)

        curr_cross = pl.col(fast_col) < pl.col(slow_col)
        prev_fast = pl.col(fast_col).shift(1).over("symbol")
        prev_slow = pl.col(slow_col).shift(1).over("symbol")
        prev_not_cross = (prev_fast >= prev_slow).fill_null(False)

        return curr_cross & prev_not_cross

    def _signal_price_cross_ma(
        self, df: pl.DataFrame, params: dict[str, Any]
    ) -> pl.Expr:
        """Price crosses MA (above or below)."""
        timeframe = params.get("timeframe", "D1")
        ma_period = params["ma_period"]
        direction = params["direction"]

        # Phase 2 only supports D1
        if timeframe != "D1":
            return pl.lit(False)

        ma_col = f"ma_{ma_period}"
        if ma_col not in df.columns:
            # Try alternate naming
            ma_col_alt = f"ma_{ma_period}_d1"
            if ma_col_alt in df.columns:
                ma_col = ma_col_alt
            else:
                return pl.lit(False)

        close_col = "close"
        prev_close = pl.col(close_col).shift(1).over("symbol")
        prev_ma = pl.col(ma_col).shift(1).over("symbol")

        if direction == "above":
            return (pl.col(close_col) > pl.col(ma_col)) & (
                (prev_close <= prev_ma).fill_null(False)
            )
        else:  # below
            return (pl.col(close_col) < pl.col(ma_col)) & (
                (prev_close >= prev_ma).fill_null(False)
            )

    def _signal_state_hex_in(
        self, df: pl.DataFrame, params: dict[str, Any]
    ) -> pl.Expr:
        """State hex value is in allowed set."""
        timeframe = params["timeframe"]
        values = params["values"]

        # Try normalized column name first, then source name
        for col_name in [
            f"{timeframe.lower()}_state",
            f"state_hex_{timeframe.lower()}",
        ]:
            if col_name in df.columns:
                return pl.col(col_name).is_in(values)

        return pl.lit(False)

    def _signal_volume_ratio(
        self, df: pl.DataFrame, params: dict[str, Any]
    ) -> pl.Expr:
        """Volume ratio comparison."""
        lookback = params["lookback"]
        operator = params["operator"]
        value = params["value"]

        # Prefer pre-computed volume_ratio column
        if "volume_ratio" in df.columns:
            ratio_col = "volume_ratio"
        elif f"volume_ma_{lookback}" in df.columns:
            ma_col = f"volume_ma_{lookback}"
            ratio_expr = pl.col("volume") / pl.col(ma_col).replace(0, None)
            return self._apply_operator(ratio_expr, operator, value)
        else:
            return pl.lit(False)

        return self._apply_operator(pl.col(ratio_col), operator, value)

    def _signal_limit_up_filter(
        self, df: pl.DataFrame, params: dict[str, Any]
    ) -> pl.Expr:
        """Limit-up filter. allow=false means exclude limit-up stocks."""
        allow = params["allow"]

        if "is_limit_up" not in df.columns:
            return pl.lit(False)

        if allow:
            return pl.col("is_limit_up") == True
        else:
            return pl.col("is_limit_up") == False

    def _signal_state_ef_count(
        self, df: pl.DataFrame, params: dict[str, Any]
    ) -> pl.Expr:
        """EF count comparison."""
        operator = params["operator"]
        value = params["value"]

        if "ef_count" not in df.columns:
            return pl.lit(False)

        return self._apply_operator(pl.col("ef_count"), operator, value)

    # ------------------------------------------------------------------
    # Trade Generation (row-by-row for position context)
    # ------------------------------------------------------------------

    def _generate_trades(
        self,
        df: pl.DataFrame,
        dsl: StrategyDSL,
        config: BacktestConfig,
    ) -> tuple[pl.DataFrame, list[TradeSummary]]:
        """Generate positions and trades using row-by-row iteration.

        This handles position context (entry_price, holding state),
        same-day conflict rules, and cost computation.

        Returns:
            (completed_frame, trades) where completed_frame has
            additional columns: position, entry_price, shares, trade_id,
            daily_return, portfolio_value, exit_date, exit_price, pnl, pnl_pct.
        """
        rows = df.to_dicts()
        n = len(rows)

        # Position tracking per symbol
        positions: dict[str, dict[str, Any]] = {}  # symbol -> position info
        trades: list[TradeSummary] = []
        trade_seq = 0

        # Portfolio tracking
        cash = config.initial_capital
        portfolio_values: list[float] = []
        daily_returns: list[float] = []
        prev_portfolio = config.initial_capital

        # Track which symbols exited today to prevent re-entry
        exited_today: set[str] = set()
        current_date: str | None = None

        # Extract stop_loss and take_profit values from DSL
        stop_loss_value: float | None = None
        take_profit_value: float | None = None
        for cond in dsl.exit:
            if cond.condition_type == "stop_loss_pct":
                stop_loss_value = cond.params.get("value")
            elif cond.condition_type == "take_profit_pct":
                take_profit_value = cond.params.get("value")

        max_position_pct = dsl.risk.max_position_pct

        for i, row in enumerate(rows):
            symbol = row["symbol"]
            date_str = str(row["date"])[:10]
            close = row.get("close")

            if close is None or close <= 0:
                portfolio_values.append(prev_portfolio)
                daily_returns.append(0.0)
                row["position"] = symbol in positions
                row["entry_price"] = positions.get(symbol, {}).get("entry_price")
                row["shares"] = positions.get(symbol, {}).get("shares", 0)
                row["trade_id"] = positions.get(symbol, {}).get("trade_id", "")
                row["exit_date"] = None
                row["exit_price"] = None
                row["pnl"] = None
                row["pnl_pct"] = None
                row["exit_reason"] = ""
                row["daily_return"] = 0.0
                row["portfolio_value"] = prev_portfolio
                continue

            # Reset exited_today when date changes
            if date_str != current_date:
                exited_today = set()
                current_date = date_str

            # Initialize row output fields
            row["exit_date"] = None
            row["exit_price"] = None
            row["pnl"] = None
            row["pnl_pct"] = None
            row["exit_reason"] = ""

            # Check tradability
            is_suspended = row.get("is_suspended", False)
            is_limit_up = row.get("is_limit_up", False)
            is_limit_down = row.get("is_limit_down", False)

            holding = symbol in positions

            # ----------------------------------------------------------
            # EXIT processing (before entry, if holding)
            # ----------------------------------------------------------
            if holding and not is_suspended:
                pos = positions[symbol]
                entry_price = pos["entry_price"]

                # Compute exit signals with position context
                stop_triggered = False
                take_triggered = False
                raw_exit = row.get("raw_exit_signal", False)

                if stop_loss_value is not None:
                    stop_triggered = close <= entry_price * (1 - stop_loss_value)
                    row["stop_loss_signal"] = stop_triggered

                if take_profit_value is not None:
                    take_triggered = close >= entry_price * (1 + take_profit_value)
                    row["take_profit_signal"] = take_triggered

                # Priority: stop_loss > take_profit > price_cross_ma > ma_death_cross
                exit_reason = ""
                should_exit = False

                if stop_triggered:
                    should_exit = True
                    exit_reason = "stop_loss_pct"
                elif take_triggered:
                    should_exit = True
                    exit_reason = "take_profit_pct"
                elif raw_exit:
                    should_exit = True
                    exit_reason = row.get("exit_reason_hint", "price_cross_ma")

                if should_exit:
                    # Check limit_down blocks sell
                    if is_limit_down:
                        row["exit_reason"] = ""
                        row["blocked_exit_reason"] = f"limit_down_blocked_{exit_reason}"
                    else:
                        # Execute exit
                        shares = pos["shares"]
                        sell_price = close * (1 - self.cost_model.slippage_rate)
                        sell_costs = self.cost_model.calculate_cost(
                            sell_price, shares, "sell"
                        )

                        pnl = (sell_price - entry_price) * shares - sell_costs["total"] - pos.get("entry_cost_total", 0)
                        notional_entry = entry_price * shares
                        pnl_pct = pnl / notional_entry if notional_entry > 0 else 0.0

                        trade_id = pos["trade_id"]
                        row["exit_date"] = date_str
                        row["exit_price"] = sell_price
                        row["pnl"] = pnl
                        row["pnl_pct"] = pnl_pct
                        row["exit_reason"] = exit_reason
                        row["trade_id"] = trade_id

                        cash += sell_price * shares - sell_costs["total"]

                        trades.append(TradeSummary(
                            trade_id=trade_id,
                            symbol=symbol,
                            side="long",
                            entry_date=pos["entry_date"],
                            entry_price=entry_price,
                            exit_date=date_str,
                            exit_price=sell_price,
                            shares=shares,
                            pnl=pnl,
                            pnl_pct=pnl_pct,
                            exit_reason=exit_reason,
                            entry_cost=pos.get("entry_cost_total", 0),
                            exit_cost=sell_costs["total"],
                            total_cost=pos.get("entry_cost_total", 0) + sell_costs["total"],
                        ))

                        del positions[symbol]
                        exited_today.add(symbol)
                        holding = False

            # ----------------------------------------------------------
            # ENTRY processing (if not holding and not exited today)
            # ----------------------------------------------------------
            if not holding and symbol not in exited_today and not is_suspended:
                entry_signal = row.get("entry_signal", False)
                filter_pass = row.get("filter_pass", True)

                # Limit-up filter check
                if is_limit_up and not filter_pass:
                    entry_signal = False
                elif is_limit_up:
                    # Check DSL filters
                    for fc in dsl.filters:
                        if fc.condition_type == "limit_up_filter":
                            if not fc.params.get("allow", False):
                                entry_signal = False
                                break

                if entry_signal and filter_pass:
                    # Compute position size
                    portfolio_val = prev_portfolio
                    target_notional = portfolio_val * max_position_pct
                    buy_price = close * (1 + self.cost_model.slippage_rate)
                    shares = int(target_notional / buy_price / 100) * 100

                    if shares <= 0:
                        row["position"] = False
                        row["entry_price"] = None
                        row["shares"] = 0
                        row["trade_id"] = ""
                    else:
                        buy_costs = self.cost_model.calculate_cost(
                            buy_price, shares, "buy"
                        )
                        total_buy_cost = buy_price * shares + buy_costs["total"]

                        if total_buy_cost > cash:
                            # Insufficient cash
                            row["position"] = False
                            row["entry_price"] = None
                            row["shares"] = 0
                            row["trade_id"] = ""
                        else:
                            trade_seq += 1
                            trade_id = f"{config.trace_id or 'bt'}:{symbol}:{date_str}:{trade_seq}"

                            cash -= total_buy_cost
                            positions[symbol] = {
                                "entry_date": date_str,
                                "entry_price": buy_price,
                                "shares": shares,
                                "trade_id": trade_id,
                                "entry_cost_total": buy_costs["total"],
                            }

                            row["position"] = True
                            row["entry_price"] = buy_price
                            row["shares"] = shares
                            row["trade_id"] = trade_id
                            row["entry_date"] = date_str
                            holding = True

            # Update row position fields
            if holding or symbol in positions:
                pos = positions.get(symbol, {})
                row["position"] = True
                row["entry_price"] = pos.get("entry_price")
                row["shares"] = pos.get("shares", 0)
                row["trade_id"] = pos.get("trade_id", "")
                if "entry_date" not in row or not row.get("entry_date"):
                    row["entry_date"] = pos.get("entry_date", "")
            else:
                row["position"] = False
                if not row.get("entry_price"):
                    row["entry_price"] = None
                row["shares"] = 0
                if not row.get("trade_id"):
                    row["trade_id"] = ""

            # Portfolio value: cash + sum of position market values
            position_value = 0.0
            for sym, pos in positions.items():
                # Use current close for the current symbol, or find close for others
                if sym == symbol:
                    position_value += close * pos["shares"]
                else:
                    # Approximate with last known close
                    position_value += pos.get("last_close", pos["entry_price"]) * pos["shares"]

            # Update last_close for this symbol
            if symbol in positions:
                positions[symbol]["last_close"] = close

            portfolio_val = cash + position_value
            portfolio_values.append(portfolio_val)
            daily_ret = (portfolio_val - prev_portfolio) / prev_portfolio if prev_portfolio > 0 else 0.0
            daily_returns.append(daily_ret)
            prev_portfolio = portfolio_val

        # Add computed columns back to df
        df = df.with_columns([
            pl.Series("portfolio_value", portfolio_values),
            pl.Series("daily_return", daily_returns),
        ])

        # Add other columns that were set during iteration
        for col_name in ["position", "entry_price", "shares", "trade_id",
                         "exit_date", "exit_price", "pnl", "pnl_pct",
                         "exit_reason", "entry_date"]:
            values = [row.get(col_name) for row in rows]
            if all(v is None for v in values):
                continue
            try:
                df = df.with_columns(pl.Series(col_name, values))
            except Exception:
                pass

        return df, trades

    # ------------------------------------------------------------------
    # Equity Curve
    # ------------------------------------------------------------------

    def _compute_equity(
        self,
        df: pl.DataFrame,
        initial_capital: float,
    ) -> pl.DataFrame:
        """Extract daily equity curve, deduped by date.

        Returns DataFrame with columns: date, portfolio_value, daily_return.
        """
        if "portfolio_value" not in df.columns:
            return pl.DataFrame(
                schema={"date": pl.Utf8, "portfolio_value": pl.Float64, "daily_return": pl.Float64}
            )

        # Get last row per date for portfolio value
        equity = (
            df.sort(["date", "symbol"])
            .group_by("date")
            .last()
            .sort("date")
            .select(["date", "portfolio_value", "daily_return"])
        )

        # Ensure date is string
        if equity["date"].dtype == pl.Date:
            equity = equity.with_columns(
                pl.col("date").cast(pl.Utf8)
            )

        return equity

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _compute_required_ma(
        self, df: pl.DataFrame, dsl: StrategyDSL
    ) -> pl.DataFrame:
        """Compute any MA columns needed by DSL conditions but not in data."""
        needed_periods: set[int] = set()

        for cond in dsl.get_all_conditions():
            ct = cond.condition_type
            params = cond.params

            if ct in ("ma_golden_cross", "ma_death_cross"):
                needed_periods.add(params.get("fast_period", 0))
                needed_periods.add(params.get("slow_period", 0))
            elif ct == "price_cross_ma":
                needed_periods.add(params.get("ma_period", 0))

        for period in needed_periods:
            if period <= 0:
                continue
            col = f"ma_{period}"
            if col not in df.columns and "close" in df.columns:
                df = df.with_columns(
                    pl.col("close")
                    .rolling_mean(window_size=period)
                    .over("symbol")
                    .alias(col)
                )

        return df

    @staticmethod
    def _apply_operator(
        expr: pl.Expr, operator: str, value: float
    ) -> pl.Expr:
        """Apply comparison operator to expression."""
        ops = {
            ">": lambda e, v: e > v,
            "<": lambda e, v: e < v,
            ">=": lambda e, v: e >= v,
            "<=": lambda e, v: e <= v,
            "==": lambda e, v: e == v,
            "!=": lambda e, v: e != v,
        }
        fn = ops.get(operator)
        if fn is None:
            return pl.lit(False)
        return fn(expr, value)

    @staticmethod
    def _trades_to_dataframe(trades: list[TradeSummary]) -> pl.DataFrame:
        """Convert trade list to Polars DataFrame for metrics computation."""
        if not trades:
            return pl.DataFrame(
                schema={
                    "pnl": pl.Float64,
                    "pnl_pct": pl.Float64,
                    "entry_date": pl.Utf8,
                    "exit_date": pl.Utf8,
                    "shares": pl.Int64,
                    "entry_price": pl.Float64,
                    "total_cost": pl.Float64,
                }
            )

        return pl.DataFrame([
            {
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct,
                "entry_date": t.entry_date,
                "exit_date": t.exit_date,
                "shares": t.shares,
                "entry_price": t.entry_price,
                "total_cost": t.total_cost,
            }
            for t in trades
        ])
