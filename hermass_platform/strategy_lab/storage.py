"""Storage - Minimal DuckDB persistence for strategies and backtests.

Tables:
    user_strategies      - strategy identity and latest metadata
    strategy_versions    - every DSL snapshot with hashes
    strategy_backtests   - backtest results linked to versions
    strategy_trades      - normalized trade-level records
    strategy_trade_events - entry/exit/hold evidence snapshots per trade
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ._duckdb_helper import connect_duckdb


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


@dataclass
class TradeRecord:
    """A normalized trade record linked to strategy and trace evidence."""

    trade_id: str
    strategy_id: str
    trace_id: str
    symbol: str
    side: str
    status: str
    entry_time: str
    entry_price: float | None = None
    exit_time: str | None = None
    exit_price: float | None = None
    quantity: float | None = None
    pnl: float | None = None
    pnl_pct: float | None = None
    created_at: str = ""


@dataclass
class TradeEventEvidence:
    """State and indicator evidence captured at entry/exit/hold events."""

    trade_id: str
    strategy_id: str
    trace_id: str
    symbol: str
    event_type: str
    event_time: str
    price: float | None
    timeframe_states: dict[str, Any]
    indicator_snapshot: dict[str, Any]
    triggered_conditions: list[dict[str, Any]]
    notes: str = ""
    event_id: int | None = None
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
        self._con = connect_duckdb(self.db_path)
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
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS strategy_trades (
                trade_id VARCHAR PRIMARY KEY,
                strategy_id VARCHAR NOT NULL,
                trace_id VARCHAR NOT NULL,
                symbol VARCHAR NOT NULL,
                side VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                entry_time TIMESTAMP NOT NULL,
                entry_price DOUBLE,
                exit_time TIMESTAMP,
                exit_price DOUBLE,
                quantity DOUBLE,
                pnl DOUBLE,
                pnl_pct DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES user_strategies(strategy_id)
            )
            """
        )
        con.execute(
            """
            CREATE SEQUENCE IF NOT EXISTS seq_trade_event_id START 1;
            CREATE TABLE IF NOT EXISTS strategy_trade_events (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_trade_event_id'),
                trade_id VARCHAR NOT NULL,
                strategy_id VARCHAR NOT NULL,
                trace_id VARCHAR NOT NULL,
                symbol VARCHAR NOT NULL,
                event_type VARCHAR NOT NULL,
                event_time TIMESTAMP NOT NULL,
                price DOUBLE,
                timeframe_states JSON NOT NULL,
                indicator_snapshot JSON NOT NULL,
                triggered_conditions JSON NOT NULL,
                notes VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trade_id) REFERENCES strategy_trades(trade_id),
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

    def get_strategy_version_by_trace_id(
        self, trace_id: str
    ) -> StrategyVersion | None:
        """Retrieve the strategy version associated with a trace_id."""
        con = self._connect()
        row = con.execute(
            """
            SELECT strategy_id, dsl, trace_id, input_hash, output_hash, created_at
            FROM strategy_versions
            WHERE trace_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [trace_id],
        ).fetchone()
        if row is None:
            return None
        return StrategyVersion(
            strategy_id=row[0],
            dsl=json.loads(row[1]),
            trace_id=row[2],
            input_hash=row[3],
            output_hash=row[4],
            created_at=str(row[5]) if row[5] else "",
        )

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

    def save_trade_record(
        self,
        *,
        trade_id: str,
        strategy_id: str,
        trace_id: str,
        symbol: str,
        side: str,
        status: str,
        entry_time: str,
        entry_price: float | None = None,
        exit_time: str | None = None,
        exit_price: float | None = None,
        quantity: float | None = None,
        pnl: float | None = None,
        pnl_pct: float | None = None,
    ) -> None:
        """Persist or update a normalized trade record.

        Trade records are intentionally separate from event snapshots. A trade
        can have one entry event, zero or more hold/snapshot events, and one
        exit event.
        """
        con = self._connect()
        con.execute(
            """
            INSERT INTO strategy_trades
                (trade_id, strategy_id, trace_id, symbol, side, status,
                 entry_time, entry_price, exit_time, exit_price, quantity, pnl, pnl_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (trade_id) DO UPDATE SET
                strategy_id = EXCLUDED.strategy_id,
                trace_id = EXCLUDED.trace_id,
                symbol = EXCLUDED.symbol,
                side = EXCLUDED.side,
                status = EXCLUDED.status,
                entry_time = EXCLUDED.entry_time,
                entry_price = EXCLUDED.entry_price,
                exit_time = EXCLUDED.exit_time,
                exit_price = EXCLUDED.exit_price,
                quantity = EXCLUDED.quantity,
                pnl = EXCLUDED.pnl,
                pnl_pct = EXCLUDED.pnl_pct
            """,
            [
                trade_id,
                strategy_id,
                trace_id,
                symbol,
                side,
                status,
                entry_time,
                entry_price,
                exit_time,
                exit_price,
                quantity,
                pnl,
                pnl_pct,
            ],
        )

    def save_trade_event_evidence(
        self,
        *,
        trade_id: str,
        strategy_id: str,
        trace_id: str,
        symbol: str,
        event_type: str,
        event_time: str,
        price: float | None,
        timeframe_states: dict[str, Any],
        indicator_snapshot: dict[str, Any],
        triggered_conditions: list[dict[str, Any]],
        notes: str = "",
    ) -> None:
        """Persist entry/exit/hold evidence with state and indicator snapshots."""
        con = self._connect()
        con.execute(
            """
            INSERT INTO strategy_trade_events
                (trade_id, strategy_id, trace_id, symbol, event_type, event_time, price,
                 timeframe_states, indicator_snapshot, triggered_conditions, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                trade_id,
                strategy_id,
                trace_id,
                symbol,
                event_type,
                event_time,
                price,
                json.dumps(
                    timeframe_states,
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                json.dumps(
                    indicator_snapshot,
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                json.dumps(
                    triggered_conditions,
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                notes,
            ],
        )

    def list_trades(
        self,
        *,
        strategy_id: str | None = None,
        trace_id: str | None = None,
    ) -> list[TradeRecord]:
        """List trade records filtered by strategy_id or trace_id."""
        con = self._connect()
        sql = """
            SELECT trade_id, strategy_id, trace_id, symbol, side, status,
                   entry_time, entry_price, exit_time, exit_price, quantity,
                   pnl, pnl_pct, created_at
            FROM strategy_trades
        """
        clauses: list[str] = []
        params: list[str] = []
        if strategy_id is not None:
            clauses.append("strategy_id = ?")
            params.append(strategy_id)
        if trace_id is not None:
            clauses.append("trace_id = ?")
            params.append(trace_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY entry_time ASC, trade_id ASC"

        rows = con.execute(sql, params).fetchall()
        return [
            TradeRecord(
                trade_id=r[0],
                strategy_id=r[1],
                trace_id=r[2],
                symbol=r[3],
                side=r[4],
                status=r[5],
                entry_time=str(r[6]) if r[6] else "",
                entry_price=r[7],
                exit_time=str(r[8]) if r[8] else None,
                exit_price=r[9],
                quantity=r[10],
                pnl=r[11],
                pnl_pct=r[12],
                created_at=str(r[13]) if r[13] else "",
            )
            for r in rows
        ]

    def list_backtests(
        self,
        *,
        strategy_id: str | None = None,
        trace_id: str | None = None,
    ) -> list[BacktestResult]:
        """List backtest results, optionally filtered by strategy_id or trace_id."""
        con = self._connect()
        sql = """
            SELECT strategy_id, trace_id, status, metrics, dsl_snapshot, created_at
            FROM strategy_backtests
        """
        clauses: list[str] = []
        params: list[str] = []
        if strategy_id is not None:
            clauses.append("strategy_id = ?")
            params.append(strategy_id)
        if trace_id is not None:
            clauses.append("trace_id = ?")
            params.append(trace_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at DESC"

        rows = con.execute(sql, params).fetchall()
        return [
            BacktestResult(
                strategy_id=r[0],
                trace_id=r[1],
                status=r[2],
                metrics=json.loads(r[3]),
                dsl_snapshot=json.loads(r[4]) if r[4] else None,
                created_at=str(r[5]) if r[5] else "",
            )
            for r in rows
        ]

    def list_trade_events(
        self,
        trade_id: str | None = None,
        *,
        trace_id: str | None = None,
    ) -> list[TradeEventEvidence]:
        """List entry/exit/hold evidence snapshots for a trade or trace.

        Args:
            trade_id: Filter by trade_id (legacy positional support).
            trace_id: Filter by trace_id.

        Raises:
            ValueError: If both trade_id and trace_id are provided, or neither.
        """
        if trade_id is not None and trace_id is not None:
            raise ValueError("Provide either trade_id or trace_id, not both")
        if trade_id is None and trace_id is None:
            raise ValueError("Provide either trade_id or trace_id")

        con = self._connect()
        if trade_id is not None:
            rows = con.execute(
                """
                SELECT id, trade_id, strategy_id, trace_id, symbol, event_type,
                       event_time, price, timeframe_states, indicator_snapshot,
                       triggered_conditions, notes, created_at
                FROM strategy_trade_events
                WHERE trade_id = ?
                ORDER BY event_time ASC, id ASC
                """,
                [trade_id],
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT id, trade_id, strategy_id, trace_id, symbol, event_type,
                       event_time, price, timeframe_states, indicator_snapshot,
                       triggered_conditions, notes, created_at
                FROM strategy_trade_events
                WHERE trace_id = ?
                ORDER BY event_time ASC, id ASC
                """,
                [trace_id],
            ).fetchall()
        return [
            TradeEventEvidence(
                event_id=r[0],
                trade_id=r[1],
                strategy_id=r[2],
                trace_id=r[3],
                symbol=r[4],
                event_type=r[5],
                event_time=str(r[6]) if r[6] else "",
                price=r[7],
                timeframe_states=json.loads(r[8]),
                indicator_snapshot=json.loads(r[9]),
                triggered_conditions=json.loads(r[10]),
                notes=r[11] or "",
                created_at=str(r[12]) if r[12] else "",
            )
            for r in rows
        ]
