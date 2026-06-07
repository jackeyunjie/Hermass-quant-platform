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
    parser.add_argument("--repeats", type=int, default=5)
    return parser.parse_args()


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
    repeats: int,
    is_synthetic: bool,
) -> list[dict]:
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
                AND date BETWEEN '2024-01-01' AND '2024-12-31'
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
                AND date BETWEEN '2024-01-01' AND '2024-12-31'
                AND (
                    close < ma_20 * 0.92
                    OR ma_5 > ma_20
                    OR ma_5 < ma_10
                )
                """
            ).pl()
    finally:
        con.close()

    times = []
    for run_index in range(repeats):
        t0 = time.perf_counter()
        result = run_vectorized_backtest(df)
        _ = result.shape
        t1 = time.perf_counter()
        times.append(t1 - t0)

    times_sorted = sorted(times)
    p50 = statistics.median(times)
    p95 = (
        times_sorted[int(len(times_sorted) * 0.95)]
        if len(times_sorted) > 1
        else times_sorted[0]
    )

    records = []
    for run_index, elapsed in enumerate(times):
        records.append(
            {
                "benchmark_name": "light_backtest_perf",
                "mode": mode,
                "universe_n": universe_n,
                "days": days,
                "run_index": run_index,
                "elapsed_s": round(elapsed, 6),
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
        db_path = create_synthetic_db(symbols=5000, days=252)

    output_path = (
        args.output
        or f"outputs/benchmarks/light_backtest_perf_{datetime.now().strftime('%Y%m%d')}.jsonl"
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    all_records: list[dict] = []
    for universe_n in [500, 2000, 5000]:
        for mode in ["full_polars", "filter_first"]:
            records = benchmark_mode(
                universe_n,
                252,
                mode,
                db_path,
                args.repeats,
                args.synthetic,
            )
            all_records.extend(records)

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(all_records)} records to {output_path}")


if __name__ == "__main__":
    main()
