"""Tests for catalog_loader.py — 5 test points."""

import pytest
from pathlib import Path

from hermass_platform.factors.catalog_loader import CatalogLoader, load_catalogs
from hermass_platform.factors.exceptions import CatalogLoadError


class TestCatalogLoader:
    """15. Test CatalogLoader."""

    def test_load_sources(self):
        loader = CatalogLoader()
        sources = loader.load_sources()
        assert len(sources) >= 10
        # Check canonical source types are present
        source_types = {s.source_type.value for s in sources}
        assert "strategy_generator" in source_types
        assert "hermass_native" in source_types

    def test_load_factors(self):
        loader = CatalogLoader()
        factors = loader.load_factors()
        assert len(factors) >= 10
        factor_ids = {f.factor_id for f in factors}
        assert "rsi_14" in factor_ids
        assert "d1_state" in factor_ids

    def test_load_blocks(self):
        loader = CatalogLoader()
        blocks = loader.load_blocks()
        assert len(blocks) >= 10
        block_ids = {b.block_id for b in blocks}
        assert "signal_indicator_cross_threshold" in block_ids
        assert "exit_fixed_stop_loss" in block_ids

    def test_load_evidence(self):
        loader = CatalogLoader()
        evidence = loader.load_evidence()
        assert len(evidence) >= 10
        # Check evidence levels
        levels = {e.evidence_level.value for e in evidence}
        assert "E0" in levels
        assert "E5" in levels

    def test_load_all_catalogs(self):
        loader = CatalogLoader()
        result = loader.load_all_catalogs()
        assert "sources" in result
        assert "factors" in result
        assert "blocks" in result
        assert "evidence" in result
        assert len(result["sources"]) >= 10
        assert len(result["factors"]) >= 10
        assert len(result["blocks"]) >= 10
        assert len(result["evidence"]) >= 10


class TestLoadCatalogs:
    """16. Test load_catalogs convenience function."""

    def test_load_catalogs(self):
        src_reg, fac_reg, blk_reg, ev_reg = load_catalogs()
        assert len(src_reg.list_all()) >= 10
        assert len(fac_reg.list_all()) >= 10
        assert len(blk_reg.list_all()) >= 10
        assert len(ev_reg.list_all()) >= 10
