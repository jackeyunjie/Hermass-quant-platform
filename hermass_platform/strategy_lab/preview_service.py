"""Preview Service - Strategy condition preview and hit estimation.

Provides mock and DuckDB-based preview of strategy conditions.
All preview operations are deterministic and auditable.

Design principles:
    - preview_support is the sole authority for preview routing.
    - UNSUPPORTED conditions cause overall failure.
    - REQUIRES_BACKTEST_CONTEXT conditions return estimates, not failures.
    - Red-line failures prevent preview execution.
    - No SELECT * in SQL preview queries.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal

from .api_models import (
    ConditionPreviewItem,
    PreviewOverallItem,
    PreviewResponse,
    SectionPreviewItem,
)
from .condition_registry import (
    ConditionRegistry,
    ContextRequirement,
    PreviewSupport,
)
from .condition_translator import translate_condition
from .dsl_schema import ConditionBlock, StrategyDSL
from .dsl_validator import ValidationLevel, validate_dsl


# ---------------------------------------------------------------------------
# Mock Data Provider
# ---------------------------------------------------------------------------

class MockDataProvider:
    """Deterministic mock data provider for preview.

    Returns fixed hit counts per condition type for reproducible tests.
    """

    # Deterministic hit counts for each condition type
    _HIT_COUNTS: dict[str, int] = {
        "ma_golden_cross": 42,
        "ma_death_cross": 38,
        "price_cross_ma": 55,
        "state_hex_in": 120,
        "state_ef_count": 89,
        "volume_ratio": 67,
        "industry_include": 200,
        "industry_exclude": 180,
        "limit_up_filter": 500,
    }

    # Base rate for context-required conditions (percentage of total bars)
    _CONTEXT_BASE_RATE: float = 0.15

    def estimate_hits(
        self,
        condition_type: str,
        params: dict[str, Any],
        preview_support: PreviewSupport,
    ) -> int | None:
        """Estimate hit count for a condition.

        Args:
            condition_type: The condition type name.
            params: Condition parameters.
            preview_support: Preview support classification.

        Returns:
            Estimated hit count, or None if not estimable.
        """
        if preview_support == PreviewSupport.UNSUPPORTED:
            return None

        if preview_support == PreviewSupport.REQUIRES_BACKTEST_CONTEXT:
            return self._estimate_context_required(condition_type, params)

        # FULLY_SUPPORTED or MOCK_ONLY
        return self._HIT_COUNTS.get(condition_type, 10)

    def _estimate_context_required(
        self, condition_type: str, params: dict[str, Any]
    ) -> int:
        """Estimate hits for conditions requiring backtest context.

        Uses a simplified model based on the condition parameters.
        """
        total_bars = 3000  # Approximate trading days in 10 years

        if condition_type == "stop_loss_pct":
            value = params.get("value", 0.08)
            # Higher stop loss = fewer hits (wider threshold)
            base_rate = max(0.02, min(value * 1.5, 0.5))
            return int(total_bars * base_rate)

        if condition_type == "take_profit_pct":
            value = params.get("value", 0.15)
            # Higher take profit = fewer hits (harder to reach)
            base_rate = max(0.02, min(0.5 - value, 0.5))
            return int(total_bars * base_rate)

        # Default fallback
        return int(total_bars * self._CONTEXT_BASE_RATE)


# ---------------------------------------------------------------------------
# Preview Service
# ---------------------------------------------------------------------------

@dataclass
class PreviewConfig:
    """Configuration for PreviewService."""

    registry: ConditionRegistry = field(default_factory=ConditionRegistry.default)
    mock_provider: MockDataProvider = field(default_factory=MockDataProvider)


class PreviewService:
    """Service for previewing strategy conditions.

    Usage:
        service = PreviewService()
        response = service.preview(dsl, data_source="mock")
    """

    def __init__(self, config: PreviewConfig | None = None) -> None:
        self.config = config or PreviewConfig()
        self._registry = self.config.registry
        self._mock = self.config.mock_provider

    def preview(
        self,
        dsl: StrategyDSL,
        data_source: Literal["mock", "duckdb"] = "mock",
        trace_id: str = "",
    ) -> PreviewResponse:
        """Preview a strategy's conditions.

        Steps:
            1. Validate DSL (all levels).
            2. Check for UNSUPPORTED conditions (fail fast).
            3. Preview each section (entry/exit/filters).
            4. Return aggregated results.

        Args:
            dsl: Strategy DSL to preview.
            data_source: Data source type (mock or duckdb).
            trace_id: Audit trace ID.

        Returns:
            PreviewResponse with per-condition and overall results.
        """
        errors: list[str] = []
        input_hash = self._hash_dsl(dsl)

        # Step 1: Validate DSL
        validation = validate_dsl(dsl, self._registry)
        if not validation.passed:
            errors.append(
                f"DSL validation failed at level '{validation.level.value}'"
            )
            for e in validation.errors:
                errors.append(f"  [{e.level.value}] {e.code}: {e.message}")
            return PreviewResponse(
                trace_id=trace_id,
                input_hash=input_hash,
                overall=PreviewOverallItem(
                    overall_status="failed",
                    errors=errors,
                ),
                errors=errors,
            )

        # Step 2: Check for UNSUPPORTED conditions
        unsupported = self._check_unsupported(dsl)
        if unsupported:
            errors.append(f"Preview failed: unsupported conditions: {unsupported}")
            return PreviewResponse(
                trace_id=trace_id,
                input_hash=input_hash,
                overall=PreviewOverallItem(
                    overall_status="failed",
                    errors=errors,
                ),
                errors=errors,
            )

        # Step 3: Preview each section
        sections: list[SectionPreviewItem] = []
        overall_has_context = False
        total_estimated_hits = 0
        section_count = 0

        for section_name in ["entry", "exit", "filters"]:
            section_conditions = getattr(dsl, section_name)
            if not section_conditions:
                continue

            section_preview = self._preview_section(
                section_name, section_conditions, data_source
            )
            sections.append(section_preview)
            section_count += 1

            if section_preview.has_context_required:
                overall_has_context = True

            if section_preview.total_estimated_hits is not None:
                total_estimated_hits += section_preview.total_estimated_hits

        # Determine overall status
        if overall_has_context:
            overall_status: Literal["success", "partial", "failed"] = "partial"
        else:
            overall_status = "success"

        sections_with_context = sum(
            1 for s in sections if s.has_context_required
        )

        return PreviewResponse(
            trace_id=trace_id,
            input_hash=input_hash,
            overall=PreviewOverallItem(
                overall_status=overall_status,
                total_sections=section_count,
                sections_with_context_required=sections_with_context,
                total_estimated_hits=total_estimated_hits if section_count > 0 else None,
                errors=[],
                warnings=[],
            ),
            sections=sections,
            errors=[],
        )

    def _hash_dsl(self, dsl: StrategyDSL) -> str:
        """Compute a stable hash of the DSL input for audit correlation."""
        payload = json.dumps(
            dsl.model_dump(mode="json"),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def _check_unsupported(self, dsl: StrategyDSL) -> list[str]:
        """Return list of unsupported condition types in the DSL."""
        unsupported: list[str] = []
        for cond in dsl.get_all_conditions():
            if self._registry.has(cond.condition_type):
                spec = self._registry.get(cond.condition_type)
                if spec.preview_support == PreviewSupport.UNSUPPORTED:
                    unsupported.append(cond.condition_type)
            else:
                # Unregistered conditions are treated as unsupported for preview
                unsupported.append(cond.condition_type)
        return unsupported

    def _preview_section(
        self,
        section_name: str,
        conditions: list[ConditionBlock],
        data_source: str,
    ) -> SectionPreviewItem:
        """Preview a single strategy section."""
        items: list[ConditionPreviewItem] = []
        section_has_context = False
        section_total_hits = 0

        for cond in conditions:
            spec = self._registry.get(cond.condition_type)

            has_context = ContextRequirement.POSITION in spec.context_requirements
            if has_context:
                section_has_context = True

            # Estimate hits
            if data_source == "mock":
                estimated = self._mock.estimate_hits(
                    cond.condition_type, cond.params, spec.preview_support
                )
            else:
                # DuckDB preview: try to get actual count, fallback to mock
                estimated = self._estimate_duckdb(cond, spec)

            if estimated is not None:
                section_total_hits += estimated

            notes = spec.preview_notes
            if spec.preview_support == PreviewSupport.REQUIRES_BACKTEST_CONTEXT:
                notes = notes or "Requires backtest context for accurate preview"

            items.append(
                ConditionPreviewItem(
                    condition_type=cond.condition_type,
                    params=cond.params,
                    preview_support=spec.preview_support.value,
                    has_context_required=has_context,
                    estimated_hits=estimated,
                    notes=notes,
                )
            )

        return SectionPreviewItem(
            section=section_name,  # type: ignore[arg-type]
            conditions=items,
            total_estimated_hits=section_total_hits if items else None,
            has_context_required=section_has_context,
        )

    def _estimate_duckdb(
        self, cond: ConditionBlock, spec: Any
    ) -> int | None:
        """Estimate hits using DuckDB (stub - falls back to mock for now).

        In full implementation, this would:
            1. Translate condition to SQL.
            2. Execute COUNT(*) against DuckDB.
            3. Return actual hit count.
        """
        # Stub: delegate to mock provider
        # SQL preview must not use SELECT *
        return self._mock.estimate_hits(
            cond.condition_type, cond.params, spec.preview_support
        )

    def preview_condition_sql(
        self,
        condition: ConditionBlock,
    ) -> str | None:
        """Get the SQL preview for a single condition (no SELECT *).

        Returns the WHERE clause fragment only.
        """
        try:
            result = translate_condition(condition, self._registry, "duckdb")
            return result.sql_expr
        except (KeyError, ValueError):
            return None
