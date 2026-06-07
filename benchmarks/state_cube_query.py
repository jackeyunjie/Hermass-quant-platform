#!/usr/bin/env python3
"""Benchmark: State Cube query patterns.

Compares no-cache vs column-pruned vs LRU-cache queries.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import statistics
import sys
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import duckdb
import polars as pl

sys.path.insert(0, str(Path(__file__).parent))
from _synthetic import create_synthetic_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="State Cube Query Benchmark")
    parser.add_argument("--db-path", type=str, default="data/state_cube.duckdb")
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--queries", type=int, default=50)
    return parser.parse_args()


def benchmark_mode(
    mode: str,
    db_path: str,
    queries_n: int,
    is_synthetic: bool,
) -> list[dict]:
    con = duckdb.connect(db_path)
    try:
        dates = [
            row[0]
            for row in con.execute(
                "SELECT DISTINCT date FROM state_cube ORDER BY date"
            ).fetchall()
        ]
        if not dates:
            raise ValueError("No dates in state_cube")
    finally:
        con.close()

    rng = random.Random(42)
    query_specs = []
    for _ in range(queries_n):
        date = rng.choice(dates)
        if mode == "no_cache":
            cols = "*"
        else:
            cols = "symbol, date, d1_state, w1_state, mn1_state"
        query_specs.append((date, cols))

    times = []
    if mode == "lru_cache":

        @lru_cache(maxsize=5)
        def cached_query(date: str, cols: str) -> pl.DataFrame:
            c = duckdb.connect(db_path)
            try:
                df = c.execute(
                    f"SELECT {cols} FROM state_cube WHERE date = ?", [date]
                ).pl()
            finally:
                c.close()
            return df

        for date, cols in query_specs:
            t0 = time.perf_counter()
            df = cached_query(date, cols)
            _ = df.shape
            t1 = time.perf_counter()
            times.append(t1 - t0)
    else:
        con = duckdb.connect(db_path)
        try:
            for date, cols in query_specs:
                t0 = time.perf_counter()
                df = con.execute(
                    f"SELECT {cols} FROM state_cube WHERE date = ?", [date]
                ).pl()
                _ = df.shape
                t1 = time.perf_counter()
                times.append(t1 - t0)
        finally:
            con.close()

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
                "benchmark_name": "state_cube_query",
                "mode": mode,
                "universe_n": None,
                "days": len(dates),
                "run_index": run_index,
                "elapsed_s": round(elapsed, 6),
                "p50_s": round(p50, 6),
                "p95_s": round(p95, 6),
                "data_source": "synthetic" if is_synthetic else "real",
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "notes": f"queries={queries_n}",
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
        or f"outputs/benchmarks/state_cube_query_{datetime.now().strftime('%Y%m%d')}.jsonl"
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    all_records: list[dict] = []
    for mode in ["no_cache", "pruned", "lru_cache"]:
        records = benchmark_mode(mode, db_path, args.queries, args.synthetic)
        all_records.extend(records)

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(all_records)} records to {output_path}")


if __name__ == "__main__":
    main()
