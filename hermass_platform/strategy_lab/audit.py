"""Audit - Minimal audit logger for strategy lifecycle.

Records every generation, validation, preview, and backtest operation
with trace_id, hashes, and red_line_result for full observability.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from ._duckdb_helper import connect_duckdb


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AuditRecord:
    """A single audit log entry."""

    trace_id: str
    operation: str
    strategy_id: str
    dsl_version: str
    input_hash: str
    output_hash: str
    red_line_result: dict[str, Any]
    created_at: str = ""


# ---------------------------------------------------------------------------
# Audit Logger
# ---------------------------------------------------------------------------

class StrategyAuditLogger:
    """Minimal DuckDB audit logger.

    Must record:
        trace_id, operation, strategy_id, dsl_version,
        input_hash, output_hash, red_line_result, created_at
    """

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
        """Create audit table if it does not exist."""
        con = self._connect()
        con.execute(
            """
            CREATE SEQUENCE IF NOT EXISTS seq_audit_id START 1;
            CREATE TABLE IF NOT EXISTS strategy_audit_log (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_audit_id'),
                trace_id VARCHAR NOT NULL,
                operation VARCHAR NOT NULL,
                strategy_id VARCHAR NOT NULL,
                dsl_version VARCHAR NOT NULL,
                input_hash VARCHAR NOT NULL,
                output_hash VARCHAR NOT NULL,
                red_line_result JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    @staticmethod
    def _hash_payload(payload: dict[str, Any]) -> str:
        """Stable SHA-256 hash truncated to 16 hex chars."""
        data = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]

    def _insert(
        self,
        trace_id: str,
        operation: str,
        strategy_id: str,
        dsl_version: str,
        input_hash: str,
        output_hash: str,
        red_line_result: dict[str, Any],
    ) -> None:
        con = self._connect()
        con.execute(
            """
            INSERT INTO strategy_audit_log
                (trace_id, operation, strategy_id, dsl_version,
                 input_hash, output_hash, red_line_result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                trace_id,
                operation,
                strategy_id,
                dsl_version,
                input_hash,
                output_hash,
                json.dumps(red_line_result, sort_keys=True, ensure_ascii=False, separators=(",", ":")),
            ],
        )

    def log_generation(
        self,
        trace_id: str,
        strategy_id: str,
        dsl_version: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
        red_line_result: dict[str, Any] | None = None,
    ) -> None:
        """Log a strategy generation event."""
        self._insert(
            trace_id=trace_id,
            operation="generation",
            strategy_id=strategy_id,
            dsl_version=dsl_version,
            input_hash=self._hash_payload(input_payload),
            output_hash=self._hash_payload(output_payload),
            red_line_result=red_line_result or {},
        )

    def log_validation(
        self,
        trace_id: str,
        strategy_id: str,
        dsl_version: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
        red_line_result: dict[str, Any] | None = None,
    ) -> None:
        """Log a validation event."""
        self._insert(
            trace_id=trace_id,
            operation="validation",
            strategy_id=strategy_id,
            dsl_version=dsl_version,
            input_hash=self._hash_payload(input_payload),
            output_hash=self._hash_payload(output_payload),
            red_line_result=red_line_result or {},
        )

    def log_preview(
        self,
        trace_id: str,
        strategy_id: str,
        dsl_version: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
        red_line_result: dict[str, Any] | None = None,
    ) -> None:
        """Log a preview event."""
        self._insert(
            trace_id=trace_id,
            operation="preview",
            strategy_id=strategy_id,
            dsl_version=dsl_version,
            input_hash=self._hash_payload(input_payload),
            output_hash=self._hash_payload(output_payload),
            red_line_result=red_line_result or {},
        )

    def log_backtest(
        self,
        trace_id: str,
        strategy_id: str,
        dsl_version: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
        red_line_result: dict[str, Any] | None = None,
    ) -> None:
        """Log a backtest event."""
        self._insert(
            trace_id=trace_id,
            operation="backtest",
            strategy_id=strategy_id,
            dsl_version=dsl_version,
            input_hash=self._hash_payload(input_payload),
            output_hash=self._hash_payload(output_payload),
            red_line_result=red_line_result or {},
        )

    def list_by_trace_id(self, trace_id: str) -> list[AuditRecord]:
        """Retrieve all audit records for a trace_id."""
        con = self._connect()
        rows = con.execute(
            """
            SELECT trace_id, operation, strategy_id, dsl_version,
                   input_hash, output_hash, red_line_result, created_at
            FROM strategy_audit_log
            WHERE trace_id = ?
            ORDER BY created_at ASC
            """,
            [trace_id],
        ).fetchall()
        return [
            AuditRecord(
                trace_id=r[0],
                operation=r[1],
                strategy_id=r[2],
                dsl_version=r[3],
                input_hash=r[4],
                output_hash=r[5],
                red_line_result=json.loads(r[6]),
                created_at=str(r[7]) if r[7] else "",
            )
            for r in rows
        ]
