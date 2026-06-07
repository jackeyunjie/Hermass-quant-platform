#!/usr/bin/env python3
"""Benchmark: Light Backtest Performance.

Compares full_polars vs filter_first for a simple MA strategy.
Strategy: MA5 golden cross MA20 entry; MA5 death cross MA10 or 8% stop loss exit.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

import duckdb
import polars as pl

sys.path.insert(0, str(Path(__file__).parent))
from _synthetic import create_synthetic_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Light Backtest Performance Benchmark")
    parser.add_argument("--db-path", type=str, default="data/p116_foundation.duckdb")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic data")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--runs", type=int, default=5, help="Repeat runs per config")
    parser.add_argument(
        "--symbols",
        type=str,
        default="500,2000,5000",
        help="Comma-separated symbol counts to benchmark",
    )
    parser.add_argument("--days", type=int, default=252, help="Days for synthetic data")
    return parser.parse_args()


def _parse_symbols(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",")]


def run_vectorized_backtest(df: pl.DataFrame) -> pl.DataFrame:
    """Vectorized backtest without Python row loops."""
    df = df.sort(["symbol", "date"])

    entry = (
        (pl.col("ma_5") > pl.col("ma_20"))
        & (
            pl.col("ma_5").shift(1).over("symbol")
            <= pl.col("ma_20").shift(1).over("symbol")
        )
    )
    exit_ma = (
        (pl.col("ma_5") < pl.col("ma_10"))
        & (
            pl.col("ma_5").shift(1).over("symbol")
            >= pl.col("ma_10").shift(1).over("symbol")
        )
    )

    raw_position = (
        pl.when(entry)
        .then(1)
        .when(exit_ma)
        .then(0)
        .otherwise(None)
        .fill_null(strategy="forward")
        .over("symbol")
    )

    entry_price = (
        pl.when(entry)
        .then(pl.col("close"))
        .otherwise(None)
        .fill_null(strategy="forward")
        .over("symbol")
    )

    stop_exit_expr = (
        (pl.col("close") <= entry_price * 0.92) & (raw_position == 1)
    ).fill_null(False)

    stop_exit_first = stop_exit_expr & (
        ~stop_exit_expr.shift(1).over("symbol").fill_null(False)
    )

    exit_combined = exit_ma | stop_exit_first

    position = (
        pl.when(entry)
        .then(1)
        .when(exit_combined)
        .then(0)
        .otherwise(None)
        .fill_null(strategy="forward")
        .over("symbol")
        .fill_null(0)
    )

    daily_ret = (
        position.shift(1).over("symbol")
        * (pl.col("close") / pl.col("close").shift(1).over("symbol") - 1)
    ).fill_null(0)

    portfolio = (
        df.with_columns([daily_ret.alias("daily_ret")])
        .group_by("date")
        .agg(pl.col("daily_ret").mean().alias("portfolio_ret"))
        .sort("date")
    )

    # Force materialization
    return portfolio.select(pl.all())


def benchmark_mode(
    universe_n: int,
    days: int,
    mode: str,
    db_path: str,
    runs: int,
    is_synthetic: bool,
) -> list[dict]:
    records: list[dict] = []
    data_load_times: list[float] = []
    signal_gen_times: list[float] = []
    equity_metrics_times: list[float] = []
    total_times: list[float] = []
    peak_memories: list[float | None] = []

    for run_index in range(runs):
        tracemalloc.start()

        # Stage 1: data load
        t0 = time.perf_counter()
        con = duckdb.connect(db_path)
        try:
            if mode == "full_polars":
                df = con.execute(
                    f"""
                    SELECT symbol, date, close, ma_5, ma_10, ma_20
                    FROM daily_bars
                    WHERE symbol IN (
                        SELECT DISTINCT symbol FROM daily_bars LIMIT {universe_n}
                    )
                    """
                ).pl()
            else:  # filter_first
                df = con.execute(
                    f"""
                    SELECT symbol, date, close, ma_5, ma_10, ma_20
                    FROM daily_bars
                    WHERE symbol IN (
                        SELECT DISTINCT symbol FROM daily_bars LIMIT {universe_n}
                    )
                    AND (
                        close < ma_20 * 0.92
                        OR ma_5 > ma_20
                        OR ma_5 < ma_10
                    )
                    """
                ).pl()
        finally:
            con.close()
        t1 = time.perf_counter()
        data_load_s = t1 - t0

        # Stage 2: signal generation
        t0 = time.perf_counter()
        df_sorted = df.sort(["symbol", "date"])
        entry = (
            (pl.col("ma_5") > pl.col("ma_20"))
            & (
                pl.col("ma_5").shift(1).over("symbol")
                <= pl.col("ma_20").shift(1).over("symbol")
            )
        )
        exit_ma = (
            (pl.col("ma_5") < pl.col("ma_10"))
            & (
                pl.col("ma_5").shift(1).over("symbol")
                >= pl.col("ma_10").shift(1).over("symbol")
            )
        )
        raw_position = (
            pl.when(entry)
            .then(1)
            .when(exit_ma)
            .then(0)
            .otherwise(None)
            .fill_null(strategy="forward")
            .over("symbol")
        )
        entry_price = (
            pl.when(entry)
            .then(pl.col("close"))
            .otherwise(None)
            .fill_null(strategy="forward")
            .over("symbol")
        )
        stop_exit_expr = (
            (pl.col("close") <= entry_price * 0.92) & (raw_position == 1)
        ).fill_null(False)
        stop_exit_first = stop_exit_expr & (
            ~stop_exit_expr.shift(1).over("symbol").fill_null(False)
        )
        exit_combined = exit_ma | stop_exit_first
        position = (
            pl.when(entry)
            .then(1)
            .when(exit_combined)
            .then(0)
            .otherwise(None)
            .fill_null(strategy="forward")
            .over("symbol")
            .fill_null(0)
        )
        t1 = time.perf_counter()
        signal_gen_s = t1 - t0

        # Stage 3: equity curve + metrics
        t0 = time.perf_counter()
        daily_ret = (
            position.shift(1).over("symbol")
            * (pl.col("close") / pl.col("close").shift(1).over("symbol") - 1)
        ).fill_null(0)
        portfolio = (
            df_sorted.with_columns([daily_ret.alias("daily_ret")])
            .group_by("date")
            .agg(pl.col("daily_ret").mean().alias("portfolio_ret"))
            .sort("date")
        )
        result = portfolio.select(pl.all())
        _ = result.shape
        t1 = time.perf_counter()
        equity_metrics_s = t1 - t0

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_memory_mb = round(peak / 1024 / 1024, 2)

        total_s = data_load_s + signal_gen_s + equity_metrics_s

        data_load_times.append(data_load_s)
        signal_gen_times.append(signal_gen_s)
        equity_metrics_times.append(equity_metrics_s)
        total_times.append(total_s)
        peak_memories.append(peak_memory_mb)

    # Compute percentiles on total time
    total_sorted = sorted(total_times)
    p50 = statistics.median(total_times)
    p95 = (
        total_sorted[int(len(total_sorted) * 0.95)]
        if len(total_sorted) > 1
        else total_sorted[0]
    )

    for run_index in range(runs):
        records.append(
            {
                "benchmark_name": "light_backtest_perf",
                "mode": mode,
                "universe_n": universe_n,
                "days": days,
                "run_index": run_index,
                "elapsed_s": round(total_times[run_index], 6),
                "data_load_s": round(data_load_times[run_index], 6),
                "signal_gen_s": round(signal_gen_times[run_index], 6),
                "equity_metrics_s": round(equity_metrics_times[run_index], 6),
                "peak_memory_mb": peak_memories[run_index],
                "p50_s": round(p50, 6),
                "p95_s": round(p95, 6),
                "data_source": "synthetic" if is_synthetic else "real",
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "notes": f"rows_loaded={df.height}",
            }
        )
    return records


def main() -> None:
    args = parse_args()
    db_path = args.db_path
    if args.synthetic:
        db_path = create_synthetic_db(symbols=max(_parse_symbols(args.symbols)), days=args.days)

    output_path = (
        args.output
        or f"outputs/benchmarks/light_backtest_perf_{datetime.now().strftime('%Y%m%d')}.jsonl"
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    all_records: list[dict] = []
    for universe_n in _parse_symbols(args.symbols):
        for mode in ["full_polars", "filter_first"]:
            records = benchmark_mode(
                universe_n,
                args.days,
                mode,
                db_path,
                args.runs,
                args.synthetic,
            )
            all_records.extend(records)

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(all_records)} records to {output_path}")


if __name__ == "__main__":
    main()
