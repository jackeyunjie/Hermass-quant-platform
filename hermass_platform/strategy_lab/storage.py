"""Storage - Minimal DuckDB persistence for strategies and backtests.

Tables:
    user_strategies      - strategy identity and latest metadata
    strategy_versions    - every DSL snapshot with hashes
    strategy_backtests   - backtest results linked to versions
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class StrategyVersion:
    """A persisted strategy version."""

    strategy_id: str
    dsl: dict[str, Any]
    trace_id: str
    input_hash: str
    output_hash: str
    created_at: str = ""


@dataclass
class BacktestResult:
    """A persisted backtest result."""

    strategy_id: str
    trace_id: str
    status: str
    metrics: dict[str, Any]
    dsl_snapshot: dict[str, Any] | None
    created_at: str = ""


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

class StrategyLabStorage:
    """Minimal DuckDB storage for strategies and backtests."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._con = None

    def _connect(self):
        if self._con is not None:
            return self._con
        import duckdb

        self._con = duckdb.connect(self.db_path)
        return self._con

    def close(self) -> None:
        if self._con is not None:
            self._con.close()
            self._con = None

    def init_schema(self) -> None:
        """Create tables if they do not exist."""
        con = self._connect()
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS user_strategies (
                strategy_id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        con.execute(
            """
            CREATE SEQUENCE IF NOT EXISTS seq_version_id START 1;
            CREATE TABLE IF NOT EXISTS strategy_versions (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_version_id'),
                strategy_id VARCHAR NOT NULL,
                dsl JSON NOT NULL,
                trace_id VARCHAR NOT NULL,
                input_hash VARCHAR NOT NULL,
                output_hash VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES user_strategies(strategy_id)
            )
            """
        )
        con.execute(
            """
            CREATE SEQUENCE IF NOT EXISTS seq_backtest_id START 1;
            CREATE TABLE IF NOT EXISTS strategy_backtests (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_backtest_id'),
                strategy_id VARCHAR NOT NULL,
                trace_id VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                metrics JSON NOT NULL,
                dsl_snapshot JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES user_strategies(strategy_id)
            )
            """
        )

    def save_strategy_version(
        self,
        strategy_id: str,
        dsl: dict[str, Any],
        trace_id: str,
        input_hash: str,
        output_hash: str,
    ) -> None:
        """Persist a strategy version."""
        con = self._connect()
        # Upsert user_strategies row
        name = dsl.get("name", "")
        description = dsl.get("description", "")
        con.execute(
            """
            INSERT INTO user_strategies (strategy_id, name, description)
            VALUES (?, ?, ?)
            ON CONFLICT (strategy_id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                updated_at = now()
            """,
            [strategy_id, name, description],
        )
        con.execute(
            """
            INSERT INTO strategy_versions
                (strategy_id, dsl, trace_id, input_hash, output_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                strategy_id,
                json.dumps(dsl, sort_keys=True, ensure_ascii=False, separators=(",", ":")),
                trace_id,
                input_hash,
                output_hash,
            ],
        )

    def save_backtest_result(
        self,
        strategy_id: str,
        trace_id: str,
        status: str,
        metrics: dict[str, Any],
        dsl_snapshot: dict[str, Any] | None = None,
    ) -> None:
        """Persist a backtest result."""
        con = self._connect()
        con.execute(
            """
            INSERT INTO strategy_backtests
                (strategy_id, trace_id, status, metrics, dsl_snapshot)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                strategy_id,
                trace_id,
                status,
                json.dumps(metrics, sort_keys=True, ensure_ascii=False, separators=(",", ":")),
                json.dumps(dsl_snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                if dsl_snapshot is not None
                else None,
            ],
        )

    def get_strategy_versions(self, strategy_id: str) -> list[StrategyVersion]:
        """Retrieve all versions for a strategy."""
        con = self._connect()
        rows = con.execute(
            """
            SELECT strategy_id, dsl, trace_id, input_hash, output_hash, created_at
            FROM strategy_versions
            WHERE strategy_id = ?
            ORDER BY created_at DESC
            """,
            [strategy_id],
        ).fetchall()
        return [
            StrategyVersion(
                strategy_id=r[0],
                dsl=json.loads(r[1]),
                trace_id=r[2],
                input_hash=r[3],
                output_hash=r[4],
                created_at=str(r[5]) if r[5] else "",
            )
            for r in rows
        ]

    def get_backtest(self, trace_id: str) -> BacktestResult | None:
        """Retrieve a backtest by trace_id."""
        con = self._connect()
        row = con.execute(
            """
            SELECT strategy_id, trace_id, status, metrics, dsl_snapshot, created_at
            FROM strategy_backtests
            WHERE trace_id = ?
            """,
            [trace_id],
        ).fetchone()
        if row is None:
            return None
        return BacktestResult(
            strategy_id=row[0],
            trace_id=row[1],
            status=row[2],
            metrics=json.loads(row[3]),
            dsl_snapshot=json.loads(row[4]) if row[4] else None,
            created_at=str(row[5]) if row[5] else "",
        )
