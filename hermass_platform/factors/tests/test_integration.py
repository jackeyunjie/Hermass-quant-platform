"""Integration tests — 8 test points."""

import pytest

from hermass_platform.factors.catalog_loader import CatalogLoader
from hermass_platform.factors.registry import (
    SourceRegistry, FactorRegistry, BlockRegistry, EvidenceRegistry, RegistryValidator,
)
from hermass_platform.factors.exceptions import RegistryValidationError


class TestEndToEndCatalogLoading:
    """17. End-to-end: load catalogs into registries and validate."""

    def test_load_all_into_registries(self):
        loader = CatalogLoader()
        src_reg, fac_reg, blk_reg, ev_reg = loader.load_all()

        assert len(src_reg.list_all()) >= 10
        assert len(fac_reg.list_all()) >= 10
        assert len(blk_reg.list_all()) >= 10
        assert len(ev_reg.list_all()) >= 10

    def test_cross_registry_source_refs_validation(self):
        loader = CatalogLoader()
        src_reg, fac_reg, blk_reg, ev_reg = loader.load_all()

        validator = RegistryValidator(src_reg, fac_reg, blk_reg, ev_reg)
        # Should pass — all source_refs in catalogs are valid
        result = validator.validate_all()
        assert result["factor_source_refs"] == []
        assert result["block_source_refs"] == []

    def test_factor_gate_derivation_from_catalog(self):
        loader = CatalogLoader()
        factors = loader.load_factors()

        from hermass_platform.factors.factor_schema import derive_factor_gate

        for f in factors:
            gate = derive_factor_gate(
                evidence_level=f.evidence_level,
                validation_status="passed",
                data_availability=f.data_availability,
                future_leakage_risk=f.future_leakage_risk,
                status=f.status,
            )
            # All catalog factors should have valid gates
            assert gate is not None
            # High future leakage factors should be blocked
            if f.future_leakage_risk.value == "high":
                assert gate.value == "blocked"

    def test_block_parameter_space_subset_in_catalog(self):
        loader = CatalogLoader()
        blocks = loader.load_blocks()

        for b in blocks:
            if b.parameter_space:
                param_keys = set(b.parameters.keys())
                space_keys = set(b.parameter_space.keys())
                assert space_keys.issubset(param_keys), \
                    f"Block {b.block_id}: parameter_space keys {space_keys} not subset of parameters {param_keys}"

    def test_evidence_source_refs_in_catalog(self):
        loader = CatalogLoader()
        all_data = loader.load_all_catalogs()
        sources = {s.source_id for s in all_data["sources"]}
        evidence = all_data["evidence"]

        for ev in evidence:
            assert ev.target_id in sources, \
                f"Evidence {ev.evidence_id} references unknown source/target {ev.target_id}"

    def test_factor_a_share_notes_present(self):
        """A-share notes should be present for all factors."""
        loader = CatalogLoader()
        factors = loader.load_factors()

        for f in factors:
            assert f.a_share_notes, \
                f"Factor {f.factor_id} missing a_share_notes"

    def test_catalog_counts(self):
        loader = CatalogLoader()
        all_data = loader.load_all_catalogs()
        assert len(all_data["sources"]) == 11
        assert len(all_data["factors"]) == 11
        assert len(all_data["blocks"]) == 12
        assert len(all_data["evidence"]) == 19

    def test_canonical_source_type_coverage(self):
        """All 10 canonical source_types should be represented."""
        loader = CatalogLoader()
        sources = loader.load_sources()
        source_types = {s.source_type.value for s in sources}
        expected = {
            "strategy_generator", "open_quant_framework", "institutional_factor",
            "academic_literature", "fundamental_data", "news_sentiment",
            "money_flow", "trader_methodology", "behavioral_factor", "hermass_native",
        }
        assert expected.issubset(source_types), \
            f"Missing source_types: {expected - source_types}"
