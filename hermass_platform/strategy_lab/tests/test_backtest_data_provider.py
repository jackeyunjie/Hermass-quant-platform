"""Unit tests for backtest_data_provider module.

Covers:
    - Required column extraction.
    - Missing column failure (BT_MISSING_REQUIRED_COLUMN).
    - Column name normalization (state_hex_d1 -> d1_state, close -> close_d1, ma_N -> ma_N_d1).
    - Date and universe filtering.
    - State cube join.
    - Optional risk column warnings.
    - Data version string computation.
    - FileNotFoundError for missing DB.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl
import pytest

from hermass_platform.strategy_lab.backtest_data_provider import (
    DuckDBBacktestDataProvider,
    _REQUIRED_BASE_COLUMNS,
    _STATE_COLUMN_ALIASES,
)
from hermass_platform.strategy_lab.backtest_models import (
    MarketDataBundle,
    MarketDataRequest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_minimal_db(
    db_path: Path,
    *,
    symbols: list[str] | None = None,
    n_days: int = 10,
    extra_columns: dict[str, list] | None = None,
    include_state: bool = True,
) -> None:
    """Create a minimal DuckDB with daily_bars and optional state_cube."""
    symbols = symbols or ["SYM_A"]
    con = duckdb.connect(str(db_path))

    dates = [f"2024-01-{d:02d}" for d in range(1, n_days + 1)]

    # Build columns
    base_cols = (
        "symbol VARCHAR, date DATE, open DOUBLE, high DOUBLE, "
        "low DOUBLE, close DOUBLE, volume BIGINT"
    )
    extra_defs = ""
    if extra_columns:
        for col_name in extra_columns:
            extra_defs += f", {col_name} DOUBLE"

    con.execute(f"CREATE TABLE daily_bars ({base_cols}{extra_defs})")

    rows = []
    for sym in symbols:
        for i, date in enumerate(dates):
            base_price = 10.0 + i * 0.1
            vals = [sym, date, base_price, base_price + 0.1, base_price - 0.1, base_price, 100000]
            if extra_columns:
                for col_name, col_vals in extra_columns.items():
                    vals.append(col_vals[i] if i < len(col_vals) else None)
            rows.append(vals)

    placeholders = ", ".join(["?"] * len(rows[0]))
    con.executemany(f"INSERT INTO daily_bars VALUES ({placeholders})", rows)

    if include_state:
        con.execute("""
            CREATE TABLE state_cube (
                symbol VARCHAR, date DATE,
                state_hex_d1 VARCHAR, state_hex_w1 VARCHAR, state_hex_mn1 VARCHAR
            )
        """)
        for sym in symbols:
            for date in dates:
                con.execute(
                    "INSERT INTO state_cube VALUES (?, ?, ?, ?, ?)",
                    [sym, date, "0x23", "0x21", "0x11"],
                )

    con.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDuckDBBacktestDataProvider:
    """Unit tests for DuckDBBacktestDataProvider."""

    def test_load_basic_columns(self, tmp_path: Path) -> None:
        """Provider loads basic OHLCV columns from DuckDB."""
        db = tmp_path / "test.duckdb"
        _create_minimal_db(db)

        provider = DuckDBBacktestDataProvider(foundation_db=db)
        request = MarketDataRequest(
            start_date="2024-01-01",
            end_date="2024-01-10",
            required_columns=[],
        )
        bundle = provider.load(request)

        for col in _REQUIRED_BASE_COLUMNS:
            assert col in bundle.bars.columns, f"Missing base column: {col}"
        assert len(bundle.bars) == 10  # 1 symbol * 10 days

    def test_load_multiple_symbols(self, tmp_path: Path) -> None:
        """Provider correctly filters by universe."""
        db = tmp_path / "test.duckdb"
        _create_minimal_db(db, symbols=["A", "B", "C"])

        provider = DuckDBBacktestDataProvider(foundation_db=db)
        request = MarketDataRequest(
            start_date="2024-01-01",
            end_date="2024-01-10",
            required_columns=[],
            universe=["A", "B"],
        )
        bundle = provider.load(request)

        syms = sorted(bundle.bars["symbol"].unique().to_list())
        assert syms == ["A", "B"]

    def test_missing_required_column_raises(self, tmp_path: Path) -> None:
        """Missing DSL-required column raises ValueError."""
        db = tmp_path / "test.duckdb"
        _create_minimal_db(db)

        provider = DuckDBBacktestDataProvider(foundation_db=db)
        request = MarketDataRequest(
            start_date="2024-01-01",
            end_date="2024-01-10",
            required_columns=["ma_5_d1", "ma_20_d1"],  # Not in DB
        )

        with pytest.raises(ValueError, match="BT_MISSING_REQUIRED_COLUMN"):
            provider.load(request)

    def test_column_normalization_state_aliases(self, tmp_path: Path) -> None:
        """state_hex_d1 is renamed to d1_state after state join."""
        db = tmp_path / "test.duckdb"
        _create_minimal_db(db, include_state=True)

        provider = DuckDBBacktestDataProvider(foundation_db=db)
        request = MarketDataRequest(
            start_date="2024-01-01",
            end_date="2024-01-10",
            required_columns=[],
            include_state=True,
        )
        bundle = provider.load(request)

        assert "d1_state" in bundle.bars.columns
        assert "w1_state" in bundle.bars.columns
        assert "mn1_state" in bundle.bars.columns

    def test_column_normalization_d1_aliases(self, tmp_path: Path) -> None:
        """close -> close_d1, ma_N -> ma_N_d1 aliases are created."""
        db = tmp_path / "test.duckdb"
        _create_minimal_db(
            db,
            extra_columns={"ma_5": [10.0] * 10, "ma_20": [10.0] * 10},
        )

        provider = DuckDBBacktestDataProvider(foundation_db=db)
        request = MarketDataRequest(
            start_date="2024-01-01",
            end_date="2024-01-10",
            required_columns=["ma_5_d1", "ma_20_d1"],
            include_state=False,
        )
        bundle = provider.load(request)

        assert "close_d1" in bundle.bars.columns
        assert "ma_5_d1" in bundle.bars.columns
        assert "ma_20_d1" in bundle.bars.columns

    def test_optional_risk_column_warning(self, tmp_path: Path) -> None:
        """Missing optional risk columns produce warnings, not errors."""
        db = tmp_path / "test.duckdb"
        _create_minimal_db(db, include_state=False)

        provider = DuckDBBacktestDataProvider(foundation_db=db)
        request = MarketDataRequest(
            start_date="2024-01-01",
            end_date="2024-01-10",
            required_columns=[],
            include_state=False,
        )
        bundle = provider.load(request)

        # is_limit_down and is_suspended should be absent -> warnings
        warning_text = " ".join(bundle.warnings)
        assert "is_limit_down" in warning_text or "is_suspended" in warning_text

    def test_date_range_filtering(self, tmp_path: Path) -> None:
        """Provider filters by date range correctly."""
        db = tmp_path / "test.duckdb"
        _create_minimal_db(db, n_days=30)

        provider = DuckDBBacktestDataProvider(foundation_db=db)
        request = MarketDataRequest(
            start_date="2024-01-05",
            end_date="2024-01-15",
            required_columns=[],
            include_state=False,
        )
        bundle = provider.load(request)

        assert len(bundle.bars) == 11  # days 5-15 inclusive

    def test_data_version_string(self, tmp_path: Path) -> None:
        """data_version contains db stem, date range, and row count."""
        db = tmp_path / "test_foundation.duckdb"
        _create_minimal_db(db)

        provider = DuckDBBacktestDataProvider(foundation_db=db)
        request = MarketDataRequest(
            start_date="2024-01-01",
            end_date="2024-01-10",
            required_columns=[],
            include_state=False,
        )
        bundle = provider.load(request)

        assert "test_foundation" in bundle.data_version
        assert "rows=10" in bundle.data_version

    def test_file_not_found_error(self, tmp_path: Path) -> None:
        """Non-existent DB path raises FileNotFoundError."""
        provider = DuckDBBacktestDataProvider(foundation_db=tmp_path / "nonexistent.duckdb")
        request = MarketDataRequest(
            start_date="2024-01-01",
            end_date="2024-01-10",
            required_columns=[],
        )

        with pytest.raises(FileNotFoundError, match="Foundation DB not found"):
            provider.load(request)

    def test_missing_daily_bars_table_raises(self, tmp_path: Path) -> None:
        """DB without daily_bars table raises ValueError."""
        db = tmp_path / "empty.duckdb"
        con = duckdb.connect(str(db))
        con.execute("CREATE TABLE other_table (x INTEGER)")
        con.close()

        provider = DuckDBBacktestDataProvider(foundation_db=db)
        request = MarketDataRequest(
            start_date="2024-01-01",
            end_date="2024-01-10",
            required_columns=[],
            include_state=False,
        )

        with pytest.raises(ValueError, match="BT_MISSING_REQUIRED_TABLE"):
            provider.load(request)

    def test_source_summary_populated(self, tmp_path: Path) -> None:
        """source_summary contains row counts, columns, and date range."""
        db = tmp_path / "test.duckdb"
        _create_minimal_db(db, symbols=["X", "Y"], n_days=5)

        provider = DuckDBBacktestDataProvider(foundation_db=db)
        request = MarketDataRequest(
            start_date="2024-01-01",
            end_date="2024-01-05",
            required_columns=[],
            include_state=False,
        )
        bundle = provider.load(request)

        assert bundle.source_summary["daily_bars_rows"] == 10  # 2 syms * 5 days
        assert "daily_bars_columns" in bundle.source_summary
        assert sorted(bundle.source_summary["symbols"]) == ["X", "Y"]
