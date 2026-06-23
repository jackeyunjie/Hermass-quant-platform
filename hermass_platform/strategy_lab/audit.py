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

    def init_onboarding_schema(self) -> None:
        """Create onboarding consent and diagnosis tables if they do not exist."""
        con = self._connect()
        con.execute(
            """
            CREATE SEQUENCE IF NOT EXISTS seq_onboarding_consent_id START 1;
            CREATE TABLE IF NOT EXISTS onboarding_consent (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_onboarding_consent_id'),
                trace_id VARCHAR NOT NULL,
                consent_version VARCHAR NOT NULL,
                agreed_items JSON NOT NULL,
                client_ip VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE SEQUENCE IF NOT EXISTS seq_onboarding_diagnosis_id START 1;
            CREATE TABLE IF NOT EXISTS onboarding_diagnosis (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_onboarding_diagnosis_id'),
                trace_id VARCHAR NOT NULL,
                answers JSON NOT NULL,
                scores JSON NOT NULL,
                recommended_level VARCHAR NOT NULL,
                selected_level VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE SEQUENCE IF NOT EXISTS seq_onboarding_feedback_id START 1;
            CREATE TABLE IF NOT EXISTS onboarding_feedback (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_onboarding_feedback_id'),
                trace_id VARCHAR NOT NULL,
                feedback_day INTEGER NOT NULL,
                primary_level VARCHAR NOT NULL,
                strategies_created INTEGER,
                blockers TEXT,
                red_line_helpful INTEGER,
                explainability INTEGER,
                nps INTEGER,
                usage_count INTEGER,
                modified_idea BOOLEAN,
                most_wanted_feature TEXT,
                most_wanted_improvement TEXT,
                would_pay TEXT,
                free_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def init_schema(self) -> None:
        """Create audit tables if they do not exist."""
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
        self.init_onboarding_schema()

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

    def log_onboarding_consent(
        self,
        trace_id: str,
        consent_version: str,
        agreed_items: dict[str, Any],
        client_ip: str | None = None,
    ) -> None:
        """Log an onboarding disclaimer consent event."""
        con = self._connect()
        con.execute(
            """
            INSERT INTO onboarding_consent
                (trace_id, consent_version, agreed_items, client_ip)
            VALUES (?, ?, ?, ?)
            """,
            [
                trace_id,
                consent_version,
                json.dumps(agreed_items, sort_keys=True, ensure_ascii=False, separators=(",", ":")),
                client_ip or "",
            ],
        )

    def log_onboarding_diagnosis(
        self,
        trace_id: str,
        answers: dict[str, Any],
        scores: dict[str, int],
        recommended_level: str,
        selected_level: str | None = None,
    ) -> None:
        """Log an onboarding H1/H2/H3 diagnosis event."""
        con = self._connect()
        con.execute(
            """
            INSERT INTO onboarding_diagnosis
                (trace_id, answers, scores, recommended_level, selected_level)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                trace_id,
                json.dumps(answers, sort_keys=True, ensure_ascii=False, separators=(",", ":")),
                json.dumps(scores, sort_keys=True, ensure_ascii=False, separators=(",", ":")),
                recommended_level,
                selected_level or "",
            ],
        )

    def log_onboarding_feedback(
        self,
        trace_id: str,
        feedback_day: int,
        primary_level: str,
        strategies_created: int | None = None,
        blockers: str | None = None,
        red_line_helpful: int | None = None,
        explainability: int | None = None,
        nps: int | None = None,
        usage_count: int | None = None,
        modified_idea: bool | None = None,
        most_wanted_feature: str | None = None,
        most_wanted_improvement: str | None = None,
        would_pay: str | None = None,
        free_text: str | None = None,
    ) -> None:
        """Log an M3 pilot feedback submission (day 7 or day 14)."""
        con = self._connect()
        con.execute(
            """
            INSERT INTO onboarding_feedback
                (trace_id, feedback_day, primary_level, strategies_created, blockers,
                 red_line_helpful, explainability, nps, usage_count, modified_idea,
                 most_wanted_feature, most_wanted_improvement, would_pay, free_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                trace_id,
                feedback_day,
                primary_level,
                strategies_created,
                blockers or "",
                red_line_helpful,
                explainability,
                nps,
                usage_count,
                modified_idea,
                most_wanted_feature or "",
                most_wanted_improvement or "",
                would_pay or "",
                free_text or "",
            ],
        )

    def list_feedback(
        self,
        feedback_day: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List onboarding feedback submissions for ops review."""
        con = self._connect()
        if feedback_day is not None:
            rows = con.execute(
                """
                SELECT * FROM onboarding_feedback
                WHERE feedback_day = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [feedback_day, limit],
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT * FROM onboarding_feedback
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [limit],
            ).fetchall()
        columns = [desc[0] for desc in con.description]
        return [dict(zip(columns, row)) for row in rows]

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
