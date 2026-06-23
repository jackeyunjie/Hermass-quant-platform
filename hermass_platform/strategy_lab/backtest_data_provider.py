"""Backtest Data Provider - DuckDB data loading and column normalization.

This module is the boundary between raw DuckDB storage and the Polars-based
backtest engine. It is responsible ONLY for:
    - Opening DuckDB connections.
    - Loading daily bars with date/universe filtering.
    - Joining state_cube data.
    - Column name normalization (e.g. state_hex_d1 -> d1_state).
    - Required column validation.

It does NOT contain any trading logic, signal computation, or metrics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import polars as pl

from .backtest_models import MarketDataBundle, MarketDataRequest
from ._duckdb_helper import connect_duckdb


# ---------------------------------------------------------------------------
# Column Name Normalization Map
# ---------------------------------------------------------------------------

# Maps source column names to normalized names expected by the engine.
_STATE_COLUMN_ALIASES: dict[str, str] = {
    "state_hex_d1": "d1_state",
    "state_hex_w1": "w1_state",
    "state_hex_mn1": "mn1_state",
}

# Maps normalized state column names back to the source names used by the
# condition translator and engine. This allows the provider to expose both
# naming conventions when only one is present in the raw data.
_STATE_REVERSE_ALIASES: dict[str, str] = {
    "d1_state": "state_hex_d1",
    "w1_state": "state_hex_w1",
    "mn1_state": "state_hex_mn1",
}

# Columns that must always be present in daily bars.
_REQUIRED_BASE_COLUMNS: list[str] = [
    "symbol",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
]

# Optional risk/tradability columns. Missing triggers a warning, not a failure.
_OPTIONAL_RISK_COLUMNS: list[str] = [
    "is_limit_down",
    "is_suspended",
]

_DEFAULT_STATE_COLUMNS: list[str] = [
    "d1_state",
    "w1_state",
    "mn1_state",
    "state_hex_d1",
    "state_hex_w1",
    "state_hex_mn1",
    "ef_count",
    "ef_width",
]


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

class DuckDBBacktestDataProvider:
    """Loads and normalizes market data from DuckDB for backtesting.

    Args:
        foundation_db: Path to p116_foundation.duckdb (or test fixture).
        state_cube_db: Optional path to state_cube.duckdb. If None,
            state data is loaded from foundation_db or skipped.
    """

    def __init__(
        self,
        foundation_db: Path,
        state_cube_db: Path | None = None,
    ) -> None:
        self.foundation_db = Path(foundation_db)
        self.state_cube_db = Path(state_cube_db) if state_cube_db else None

    def load(self, request: MarketDataRequest) -> MarketDataBundle:
        """Load market data from DuckDB and return a normalized bundle.

        Raises:
            FileNotFoundError: If foundation_db does not exist.
            ValueError: If required columns are missing after loading.
        """
        if not self.foundation_db.exists():
            raise FileNotFoundError(
                f"Foundation DB not found: {self.foundation_db}"
            )

        warnings: list[str] = []
        source_summary: dict[str, Any] = {}

        # Load daily bars
        bars = self._load_daily_bars(request, source_summary)

        # Join state data if requested
        if request.include_state:
            bars, state_warnings = self._join_state_data(bars, request)
            warnings.extend(state_warnings)

        # Normalize column names
        bars = self._normalize_columns(bars)

        # Validate required columns
        missing_required = [
            c for c in _REQUIRED_BASE_COLUMNS if c not in bars.columns
        ]
        if missing_required:
            raise ValueError(
                f"BT_MISSING_REQUIRED_COLUMN: {missing_required}"
            )

        # Check DSL-requested required columns
        missing_dsl = [
            c for c in request.required_columns
            if c not in bars.columns
        ]
        if missing_dsl:
            # volume_ratio alternate group: if volume_ma_N is missing but
            # volume_ratio (pre-computed) exists in bars, the engine can use
            # the pre-computed column instead.
            _volume_alt_ok = (
                any(c.startswith("volume_ma_") for c in missing_dsl)
                and "volume_ratio" in bars.columns
            )
            if _volume_alt_ok:
                missing_dsl = [
                    c for c in missing_dsl
                    if not c.startswith("volume_ma_")
                ]

            # state_ef_count fallback: ef_count is not always present in real
            # state_cube databases. Add a null placeholder column and warn so
            # the strategy can still run (the condition simply evaluates to
            # false) rather than failing the entire backtest.
            if "ef_count" in missing_dsl:
                missing_dsl = [c for c in missing_dsl if c != "ef_count"]
                bars = bars.with_columns(pl.lit(None).cast(pl.Int64).alias("ef_count"))
                warnings.append("BT_STATE_EF_COUNT_UNAVAILABLE: ef_count not present in state_cube; state_ef_count conditions will evaluate to false")

            # Separate mandatory vs optional
            mandatory_missing = [
                c for c in missing_dsl
                if c not in _OPTIONAL_RISK_COLUMNS
            ]
            optional_missing = [
                c for c in missing_dsl
                if c in _OPTIONAL_RISK_COLUMNS
            ]
            if mandatory_missing:
                raise ValueError(
                    f"BT_MISSING_REQUIRED_COLUMN: {mandatory_missing}"
                )
            for col in optional_missing:
                warnings.append(f"BT_OPTIONAL_COLUMN_MISSING: {col}")

        # Check optional risk columns
        for col in _OPTIONAL_RISK_COLUMNS:
            if col not in bars.columns:
                if col not in [c for c in request.required_columns if c in _OPTIONAL_RISK_COLUMNS]:
                    warnings.append(f"BT_OPTIONAL_RISK_COLUMN_ABSENT: {col}")

        data_version = self._compute_data_version(source_summary)

        return MarketDataBundle(
            bars=bars,
            data_version=data_version,
            warnings=warnings,
            source_summary=source_summary,
        )

    # ------------------------------------------------------------------
    # Internal Loaders
    # ------------------------------------------------------------------

    def _load_daily_bars(
        self,
        request: MarketDataRequest,
        source_summary: dict[str, Any],
    ) -> pl.DataFrame:
        """Load daily_bars from foundation DuckDB."""
        con = connect_duckdb(str(self.foundation_db), read_only=True)
        try:
            # Discover available tables
            tables = con.execute(
                "SELECT table_name FROM information_schema.tables"
            ).fetchall()
            table_names = [t[0] for t in tables]

            if "daily_bars" not in table_names:
                raise ValueError(
                    "BT_MISSING_REQUIRED_TABLE: daily_bars not found in "
                    f"{self.foundation_db}"
                )

            available_columns = self._table_columns(con, "daily_bars")
            select_columns = self._resolve_daily_select_columns(
                available_columns,
                request.required_columns,
            )
            select_sql = ", ".join(self._quote_identifier(c) for c in select_columns)

            # Build query with date filter
            sql = f"""
                SELECT {select_sql}
                FROM daily_bars
                WHERE date >= ? AND date <= ?
            """
            params: list[Any] = [request.start_date, request.end_date]

            if request.universe:
                placeholders = ", ".join(["?"] * len(request.universe))
                sql += f" AND symbol IN ({placeholders})"
                params.extend(request.universe)

            sql += " ORDER BY date, symbol"

            result = con.execute(sql, params)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            df = pl.DataFrame(rows, schema=columns, orient="row")
            source_summary["daily_bars_rows"] = len(df)
            source_summary["daily_bars_columns"] = list(df.columns)
            source_summary["daily_bars_db"] = str(self.foundation_db)

            if len(df) > 0:
                source_summary["date_min"] = str(df["date"].min())
                source_summary["date_max"] = str(df["date"].max())
                source_summary["symbols"] = sorted(df["symbol"].unique().to_list())

            return df
        finally:
            con.close()

    def _join_state_data(
        self,
        bars: pl.DataFrame,
        request: MarketDataRequest,
    ) -> tuple[pl.DataFrame, list[str]]:
        """Join state_cube data onto bars. Returns (bars, warnings)."""
        warnings: list[str] = []

        db_path = self.state_cube_db or self.foundation_db
        if not db_path.exists():
            warnings.append(f"BT_STATE_DB_NOT_FOUND: {db_path}")
            return bars, warnings

        con = connect_duckdb(str(db_path), read_only=True)
        try:
            tables = con.execute(
                "SELECT table_name FROM information_schema.tables"
            ).fetchall()
            table_names = [t[0] for t in tables]

            if "state_cube" not in table_names:
                # Try the foundation DB if state_cube_db was different
                if self.state_cube_db and self.state_cube_db != self.foundation_db:
                    con2 = connect_duckdb(str(self.foundation_db), read_only=True)
                    try:
                        tables2 = con2.execute(
                            "SELECT table_name FROM information_schema.tables"
                        ).fetchall()
                        if "state_cube" in [t[0] for t in tables2]:
                            con.close()
                            con = con2
                            table_names = [t[0] for t in tables2]
                        else:
                            con2.close()
                            warnings.append("BT_STATE_CUBE_TABLE_NOT_FOUND")
                            return bars, warnings
                    except Exception:
                        con2.close()
                        warnings.append("BT_STATE_CUBE_TABLE_NOT_FOUND")
                        return bars, warnings
                else:
                    warnings.append("BT_STATE_CUBE_TABLE_NOT_FOUND")
                    return bars, warnings

            available_columns = self._table_columns(con, "state_cube")
            select_columns = self._resolve_state_select_columns(
                available_columns,
                request.required_columns,
            )
            select_sql = ", ".join(self._quote_identifier(c) for c in select_columns)

            sql = """
                SELECT {select_sql}
                FROM state_cube
                WHERE date >= ? AND date <= ?
            """.format(select_sql=select_sql)
            params: list[Any] = [request.start_date, request.end_date]

            if request.universe:
                placeholders = ", ".join(["?"] * len(request.universe))
                sql += f" AND symbol IN ({placeholders})"
                params.extend(request.universe)

            sql += " ORDER BY date, symbol"

            result = con.execute(sql, params)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            state_df = pl.DataFrame(rows, schema=columns, orient="row")

            if len(state_df) == 0:
                warnings.append("BT_STATE_CUBE_EMPTY: no state data in range")
                return bars, warnings

            # Determine join columns
            join_cols = ["symbol", "date"]
            # Avoid duplicate columns after join
            state_cols_to_add = [
                c for c in state_df.columns
                if c not in bars.columns and c not in join_cols
            ]

            if state_cols_to_add:
                state_select = state_df.select(join_cols + state_cols_to_add)
                bars = bars.join(state_select, on=join_cols, how="left")

            return bars, warnings
        finally:
            con.close()

    @staticmethod
    def _table_columns(con: duckdb.DuckDBPyConnection, table_name: str) -> list[str]:
        """Return column names for a known table."""
        rows = con.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = ?
            ORDER BY ordinal_position
            """,
            [table_name],
        ).fetchall()
        return [r[0] for r in rows]

    @classmethod
    def _resolve_daily_select_columns(
        cls,
        available_columns: list[str],
        required_columns: list[str],
    ) -> list[str]:
        """Resolve whitelisted daily_bars columns needed for a request."""
        available = set(available_columns)
        selected: list[str] = []

        def add(col: str) -> None:
            if col in available and col not in selected:
                selected.append(col)

        for col in _REQUIRED_BASE_COLUMNS:
            add(col)
        for col in ["is_limit_up", *_OPTIONAL_RISK_COLUMNS]:
            add(col)

        for col in required_columns:
            for candidate in cls._daily_source_candidates(col):
                add(candidate)

        return selected

    @classmethod
    def _resolve_state_select_columns(
        cls,
        available_columns: list[str],
        required_columns: list[str],
    ) -> list[str]:
        """Resolve whitelisted state_cube columns needed for a request."""
        available = set(available_columns)
        selected: list[str] = []

        def add(col: str) -> None:
            if col in available and col not in selected:
                selected.append(col)

        add("symbol")
        add("date")
        for col in _DEFAULT_STATE_COLUMNS:
            add(col)
        for col in required_columns:
            for candidate in cls._state_source_candidates(col):
                add(candidate)

        return selected

    @staticmethod
    def _daily_source_candidates(column: str) -> list[str]:
        """Map normalized/registry columns to possible daily_bars source columns."""
        if column in {"symbol", "date"}:
            return [column]
        if column.endswith("_d1"):
            base = column.removesuffix("_d1")
            return [base, column]
        if column in {"state_hex_d1", "state_hex_w1", "state_hex_mn1"}:
            return []
        if column in {"d1_state", "w1_state", "mn1_state", "ef_count", "ef_width"}:
            return []
        # volume_ratio alternate group: volume_ma_N can be substituted by
        # the pre-computed volume_ratio column.
        if column.startswith("volume_ma_"):
            return [column, "volume_ratio"]
        if column == "volume_ratio":
            return ["volume_ratio"]
            # Also try any volume_ma_N columns that may exist
            # (handled by the reverse mapping above)
        return [column]

    @staticmethod
    def _state_source_candidates(column: str) -> list[str]:
        """Map normalized/registry columns to possible state_cube source columns."""
        aliases = {
            "d1_state": ["d1_state", "state_hex_d1"],
            "w1_state": ["w1_state", "state_hex_w1"],
            "mn1_state": ["mn1_state", "state_hex_mn1"],
            "state_hex_d1": ["state_hex_d1", "d1_state"],
            "state_hex_w1": ["state_hex_w1", "w1_state"],
            "state_hex_mn1": ["state_hex_mn1", "mn1_state"],
        }
        return aliases.get(column, [column])

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        """Quote a DuckDB identifier from discovered schema metadata."""
        return '"' + identifier.replace('"', '""') + '"'

    @staticmethod
    def _normalize_columns(df: pl.DataFrame) -> pl.DataFrame:
        """Rename source columns to normalized engine-expected names."""
        rename_map: dict[str, str] = {}
        for src, dst in _STATE_COLUMN_ALIASES.items():
            if src in df.columns and dst not in df.columns:
                rename_map[src] = dst
        if rename_map:
            df = df.rename(rename_map)

        # Add reverse aliases so engine/translator expressions that reference
        # source names (e.g. state_hex_d1) still work when the raw data only
        # provides normalized names (e.g. d1_state).
        for src, dst in _STATE_REVERSE_ALIASES.items():
            if src in df.columns and dst not in df.columns:
                df = df.with_columns(pl.col(src).alias(dst))

        # Add D1 timeframe aliases: close_d1 = close, ma_N_d1 = ma_N
        # This ensures columns resolved with D1 suffix are available.
        if "close" in df.columns and "close_d1" not in df.columns:
            df = df.with_columns(pl.col("close").alias("close_d1"))

        # Add aliases for MA columns: ma_N -> ma_N_d1
        for col in list(df.columns):
            if col.startswith("ma_") and not col.endswith("_d1") and not col.endswith("_w1") and not col.endswith("_mn1"):
                alias = f"{col}_d1"
                if alias not in df.columns:
                    df = df.with_columns(pl.col(col).alias(alias))

        return df

    @staticmethod
    def _compute_data_version(source_summary: dict[str, Any]) -> str:
        """Compute a data version string from source metadata."""
        db = source_summary.get("daily_bars_db", "unknown")
        date_min = source_summary.get("date_min", "?")
        date_max = source_summary.get("date_max", "?")
        rows = source_summary.get("daily_bars_rows", 0)
        return f"{Path(db).stem}:{date_min}..{date_max}:rows={rows}"
