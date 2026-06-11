"""Synthetic data generator for benchmarks.

Loops and Python-level generation are allowed here because this is setup,
not the benchmark hot path.
"""

from __future__ import annotations

import os
import random
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import polars as pl


def _generate_daily_bars(symbols: int, days: int, seed: int = 42) -> pl.DataFrame:
    rng = random.Random(seed)

    # Generate symbol list
    sym_list = [f"SYM{i:04d}" for i in range(symbols)]

    # Generate date list (calendar days for simplicity)
    start = datetime(2024, 1, 1)
    date_list = [(start + timedelta(days=d)).date() for d in range(days)]

    # Build grid
    df = (
        pl.DataFrame({"symbol": sym_list})
        .join(pl.DataFrame({"date": date_list}), how="cross")
    )

    n = df.height

    # Random walk for close
    init_prices = pl.Series("close", [rng.uniform(10.0, 200.0) for _ in range(n)])
    changes = pl.Series("chg", [rng.uniform(-0.03, 0.03) for _ in range(n)])

    # For a proper per-symbol random walk we need grouping, but for synthetic fixture
    # a global random walk per symbol ordering is acceptable.
    # We'll do it via a simple expression using over(symbol) later; easier:
    # assign a random number per row then cumulative sum within symbol.
    df = df.with_columns(
        pl.lit(rng.uniform(-0.03, 0.03)).alias("daily_ret")
    )
    df = df.with_columns(
        (1 + pl.col("daily_ret")).log().cum_sum().over("symbol").exp().alias("close_raw")
    )
    df = df.with_columns(
        (pl.col("close_raw") * 100).alias("close")
    )

    # Derive ohlc from close
    df = df.with_columns(
        (pl.col("close") * (1 + pl.lit(rng.uniform(-0.01, 0.01)))).alias("open"),
        (pl.col("close") * (1 + pl.lit(rng.uniform(0.0, 0.02)))).alias("high"),
        (pl.col("close") * (1 + pl.lit(rng.uniform(-0.02, 0.0)))).alias("low"),
    )
    df = df.with_columns(
        pl.lit(rng.randint(1_000_000, 10_000_000)).alias("volume")
    )

    # Precompute indicators using Polars window functions
    df = df.sort(["symbol", "date"])
    df = df.with_columns(
        pl.col("close").rolling_mean(window_size=5).over("symbol").alias("ma_5"),
        pl.col("close").rolling_mean(window_size=10).over("symbol").alias("ma_10"),
        pl.col("close").rolling_mean(window_size=20).over("symbol").alias("ma_20"),
        pl.col("close").rolling_mean(window_size=60).over("symbol").alias("ma_60"),
    )
    # ATR14 synthetic
    tr = pl.max_horizontal(
        pl.col("high") - pl.col("low"),
        (pl.col("high") - pl.col("close").shift(1)).abs(),
        (pl.col("low") - pl.col("close").shift(1)).abs(),
    ).over("symbol")
    df = df.with_columns(
        tr.rolling_mean(window_size=14).over("symbol").alias("atr_14")
    )
    # BB position synthetic
    df = df.with_columns(
        pl.col("close").rolling_mean(window_size=20).over("symbol").alias("bb_mid"),
        pl.col("close").rolling_std(window_size=20).over("symbol").alias("bb_std"),
    )
    df = df.with_columns(
        ((pl.col("close") - pl.col("bb_mid")) / (2 * pl.col("bb_std"))).alias("bb_position")
    )
    # Volume ratio
    df = df.with_columns(
        pl.col("volume").rolling_mean(window_size=20).over("symbol").alias("volume_ma_20")
    )
    df = df.with_columns(
        (pl.col("volume") / pl.col("volume_ma_20")).alias("volume_ratio")
    )
    # ADX14 synthetic placeholder (random)
    df = df.with_columns(
        pl.lit(rng.uniform(10.0, 50.0)).alias("adx_14")
    )
    # Limit up flag
    df = df.with_columns(
        (pl.col("close") / pl.col("close").shift(1) >= 1.095).over("symbol").alias("is_limit_up")
    )

    # Clean nulls from rolling windows at start
    df = df.fill_null(strategy="backward")

    # Select final columns
    return df.select([
        "symbol", "date", "open", "high", "low", "close", "volume",
        "ma_5", "ma_10", "ma_20", "ma_60", "atr_14", "bb_position",
        "volume_ratio", "adx_14", "is_limit_up",
    ])


def _generate_state_cube(symbols: int, days: int, seed: int = 43) -> pl.DataFrame:
    rng = random.Random(seed)
    sym_list = [f"SYM{i:04d}" for i in range(symbols)]
    start = datetime(2024, 1, 1)
    date_list = [(start + timedelta(days=d)).date() for d in range(days)]
    states = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B"]
    extra_states = ["1A", "2A", "3A", "4A"]

    df = (
        pl.DataFrame({"symbol": sym_list})
        .join(pl.DataFrame({"date": date_list}), how="cross")
    )
    df = df.with_columns(
        pl.lit(rng.choice(states)).alias("d1_state"),
        pl.lit(rng.choice(states)).alias("w1_state"),
        pl.lit(rng.choice(states)).alias("mn1_state"),
        pl.lit(rng.choice(extra_states)).alias("h4_state"),
        pl.lit(rng.choice(extra_states)).alias("h1_state"),
        pl.lit(rng.uniform(0.0, 1.0)).alias("ef_width"),
        pl.lit(rng.randint(0, 10)).alias("ef_count"),
    )
    return df.select([
        "symbol", "date", "d1_state", "w1_state", "mn1_state",
        "h4_state", "h1_state", "ef_width", "ef_count",
    ])


def create_synthetic_db(
    db_path: str | None = None,
    symbols: int = 5000,
    days: int = 252,
) -> str:
    """Create a temporary DuckDB with synthetic daily_bars and state_cube.

    Returns the path to the created database.
    """
    if db_path is None:
        db_path = str(
            Path(tempfile.gettempdir())
            / f"hermass_synthetic_{os.getpid()}_{symbols}_{days}.duckdb"
        )
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    if Path(db_path).exists():
        os.remove(db_path)

    con = duckdb.connect(db_path)
    df_bars = _generate_daily_bars(symbols, days)
    con.execute("CREATE TABLE daily_bars AS SELECT * FROM df_bars")
    df_cube = _generate_state_cube(symbols, days)
    con.execute("CREATE TABLE state_cube AS SELECT * FROM df_cube")
    con.execute("CREATE INDEX idx_state_cube_date ON state_cube(date)")
    con.execute("CREATE INDEX idx_state_cube_symbol ON state_cube(symbol)")
    con.close()
    return db_path


def ensure_synthetic_table(db_path: str, table: str, symbols: int, days: int) -> None:
    """Ensure the given table exists in db_path with expected row count."""
    con = duckdb.connect(db_path)
    try:
        count = con.execute(
            f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table}'"
        ).fetchone()[0]
        if count == 0:
            if table == "daily_bars":
                df = _generate_daily_bars(symbols, days)
            elif table == "state_cube":
                df = _generate_state_cube(symbols, days)
            else:
                raise ValueError(f"Unknown table {table}")
            con.execute(f"CREATE TABLE {table} AS SELECT * FROM df")
            if table == "state_cube":
                con.execute("CREATE INDEX idx_state_cube_date ON state_cube(date)")
                con.execute("CREATE INDEX idx_state_cube_symbol ON state_cube(symbol)")
    finally:
        con.close()
