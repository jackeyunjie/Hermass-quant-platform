"""Backtest Adapter - DSL to BacktestConfig conversion and execution facade.

Phase 0: Stub implementation.
Phase 2: Facade that routes to LightBacktestEngine when foundation_db is
    provided, or falls back to stub for backwards-compatible tests.

This module provides:
    - CostModel: Trading cost definitions.
    - BacktestConfig: Extended configuration with state_cube_db, universe, trace_id.
    - BacktestResult: Extended result with mode, status, data_version, warnings.
    - BacktestAdapter: Facade for backtest execution.
    - run_dsl_backtest(): High-level convenience function.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .dsl_schema import StrategyDSL


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class CostModel:
    """Trading cost model for A-shares."""

    commission_rate: float = 0.0003  # 万三
    stamp_duty_rate: float = 0.0005  # 千五 (sell only)
    slippage_rate: float = 0.001  # 千一
    min_commission: float = 5.0  # minimum commission in RMB

    def calculate_cost(
        self,
        price: float,
        shares: int,
        side: str,  # "buy" or "sell"
    ) -> dict[str, float]:
        """Calculate trading costs for a single order.

        Returns:
            Dict with commission, stamp_duty, slippage, total.
        """
        notional = price * shares

        commission = max(notional * self.commission_rate, self.min_commission)
        stamp_duty = notional * self.stamp_duty_rate if side == "sell" else 0.0
        slippage = notional * self.slippage_rate

        return {
            "commission": commission,
            "stamp_duty": stamp_duty,
            "slippage": slippage,
            "total": commission + stamp_duty + slippage,
        }


@dataclass
class BacktestConfig:
    """Configuration for running a backtest."""

    dsl: StrategyDSL
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    initial_capital: float = 1_000_000.0
    cost_model: CostModel = field(default_factory=CostModel)
    mode: str = "light"  # "light" | "full"
    foundation_db: Path | None = None
    state_cube_db: Path | None = None
    universe: list[str] | None = None
    trace_id: str | None = None


@dataclass
class BacktestResult:
    """Result of a backtest run.

    Attributes:
        metrics: Core performance metrics.
        trades: List of individual trades.
        daily_curve: Daily portfolio value curve.
        state_breakdown: Performance by market state.
        walk_forward: Walk-forward validation results.
        risk_flags: List of risk warnings.
        report_path: Path to generated report.
        elapsed_seconds: Runtime duration.
        trace_id: Link to observability trace.
        mode: Execution mode ("light_real_v1" or "light_stub").
        status: Execution status ("success", "partial", "failed").
        data_version: Data freshness identifier.
        warnings: Data quality and execution warnings.
        trades_path: Optional path to persisted trades.
    """

    metrics: dict[str, float] = field(default_factory=dict)
    trades: list[dict[str, Any]] = field(default_factory=list)
    daily_curve: list[dict[str, Any]] = field(default_factory=list)
    state_breakdown: dict[str, Any] = field(default_factory=dict)
    walk_forward: dict[str, Any] = field(default_factory=dict)
    risk_flags: list[str] = field(default_factory=list)
    report_path: str = ""
    elapsed_seconds: float = 0.0
    trace_id: str | None = None
    mode: str = "light_stub"
    status: str = "success"
    data_version: str | None = None
    warnings: list[str] = field(default_factory=list)
    trades_path: str | None = None
    signal_frame: Any = None


# ---------------------------------------------------------------------------
# Adapter Facade
# ---------------------------------------------------------------------------

class BacktestAdapter:
    """Adapter from StrategyDSL to backtest execution.

    Phase 0: Stub implementation (returns zero metrics).
    Phase 2: Routes to LightBacktestEngine when foundation_db is provided.
    """

    def __init__(
        self,
        foundation_db: Path | None = None,
        state_cube_db: Path | None = None,
    ) -> None:
        self.foundation_db = foundation_db
        self.state_cube_db = state_cube_db

    def create_config(
        self,
        dsl: StrategyDSL,
        start_date: str,
        end_date: str,
        initial_capital: float = 1_000_000.0,
        mode: str = "light",
        universe: list[str] | None = None,
        trace_id: str | None = None,
    ) -> BacktestConfig:
        """Create a BacktestConfig from DSL."""
        return BacktestConfig(
            dsl=dsl,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            cost_model=CostModel(),
            mode=mode,
            foundation_db=self.foundation_db,
            state_cube_db=self.state_cube_db,
            universe=universe,
            trace_id=trace_id,
        )

    def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """Run a backtest.

        Phase 2: If foundation_db is provided and exists, routes to
        LightBacktestEngine for real light_real_v1 execution.
        Otherwise falls back to stub for backwards compatibility.
        """
        from .dsl_validator import validate_dsl

        validation = validate_dsl(config.dsl)
        if not validation.passed:
            return BacktestResult(
                metrics={},
                risk_flags=[f"BT_VALIDATION_FAILED: {e.code}" for e in validation.errors],
                elapsed_seconds=0.0,
                trace_id=config.trace_id,
                mode="light_real_v1" if config.foundation_db else "light_stub",
                status="failed",
                warnings=[e.message for e in validation.errors],
            )

        # Determine if we can run real backtest
        if config.foundation_db is not None:
            if not Path(config.foundation_db).exists():
                return BacktestResult(
                    metrics={},
                    risk_flags=[
                        "BT_DATA_DB_NOT_FOUND: foundation_db does not exist at "
                        f"{config.foundation_db}"
                    ],
                    mode="light_real_v1",
                    status="failed",
                    elapsed_seconds=0.0,
                    trace_id=config.trace_id,
                    warnings=[
                        f"Foundation DB not found: {config.foundation_db}"
                    ],
                )
            return self._run_real_backtest(config)
        else:
            return self._run_stub_backtest()

    def _run_real_backtest(self, config: BacktestConfig) -> BacktestResult:
        """Run real Light Backtest v1 via provider and engine."""
        from .backtest_data_provider import DuckDBBacktestDataProvider
        from .backtest_models import MarketDataRequest
        from .light_backtest_engine import LightBacktestEngine

        # Resolve required columns from DSL
        from .condition_registry import ConditionRegistry

        registry = ConditionRegistry.default()
        required_columns: list[str] = []
        for cond in config.dsl.get_all_conditions():
            try:
                spec = registry.get(cond.condition_type)
                cols = spec.resolve_required_columns(cond.params)
                required_columns.extend(cols)
            except KeyError:
                pass

        # Create provider and load data
        provider = DuckDBBacktestDataProvider(
            foundation_db=Path(config.foundation_db),
            state_cube_db=Path(config.state_cube_db) if config.state_cube_db else None,
        )

        try:
            request = MarketDataRequest(
                start_date=config.start_date,
                end_date=config.end_date,
                required_columns=list(set(required_columns)),
                universe=config.universe,
                include_state=True,
            )
            data = provider.load(request)
        except Exception as e:
            return BacktestResult(
                metrics={},
                risk_flags=[f"BT_DATA_LOAD_FAILED: {e}"],
                mode="light_real_v1",
                status="failed",
                warnings=[str(e)],
                elapsed_seconds=0.0,
            )

        # Run engine
        engine = LightBacktestEngine(
            registry=registry,
            cost_model=config.cost_model,
        )
        output = engine.run(config.dsl, config, data)

        # Convert to BacktestResult
        trades_dicts = [
            {
                "trade_id": t.trade_id,
                "symbol": t.symbol,
                "side": t.side,
                "entry_date": t.entry_date,
                "entry_price": t.entry_price,
                "exit_date": t.exit_date,
                "exit_price": t.exit_price,
                "shares": t.shares,
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct,
                "exit_reason": t.exit_reason,
                "entry_cost": t.entry_cost,
                "exit_cost": t.exit_cost,
                "total_cost": t.total_cost,
            }
            for t in output.trades
        ]

        daily_curve_dicts = [
            {"date": ep.date, "portfolio_value": ep.portfolio_value, "daily_return": ep.daily_return}
            for ep in output.daily_curve
        ]

        risk_flags: list[str] = []
        if not output.trades:
            risk_flags.append("BT_NO_TRADES")

        return BacktestResult(
            metrics=dict(output.metrics) if output.metrics else {},
            trades=trades_dicts,
            daily_curve=daily_curve_dicts,
            risk_flags=risk_flags,
            elapsed_seconds=output.elapsed_seconds,
            trace_id=config.trace_id,
            mode=output.mode,
            status=output.status,
            data_version=output.data_version,
            warnings=output.warnings,
            signal_frame=output.signal_frame,
        )

    def _run_stub_backtest(self) -> BacktestResult:
        """Return stub backtest result (Phase 0 compatibility)."""
        return BacktestResult(
            metrics={
                "total_return": 0.0,
                "annual_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "trade_count": 0,
            },
            risk_flags=["STUB_BACKTEST: Not yet implemented"],
            elapsed_seconds=0.001,
            mode="light_stub",
        )


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def run_dsl_backtest(
    dsl: StrategyDSL,
    start_date: str,
    end_date: str,
    foundation_db: Path | None = None,
    initial_capital: float = 1_000_000.0,
    cost_model: str = "a_share_default",
    mode: str = "light",
    state_cube_db: Path | None = None,
    universe: list[str] | None = None,
    trace_id: str | None = None,
) -> BacktestResult:
    """High-level function to run a backtest from DSL.

    Phase 2: Routes to real engine when foundation_db is provided.
    Phase 0: Falls back to stub when foundation_db is None.
    """
    adapter = BacktestAdapter(
        foundation_db=foundation_db,
        state_cube_db=state_cube_db,
    )
    config = adapter.create_config(
        dsl=dsl,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        mode=mode,
        universe=universe,
        trace_id=trace_id,
    )
    return adapter.run_backtest(config)
