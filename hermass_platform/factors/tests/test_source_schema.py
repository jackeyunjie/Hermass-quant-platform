"""Tests for source_schema.py — 8 test points."""

import pytest
from datetime import datetime

from hermass_platform.factors.source_schema import (
    SourceType,
    FactorSource,
    Evidence,
    EvidenceType,
    EvidenceStatus,
    ValidationStatus,
    MetricRef,
    EvidenceLevel,
)
from hermass_platform.factors.exceptions import SourceValidationError


class TestSourceType:
    """1. Test canonical source_type values (decision 0009)."""

    def test_all_canonical_values_present(self):
        expected = {
            "strategy_generator",
            "open_quant_framework",
            "institutional_factor",
            "academic_literature",
            "fundamental_data",
            "news_sentiment",
            "money_flow",
            "trader_methodology",
            "behavioral_factor",
            "hermass_native",
        }
        actual = {m.value for m in SourceType}
        assert actual == expected

    def test_source_type_enum_membership(self):
        assert SourceType.STRATEGY_GENERATOR == "strategy_generator"
        assert SourceType.HERMASS_NATIVE == "hermass_native"


class TestFactorSource:
    """2. Test FactorSource model validation."""

    def test_valid_source(self):
        src = FactorSource(
            source_id="test_src",
            name="Test Source",
            source_type=SourceType.OPEN_QUANT_FRAMEWORK,
            url_or_local_ref="https://example.com",
            applicable_markets=["A_SHARE"],
        )
        assert src.source_id == "test_src"
        assert src.source_type == SourceType.OPEN_QUANT_FRAMEWORK

    def test_empty_applicable_markets_raises(self):
        with pytest.raises(ValueError):
            FactorSource(
                source_id="bad_src",
                name="Bad",
                source_type=SourceType.ACADEMIC_LITERATURE,
                applicable_markets=[],
            )

    def test_source_type_from_string(self):
        src = FactorSource(
            source_id="str_src",
            name="String Source",
            source_type="fundamental_data",
            applicable_markets=["A_SHARE"],
        )
        assert src.source_type == SourceType.FUNDAMENTAL_DATA

    def test_legacy_url_field_synced(self):
        src = FactorSource(
            source_id="legacy_src",
            name="Legacy",
            source_type=SourceType.STRATEGY_GENERATOR,
            url="https://legacy.example.com",
            applicable_markets=["A_SHARE"],
        )
        assert src.url_or_local_ref == "https://legacy.example.com"


class TestEvidence:
    """3. Test Evidence model."""

    def test_valid_evidence(self):
        ev = Evidence(
            evidence_id="ev_001",
            target_id="fac_001",
            target_type="factor",
            evidence_type=EvidenceType.BACKTEST,
            evidence_level=EvidenceLevel.E2,
            validation_status=ValidationStatus.PASSED,
        )
        assert ev.evidence_level == EvidenceLevel.E2
        assert ev.validation_status == ValidationStatus.PASSED

    def test_evidence_with_metrics(self):
        ev = Evidence(
            evidence_id="ev_002",
            target_id="fac_001",
            target_type="factor",
            evidence_type=EvidenceType.BACKTEST,
            evidence_level=EvidenceLevel.E3,
            validation_status=ValidationStatus.PASSED,
            metric_refs=[
                MetricRef(metric="sharpe", value=1.5, window="2024")
            ],
        )
        assert len(ev.metric_refs) == 1
        assert ev.metric_refs[0].value == 1.5

    def test_legacy_source_id_synced(self):
        ev = Evidence(
            evidence_id="ev_003",
            source_id="src_001",
            evidence_type=EvidenceType.BACKTEST,
            evidence_level=EvidenceLevel.E2,
            validation_status=ValidationStatus.PASSED,
        )
        assert ev.target_id == "src_001"

    def test_evidence_level_ordering(self):
        assert EvidenceLevel.E0 < EvidenceLevel.E1 < EvidenceLevel.E2 < EvidenceLevel.E3 < EvidenceLevel.E4 < EvidenceLevel.E5 < EvidenceLevel.E6
