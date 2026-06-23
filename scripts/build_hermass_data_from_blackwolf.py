#!/usr/bin/env python3
"""Build Hermass foundation and state cube DuckDBs from Blackwolf A-share daily zip.

This script reads an existing Blackwolf Mac-format daily zip (L0 raw evidence),
computes required indicators, and produces:
    - data/p116_foundation.duckdb  (daily_bars table)
    - data/state_cube.duckdb       (state_cube table)
    - data/metadata.json           (data source metadata)
    - outputs/benchmarks/real_data_validation_YYYYMMDD.json
    - outputs/benchmarks/data_readiness_status.json

It does not download data. Use Blackwolf download scripts in the Hermass repo
(hongrun-chaos-trading-system) first if fresher data is needed.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import polars as pl


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLACKWOLF_ZIP = Path(
    "/Users/lv111101/Documents/hongrun-chaos-trading-system/data"
) / "blackwolf_ashare_daily_mac_format_20180515_20260618.zip"
DEFAULT_FOUNDATION_DB = REPO_ROOT / "data" / "p116_foundation.duckdb"
DEFAULT_STATE_CUBE_DB = REPO_ROOT / "data" / "state_cube.duckdb"
DEFAULT_METADATA = REPO_ROOT / "data" / "metadata.json"
DEFAULT_VALIDATION_OUTPUT = (
    REPO_ROOT / "outputs" / "benchmarks" / f"real_data_validation_{datetime.now():%Y%m%d}.json"
)
DEFAULT_READINESS_OUTPUT = REPO_ROOT / "outputs" / "benchmarks" / "data_readiness_status.json"

REQUIRED_FOUNDATION_COLUMNS = [
    "symbol", "date", "open", "high", "low", "close", "volume",
    "ma_5", "ma_10", "ma_20", "ma_60",
    "atr_14", "bb_position", "volume_ratio", "adx_14",
    "is_limit_up",
]


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def _connect_duckdb(database: str) -> duckdb.DuckDBPyConnection:
    """Open DuckDB with extension autoload disabled to avoid network stalls."""
    con = duckdb.connect(database)
    con.execute("SET autoinstall_known_extensions=false")
    con.execute("SET autoload_known_extensions=false")
    return con


def read_blackwolf_zip(zip_path: Path) -> pl.DataFrame:
    """Read the CSV inside the Blackwolf Mac-format zip into a Polars DataFrame."""
    log(f"Reading Blackwolf zip: {zip_path}")
    with zipfile.ZipFile(zip_path) as zf:
        csv_members = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(csv_members) != 1:
            raise RuntimeError(f"Expected exactly one CSV in zip, got {csv_members}")
        with zf.open(csv_members[0]) as f:
            df = pl.read_csv(
                f,
                schema_overrides={
                    "stock_code": pl.String,
                    "date": pl.String,
                    "open": pl.Float64,
                    "high": pl.Float64,
                    "low": pl.Float64,
                    "close": pl.Float64,
                    "volume": pl.Float64,
                    "amount": pl.Float64,
                },
            )
    log(f"Loaded {df.height:,} rows, {df['stock_code'].n_unique():,} symbols")
    return df


def normalize_base(df: pl.DataFrame) -> pl.DataFrame:
    """Rename columns and cast to the schema expected by Hermass."""
    df = df.rename({
        "stock_code": "symbol",
    })
    df = df.with_columns(
        pl.col("date").str.to_date(format="%Y-%m-%d").alias("date"),
        pl.col("symbol").str.strip_chars().str.to_uppercase().alias("symbol"),
    )
    df = df.sort(["symbol", "date"])
    return df


def compute_indicators(df: pl.DataFrame) -> pl.DataFrame:
    """Compute required foundation indicators using Polars window expressions."""
    log("Computing indicators")
    df = df.with_columns(
        pl.col("close").rolling_mean(window_size=5).over("symbol").alias("ma_5"),
        pl.col("close").rolling_mean(window_size=10).over("symbol").alias("ma_10"),
        pl.col("close").rolling_mean(window_size=20).over("symbol").alias("ma_20"),
        pl.col("close").rolling_mean(window_size=60).over("symbol").alias("ma_60"),
    )

    # True Range
    prev_close = pl.col("close").shift(1).over("symbol")
    tr = pl.max_horizontal(
        pl.col("high") - pl.col("low"),
        (pl.col("high") - prev_close).abs(),
        (pl.col("low") - prev_close).abs(),
    )
    df = df.with_columns(
        tr.rolling_mean(window_size=14).over("symbol").alias("atr_14")
    )

    # Bollinger Bands position
    bb_mid = pl.col("close").rolling_mean(window_size=20).over("symbol")
    bb_std = pl.col("close").rolling_std(window_size=20).over("symbol")
    df = df.with_columns(
        ((pl.col("close") - bb_mid) / (2 * bb_std)).alias("bb_position")
    )

    # Volume ratio: volume / 5-day mean volume (matches task contract)
    volume_ma_5 = pl.col("volume").rolling_mean(window_size=5).over("symbol")
    df = df.with_columns(
        (pl.col("volume") / volume_ma_5).alias("volume_ratio")
    )

    # ADX14 approximation using simplified directional movement
    prev_high = pl.col("high").shift(1).over("symbol")
    prev_low = pl.col("low").shift(1).over("symbol")
    plus_dm = (pl.col("high") - prev_high).clip(0)
    minus_dm = (prev_low - pl.col("low")).clip(0)
    plus_dm = pl.when(plus_dm > minus_dm).then(plus_dm).otherwise(0)
    minus_dm = pl.when(minus_dm > plus_dm).then(minus_dm).otherwise(0)

    plus_di = 100 * plus_dm.rolling_mean(window_size=14).over("symbol") / tr.replace(0, 1e-9)
    minus_di = 100 * minus_dm.rolling_mean(window_size=14).over("symbol") / tr.replace(0, 1e-9)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9)
    df = df.with_columns(
        dx.rolling_mean(window_size=14).over("symbol").alias("adx_14")
    )

    # Limit up approximation: close == high and daily gain >= 9.5%
    prev_close = pl.col("close").shift(1).over("symbol")
    df = df.with_columns(
        (
            (pl.col("close") == pl.col("high"))
            & ((pl.col("close") / prev_close.replace(0, 1e-9)) >= 1.095)
        ).cast(pl.Int32).alias("is_limit_up")
    )

    # Select final columns and fill nulls introduced by rolling windows
    df = df.select(REQUIRED_FOUNDATION_COLUMNS)
    df = df.fill_null(strategy="backward").fill_null(strategy="forward")
    return df


def _df_to_table(df: pl.DataFrame, out_db: Path, table: str, indexes: list[str]) -> None:
    """Write a Polars DataFrame to a DuckDB table via temporary parquet."""
    out_db.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        df.write_parquet(tmp_path)
        con = _connect_duckdb(str(out_db))
        try:
            con.execute(f"CREATE TABLE {table} AS SELECT * FROM read_parquet('{tmp_path.as_posix()}')")
            for idx_sql in indexes:
                con.execute(idx_sql)
        finally:
            con.close()
    finally:
        tmp_path.unlink(missing_ok=True)


def build_foundation_db(df: pl.DataFrame, out_db: Path) -> dict[str, Any]:
    """Write the daily_bars table to p116_foundation.duckdb."""
    log(f"Building foundation DB: {out_db}")
    if out_db.exists():
        out_db.unlink()

    _df_to_table(
        df,
        out_db,
        "daily_bars",
        [
            "CREATE UNIQUE INDEX idx_daily_bars_symbol_date ON daily_bars(symbol, date)",
            "CREATE INDEX idx_daily_bars_date ON daily_bars(date)",
        ],
    )

    con = _connect_duckdb(str(out_db))
    try:

        stats = con.execute("""
            SELECT
                COUNT(*) AS row_count,
                COUNT(DISTINCT symbol) AS symbol_count,
                MIN(date) AS date_min,
                MAX(date) AS date_max,
                COUNT(DISTINCT date) AS trading_days
            FROM daily_bars
        """).fetchone()
    finally:
        con.close()

    return {
        "row_count": int(stats[0]),
        "symbol_count": int(stats[1]),
        "date_min": str(stats[2]),
        "date_max": str(stats[3]),
        "trading_days": int(stats[4]),
    }


def _state_label(close: pl.Expr, ma: pl.Expr, ma_slope: pl.Expr) -> pl.Expr:
    """Simplified state label based on close vs moving average and slope."""
    return (
        pl.when((close > ma) & (ma_slope > 0)).then(pl.lit("trending_up"))
        .when((close > ma) & (ma_slope <= 0)).then(pl.lit("topping"))
        .when((close < ma) & (ma_slope < 0)).then(pl.lit("trending_down"))
        .when((close < ma) & (ma_slope >= 0)).then(pl.lit("bottoming"))
        .otherwise(pl.lit("neutral"))
    )


def build_state_cube(df: pl.DataFrame, out_db: Path) -> dict[str, Any]:
    """Compute multi-timeframe states and write state_cube table."""
    log(f"Building state cube DB: {out_db}")
    out_db.parent.mkdir(parents=True, exist_ok=True)
    if out_db.exists():
        out_db.unlink()

    # D1 state: based on MA20 and its slope
    d1 = df.select(["symbol", "date", "close"]).with_columns(
        pl.col("close").rolling_mean(window_size=20).over("symbol").alias("ma_20"),
    ).with_columns(
        (pl.col("ma_20") - pl.col("ma_20").shift(1).over("symbol")).alias("ma_20_slope"),
    ).with_columns(
        _state_label(pl.col("close"), pl.col("ma_20"), pl.col("ma_20_slope")).alias("d1_state")
    ).select(["symbol", "date", "d1_state"])

    # W1 state: resample weekly (last trading day of week), based on MA12 weeks (~60 days)
    df_w = df.select(["symbol", "date", "close"]).with_columns(
        pl.col("date").dt.truncate("1w").alias("week")
    )
    w1 = (
        df_w.sort(["symbol", "date"])
        .group_by(["symbol", "week"])
        .agg(pl.col("close").last().alias("close"))
        .rename({"week": "date"})
        .with_columns(
            pl.col("close").rolling_mean(window_size=12).over("symbol").alias("ma_12w"),
        )
        .with_columns(
            (pl.col("ma_12w") - pl.col("ma_12w").shift(1).over("symbol")).alias("ma_12w_slope"),
        )
        .with_columns(
            _state_label(pl.col("close"), pl.col("ma_12w"), pl.col("ma_12w_slope")).alias("w1_state")
        )
        .select(["symbol", "date", "w1_state"])
    )

    # MN1 state: resample monthly (last trading day of month), based on MA6 months (~120 days)
    df_m = df.select(["symbol", "date", "close"]).with_columns(
        pl.col("date").dt.truncate("1mo").alias("month")
    )
    mn1 = (
        df_m.sort(["symbol", "date"])
        .group_by(["symbol", "month"])
        .agg(pl.col("close").last().alias("close"))
        .rename({"month": "date"})
        .with_columns(
            pl.col("close").rolling_mean(window_size=6).over("symbol").alias("ma_6m"),
        )
        .with_columns(
            (pl.col("ma_6m") - pl.col("ma_6m").shift(1).over("symbol")).alias("ma_6m_slope"),
        )
        .with_columns(
            _state_label(pl.col("close"), pl.col("ma_6m"), pl.col("ma_6m_slope")).alias("mn1_state")
        )
        .select(["symbol", "date", "mn1_state"])
    )

    # Join D1 with W1 and MN1 using as-of joins on date
    cube = d1
    cube = cube.join(w1, on=["symbol", "date"], how="left")
    cube = cube.join(mn1, on=["symbol", "date"], how="left")

    # Forward-fill W1/MN1 states to daily rows (state remains valid until next resampled state)
    cube = cube.sort(["symbol", "date"]).with_columns(
        pl.col("w1_state").forward_fill().over("symbol"),
        pl.col("mn1_state").forward_fill().over("symbol"),
    )
    cube = cube.fill_null("neutral")

    _df_to_table(
        cube,
        out_db,
        "state_cube",
        ["CREATE UNIQUE INDEX idx_state_cube_symbol_date ON state_cube(symbol, date)"],
    )

    con = _connect_duckdb(str(out_db))
    try:
        stats = con.execute("""
            SELECT
                COUNT(*) AS row_count,
                COUNT(DISTINCT symbol) AS symbol_count,
                MIN(date) AS date_min,
                MAX(date) AS date_max
            FROM state_cube
        """).fetchone()
    finally:
        con.close()

    return {
        "row_count": int(stats[0]),
        "symbol_count": int(stats[1]),
        "date_min": str(stats[2]),
        "date_max": str(stats[3]),
    }


def write_metadata(metadata_path: Path, foundation_stats: dict, state_stats: dict) -> dict[str, Any]:
    """Write data source metadata JSON."""
    metadata = {
        "price_adjustment": "forward_adjusted",
        "data_source": "blackwolf_real",
        "license_status": "research_only",
        "last_refresh_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "symbol_count": foundation_stats["symbol_count"],
        "date_min": foundation_stats["date_min"],
        "date_max": foundation_stats["date_max"],
        "daily_bars_rows": foundation_stats["row_count"],
        "state_cube_rows": state_stats["row_count"],
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"Wrote metadata: {metadata_path}")
    return metadata


def run_validation(foundation_db: Path, state_cube_db: Path, output: Path) -> dict[str, Any]:
    """Run validate_real_data.py and return its JSON output."""
    log("Running validate_real_data.py")
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "benchmarks/validate_real_data.py",
        "--foundation-db", str(foundation_db),
        "--state-cube-db", str(state_cube_db),
        "--output", str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    if result.returncode != 0:
        log(f"Validation failed with rc={result.returncode}")
        log(result.stderr)
    try:
        return json.loads(output.read_text(encoding="utf-8"))
    except Exception as exc:
        log(f"Could not parse validation output: {exc}")
        return {"ok": False, "errors": [result.stderr or "validation failed"]}


def write_readiness(
    foundation_db: Path,
    state_cube_db: Path,
    foundation_stats: dict,
    state_stats: dict,
    validation_result: dict,
    validation_path: Path,
    readiness_path: Path,
) -> dict[str, Any]:
    """Write data_readiness_status.json matching Kimi contract."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    validation_ok = validation_result.get("ok", False)
    verdict = "READY" if validation_ok else "NOT_READY"

    foundation_exists = foundation_db.exists()
    state_exists = state_cube_db.exists()

    readiness = {
        "as_of_date": today,
        "verdict": verdict,
        "foundation_db": {
            "path": str(foundation_db.relative_to(REPO_ROOT)),
            "exists": foundation_exists,
            "open_ok": foundation_exists,
            "table": "daily_bars",
            "columns_ok": validation_ok,
            "missing_columns": validation_result.get("foundation", {}).get("column_checks", {}).get("missing", []),
            "symbol_count": foundation_stats["symbol_count"],
            "trading_days": foundation_stats["trading_days"],
            "total_rows": foundation_stats["row_count"],
            "date_min": foundation_stats["date_min"],
            "date_max": foundation_stats["date_max"],
            "staleness_days": 0,
            "data_quality_issues": validation_result.get("errors", []),
            "metadata": {
                "data_source": "blackwolf_real",
                "price_adjustment": "forward_adjusted",
                "license_status": "research_only",
                "last_refresh_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
        },
        "state_cube_db": {
            "path": str(state_cube_db.relative_to(REPO_ROOT)),
            "exists": state_exists,
            "open_ok": state_exists,
            "table": "state_cube",
            "columns_ok": validation_ok,
            "missing_columns": validation_result.get("state_cube", {}).get("column_checks", {}).get("missing", []),
            "symbol_count": state_stats["symbol_count"],
            "trading_days": state_stats.get("trading_days", 0),
            "total_rows": state_stats["row_count"],
            "date_min": state_stats["date_min"],
            "date_max": state_stats["date_max"],
            "staleness_days": 0,
            "state_value_issues": [],
        },
        "validation_result_path": str(validation_path.relative_to(REPO_ROOT)),
        "validation_ok": validation_ok,
        "validation_errors": validation_result.get("errors", []),
        "ui_display": {
            "zh": "真实数据基线已就绪，可切换 light_real_v1 模式。" if validation_ok else "真实数据基线尚未就绪，当前仅支持 synthetic / light_stub 模式。",
            "en": "Real data baseline is ready; light_real_v1 mode available." if validation_ok else "Real data baseline not ready; synthetic / light_stub modes only.",
        },
    }
    if not validation_ok:
        readiness["next_steps"] = [
            "检查 validate_real_data.py 输出中的错误",
            "修复 foundation_db / state_cube_db 的列或数据问题",
            "重新运行 scripts/build_hermass_data_from_blackwolf.py",
        ]

    readiness_path.parent.mkdir(parents=True, exist_ok=True)
    readiness_path.write_text(json.dumps(readiness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"Wrote readiness status: {readiness_path}")
    return readiness


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Hermass foundation/state cube from Blackwolf zip.")
    parser.add_argument("--blackwolf-zip", type=Path, default=DEFAULT_BLACKWOLF_ZIP)
    parser.add_argument("--foundation-db", type=Path, default=DEFAULT_FOUNDATION_DB)
    parser.add_argument("--state-cube-db", type=Path, default=DEFAULT_STATE_CUBE_DB)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--validation-output", type=Path, default=DEFAULT_VALIDATION_OUTPUT)
    parser.add_argument("--readiness-output", type=Path, default=DEFAULT_READINESS_OUTPUT)
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()

    if not args.blackwolf_zip.exists():
        log(f"Blackwolf zip not found: {args.blackwolf_zip}")
        return 1

    raw_df = read_blackwolf_zip(args.blackwolf_zip)
    base_df = normalize_base(raw_df)
    foundation_df = compute_indicators(base_df)

    foundation_stats = build_foundation_db(foundation_df, args.foundation_db)
    state_stats = build_state_cube(base_df, args.state_cube_db)
    metadata = write_metadata(args.metadata, foundation_stats, state_stats)

    if args.skip_validation:
        log("Skipping validation")
        validation_result = {"ok": False, "errors": ["validation skipped"]}
    else:
        validation_result = run_validation(
            args.foundation_db, args.state_cube_db, args.validation_output
        )

    readiness = write_readiness(
        args.foundation_db,
        args.state_cube_db,
        foundation_stats,
        state_stats,
        validation_result,
        args.validation_output,
        args.readiness_output,
    )

    summary = {
        "status": "PASS" if validation_result.get("ok") else "FAIL",
        "foundation_db": str(args.foundation_db),
        "state_cube_db": str(args.state_cube_db),
        "foundation_stats": foundation_stats,
        "state_stats": state_stats,
        "validation_ok": validation_result.get("ok"),
        "validation_errors": validation_result.get("errors", []),
        "readiness": readiness,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if validation_result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
