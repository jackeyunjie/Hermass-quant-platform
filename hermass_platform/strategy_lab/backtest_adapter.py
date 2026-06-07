"""Backtest Adapter - DSL to BacktestConfig conversion.

STUB for Phase 0. Full implementation in Phase 2.

This module provides:
    - Interface definition for DSL -> BacktestConfig
    - Cost model definitions
    - Mock backtest result for testing
"""

from __future__ import annotations

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


# ---------------------------------------------------------------------------
# Adapter Interface
# ---------------------------------------------------------------------------

class BacktestAdapter:
    """Adapter from StrategyDSL to backtest execution.

    Phase 0: Interface definition only.
    Phase 2: Full implementation with DuckDB/Polars engine.
    """

    def __init__(self, foundation_db: Path | None = None) -> None:
        self.foundation_db = foundation_db

    def create_config(
        self,
        dsl: StrategyDSL,
        start_date: str,
        end_date: str,
        initial_capital: float = 1_000_000.0,
        mode: str = "light",
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
        )

    def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """Run a backtest.

        STUB for Phase 0. Returns a mock result.
        Phase 2: Full implementation.
        """
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
) -> BacktestResult:
    """High-level function to run a backtest from DSL.

    STUB for Phase 0.
    """
    adapter = BacktestAdapter(foundation_db=foundation_db)
    config = adapter.create_config(
        dsl=dsl,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        mode=mode,
    )
    return adapter.run_backtest(config)
