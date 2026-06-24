"""Multi-timeframe and Multi-period Backtest Engine.

Supports:
    - Multi-timeframe analysis: Run strategy across D1/W1/MN1 simultaneously
    - Multi-period backtest: Run strategy across multiple date ranges and aggregate results
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .backtest_adapter import BacktestAdapter, BacktestConfig, BacktestResult, CostModel
from .dsl_schema import StrategyDSL


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class TimeframeResult:
    """Result for a single timeframe analysis."""

    timeframe: str
    result: BacktestResult
    signal_count: int = 0
    agreement_rate: float = 0.0  # Agreement with primary timeframe


@dataclass
class PeriodResult:
    """Result for a single backtest period."""

    period_label: str
    start_date: str
    end_date: str
    result: BacktestResult
    status: str = "success"  # success, partial, failed


@dataclass
class MultiTimeframeBacktestResult:
    """Aggregated result from multi-timeframe backtest."""

    primary_timeframe: str
    timeframe_results: list[TimeframeResult] = field(default_factory=list)
    overall_metrics: dict[str, float] = field(default_factory=dict)
    cross_timeframe_signals: list[dict[str, Any]] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    status: str = "success"
    warnings: list[str] = field(default_factory=list)


@dataclass
class MultiPeriodBacktestResult:
    """Aggregated result from multi-period backtest."""

    period_results: list[PeriodResult] = field(default_factory=list)
    overall_metrics: dict[str, float] = field(default_factory=dict)
    period_comparison: dict[str, Any] = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    status: str = "success"
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Multi-timeframe Engine
# ---------------------------------------------------------------------------

class MultiTimeframeEngine:
    """Engine for running backtests across multiple timeframes simultaneously.

    Usage:
        engine = MultiTimeframeEngine(adapter)
        result = engine.run(dsl, start_date, end_date)
    """

    def __init__(self, adapter: BacktestAdapter) -> None:
        self.adapter = adapter

    def run(
        self,
        dsl: StrategyDSL,
        start_date: str,
        end_date: str,
        initial_capital: float = 1_000_000.0,
    ) -> MultiTimeframeBacktestResult:
        """Run multi-timeframe backtest.

        Steps:
            1. Run backtest on primary timeframe
            2. Run backtest on each secondary timeframe
            3. Calculate cross-timeframe agreement
            4. Aggregate metrics
        """
        start_time = time.time()
        tf_config = dsl.multi_timeframe
        timeframes = tf_config.timeframes
        primary = tf_config.primary_timeframe

        if primary not in timeframes:
            timeframes = [primary] + [t for t in timeframes if t != primary]

        results: list[TimeframeResult] = []
        warnings: list[str] = []

        # Run backtest for each timeframe
        for tf in timeframes:
            # Create timeframe-specific DSL copy
            tf_dsl = self._create_timeframe_dsl(dsl, tf)

            config = self.adapter.create_config(
                dsl=tf_dsl,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
            )

            result = self.adapter.run_backtest(config)

            signal_count = len(result.trades) if result.trades else 0
            tf_result = TimeframeResult(
                timeframe=tf,
                result=result,
                signal_count=signal_count,
            )
            results.append(tf_result)

            if result.status != "success":
                warnings.append(f"Timeframe {tf}: backtest status = {result.status}")

        # Calculate cross-timeframe agreement
        primary_result = next((r for r in results if r.timeframe == primary), None)
        if primary_result and len(results) > 1:
            for r in results:
                if r.timeframe != primary:
                    r.agreement_rate = self._calculate_agreement(
                        primary_result.result, r.result
                    )

        # Aggregate metrics
        overall_metrics = self._aggregate_timeframe_metrics(results)

        # Cross-timeframe signals (signals that appear in multiple timeframes)
        cross_signals = self._find_cross_timeframe_signals(results)

        elapsed = time.time() - start_time

        status = "success"
        if any(r.result.status == "failed" for r in results):
            status = "partial" if any(r.result.status == "success" for r in results) else "failed"

        return MultiTimeframeBacktestResult(
            primary_timeframe=primary,
            timeframe_results=results,
            overall_metrics=overall_metrics,
            cross_timeframe_signals=cross_signals,
            elapsed_seconds=elapsed,
            status=status,
            warnings=warnings,
        )

    def _create_timeframe_dsl(self, dsl: StrategyDSL, timeframe: str) -> StrategyDSL:
        """Create a DSL copy with timeframe-specific parameters."""
        # Deep copy DSL
        dsl_dict = dsl.model_dump()

        # Update condition params with timeframe
        for section in ["entry", "exit", "filters"]:
            for cond in dsl_dict.get(section, []):
                if "timeframe" in cond.get("params", {}):
                    cond["params"]["timeframe"] = timeframe

        # Update multi_timeframe config
        dsl_dict["multi_timeframe"]["primary_timeframe"] = timeframe
        dsl_dict["multi_timeframe"]["timeframes"] = [timeframe]

        return StrategyDSL.model_validate(dsl_dict)

    def _calculate_agreement(
        self, primary: BacktestResult, secondary: BacktestResult
    ) -> float:
        """Calculate signal agreement rate between two timeframes."""
        primary_dates = {t.get("entry_date", "") for t in primary.trades}
        secondary_dates = {t.get("entry_date", "") for t in secondary.trades}

        if not primary_dates or not secondary_dates:
            return 0.0

        agreement = len(primary_dates & secondary_dates)
        total = len(primary_dates)
        return agreement / total if total > 0 else 0.0

    def _aggregate_timeframe_metrics(
        self, results: list[TimeframeResult]
    ) -> dict[str, float]:
        """Aggregate metrics across timeframes."""
        if not results:
            return {}

        aggregated: dict[str, float] = {}
        metric_keys = ["total_return", "annual_return", "max_drawdown", "sharpe_ratio",
                      "win_rate", "profit_factor", "trade_count"]

        for key in metric_keys:
            values = [r.result.metrics.get(key, 0.0) for r in results if r.result.metrics]
            if values:
                aggregated[f"avg_{key}"] = sum(values) / len(values)
                aggregated[f"min_{key}"] = min(values)
                aggregated[f"max_{key}"] = max(values)

        # Primary timeframe metrics (most important)
        primary = next((r for r in results if r.timeframe == results[0].timeframe), None)
        if primary and primary.result.metrics:
            for key, value in primary.result.metrics.items():
                aggregated[f"primary_{key}"] = value

        return aggregated

    def _find_cross_timeframe_signals(
        self, results: list[TimeframeResult]
    ) -> list[dict[str, Any]]:
        """Find signals that appear in multiple timeframes."""
        if len(results) < 2:
            return []

        # Collect signals by date across all timeframes
        date_signals: dict[str, dict[str, Any]] = {}
        for r in results:
            for trade in r.result.trades:
                date = trade.get("entry_date", "")
                if date not in date_signals:
                    date_signals[date] = {"date": date, "timeframes": [], "symbols": set()}
                date_signals[date]["timeframes"].append(r.timeframe)
                date_signals[date]["symbols"].add(trade.get("symbol", ""))

        # Find dates with signals in multiple timeframes
        cross_signals = []
        for date, info in date_signals.items():
            if len(set(info["timeframes"])) >= 2:
                cross_signals.append({
                    "date": date,
                    "timeframes": list(set(info["timeframes"])),
                    "symbols": list(info["symbols"]),
                    "timeframe_count": len(set(info["timeframes"])),
                })

        return sorted(cross_signals, key=lambda x: x["date"])


# ---------------------------------------------------------------------------
# Multi-period Engine
# ---------------------------------------------------------------------------

class MultiPeriodEngine:
    """Engine for running backtests across multiple time periods.

    Usage:
        engine = MultiPeriodEngine(adapter)
        result = engine.run(dsl)
    """

    def __init__(self, adapter: BacktestAdapter) -> None:
        self.adapter = adapter

    def run(
        self,
        dsl: StrategyDSL,
        initial_capital: float = 1_000_000.0,
    ) -> MultiPeriodBacktestResult:
        """Run multi-period backtest.

        Steps:
            1. Run backtest for each configured period
            2. Aggregate results based on aggregate_method
            3. Generate period comparison analysis
        """
        start_time = time.time()
        mp_config = dsl.multi_period
        periods = mp_config.periods

        if not periods:
            # Fallback: use single period from backtest config
            return MultiPeriodBacktestResult(
                status="failed",
                warnings=["No periods configured in multi_period config"],
            )

        period_results: list[PeriodResult] = []
        warnings: list[str] = []
        success_count = 0

        for period in periods:
            config = self.adapter.create_config(
                dsl=dsl,
                start_date=period.start_date,
                end_date=period.end_date,
                initial_capital=initial_capital,
            )

            result = self.adapter.run_backtest(config)

            status = "success" if result.status == "success" else "failed"
            if status == "success":
                success_count += 1

            period_results.append(PeriodResult(
                period_label=period.label or f"{period.start_date} to {period.end_date}",
                start_date=period.start_date,
                end_date=period.end_date,
                result=result,
                status=status,
            ))

            if result.status != "success":
                warnings.append(
                    f"Period {period.label}: backtest failed - {result.warnings}"
                )

        # Check minimum periods requirement
        if success_count < mp_config.min_periods_required:
            return MultiPeriodBacktestResult(
                period_results=period_results,
                status="failed",
                warnings=warnings + [
                    f"Only {success_count}/{len(periods)} periods succeeded, "
                    f"minimum required: {mp_config.min_periods_required}"
                ],
            )

        # Aggregate results
        overall_metrics = self._aggregate_period_metrics(
            period_results, mp_config.aggregate_method
        )

        # Period comparison
        period_comparison = self._compare_periods(period_results)

        elapsed = time.time() - start_time

        status = "success" if success_count == len(periods) else "partial"

        return MultiPeriodBacktestResult(
            period_results=period_results,
            overall_metrics=overall_metrics,
            period_comparison=period_comparison,
            elapsed_seconds=elapsed,
            status=status,
            warnings=warnings,
        )

    def _aggregate_period_metrics(
        self,
        period_results: list[PeriodResult],
        method: str,
    ) -> dict[str, float]:
        """Aggregate metrics across periods using specified method."""
        successful = [p for p in period_results if p.status == "success" and p.result.metrics]
        if not successful:
            return {}

        metric_keys = ["total_return", "annual_return", "max_drawdown", "sharpe_ratio",
                      "win_rate", "profit_factor", "trade_count"]

        aggregated: dict[str, float] = {}

        for key in metric_keys:
            values = [p.result.metrics.get(key, 0.0) for p in successful]
            if not values:
                continue

            if method == "average":
                aggregated[key] = sum(values) / len(values)
            elif method == "weighted":
                # Weight by number of trades (more trades = more reliable)
                trade_counts = [p.result.metrics.get("trade_count", 1) for p in successful]
                total_trades = sum(trade_counts)
                if total_trades > 0:
                    aggregated[key] = sum(v * w for v, w in zip(values, trade_counts)) / total_trades
                else:
                    aggregated[key] = sum(values) / len(values)
            else:  # concat (default) - sum for counts, average for ratios
                if key in ["trade_count"]:
                    aggregated[key] = sum(values)
                else:
                    aggregated[key] = sum(values) / len(values)

        # Add consistency metrics
        if len(values) > 1:
            returns = [p.result.metrics.get("total_return", 0.0) for p in successful]
            if returns:
                avg_return = sum(returns) / len(returns)
                variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                aggregated["return_consistency"] = 1.0 / (1.0 + variance)  # Higher = more consistent

        # Period count
        aggregated["period_count"] = len(successful)
        aggregated["success_rate"] = len(successful) / len(period_results)

        return aggregated

    def _compare_periods(self, period_results: list[PeriodResult]) -> dict[str, Any]:
        """Generate period comparison analysis."""
        successful = [p for p in period_results if p.status == "success"]
        if not successful:
            return {}

        comparison = {
            "period_count": len(period_results),
            "success_count": len(successful),
            "failed_count": len(period_results) - len(successful),
        }

        # Best and worst periods
        returns = [(p.period_label, p.result.metrics.get("total_return", 0.0))
                   for p in successful if p.result.metrics]
        if returns:
            returns_sorted = sorted(returns, key=lambda x: x[1], reverse=True)
            comparison["best_period"] = returns_sorted[0][0]
            comparison["best_return"] = returns_sorted[0][1]
            comparison["worst_period"] = returns_sorted[-1][0]
            comparison["worst_return"] = returns_sorted[-1][1]

        # Drawdown comparison
        drawdowns = [(p.period_label, p.result.metrics.get("max_drawdown", 0.0))
                     for p in successful if p.result.metrics]
        if drawdowns:
            dd_sorted = sorted(drawdowns, key=lambda x: x[1])  # Lower is better
            comparison["safest_period"] = dd_sorted[0][0]
            comparison["safest_drawdown"] = dd_sorted[0][1]
            comparison["riskiest_period"] = dd_sorted[-1][0]
            comparison["riskiest_drawdown"] = dd_sorted[-1][1]

        # Period-by-period summary
        comparison["period_summaries"] = [
            {
                "label": p.period_label,
                "start_date": p.start_date,
                "end_date": p.end_date,
                "total_return": p.result.metrics.get("total_return", 0.0) if p.result.metrics else 0.0,
                "max_drawdown": p.result.metrics.get("max_drawdown", 0.0) if p.result.metrics else 0.0,
                "trade_count": len(p.result.trades) if p.result.trades else 0,
                "status": p.status,
            }
            for p in period_results
        ]

        return comparison


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def run_multi_timeframe_backtest(
    dsl: StrategyDSL,
    start_date: str,
    end_date: str,
    foundation_db: Path | None = None,
    initial_capital: float = 1_000_000.0,
) -> MultiTimeframeBacktestResult:
    """High-level function to run multi-timeframe backtest."""
    adapter = BacktestAdapter(foundation_db=foundation_db)
    engine = MultiTimeframeEngine(adapter)
    return engine.run(dsl, start_date, end_date, initial_capital)


def run_multi_period_backtest(
    dsl: StrategyDSL,
    foundation_db: Path | None = None,
    initial_capital: float = 1_000_000.0,
) -> MultiPeriodBacktestResult:
    """High-level function to run multi-period backtest."""
    adapter = BacktestAdapter(foundation_db=foundation_db)
    engine = MultiPeriodEngine(adapter)
    return engine.run(dsl, initial_capital)
