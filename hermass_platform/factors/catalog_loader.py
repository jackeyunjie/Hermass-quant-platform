"""YAML catalog loader.

Loads Source / Factor / Block / Evidence metadata from config/factors/*.yaml.
"""

from pathlib import Path
from typing import Tuple

import yaml

from hermass_platform.factors.block_schema import BlockSpec
from hermass_platform.factors.factor_schema import FactorSpec
from hermass_platform.factors.registry import (
    BlockRegistry,
    EvidenceRegistry,
    FactorRegistry,
    SourceRegistry,
)
from hermass_platform.factors.source_schema import Evidence, FactorSource


_DEFAULT_CONFIG_DIR = Path(__file__).parent.parent.parent / "config" / "factors"


class CatalogLoader:
    """Catalog loader."""

    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = Path(config_dir) if config_dir else _DEFAULT_CONFIG_DIR
        self.source_path = self.config_dir / "source_catalog.yaml"
        self.factor_path = self.config_dir / "factor_catalog.yaml"
        self.block_path = self.config_dir / "block_catalog.yaml"
        self.evidence_path = self.config_dir / "evidence_catalog.yaml"

    def _load_yaml(self, path: Path) -> dict:
        if not path.exists():
            raise FileNotFoundError(f"catalog file not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def load_sources(self) -> list[FactorSource]:
        data = self._load_yaml(self.source_path)
        items = data.get("sources", [])
        return [FactorSource.model_validate(item) for item in items]

    def load_factors(self) -> list[FactorSpec]:
        data = self._load_yaml(self.factor_path)
        items = data.get("factors", [])
        return [FactorSpec.model_validate(item) for item in items]

    def load_blocks(self) -> list[BlockSpec]:
        data = self._load_yaml(self.block_path)
        items = data.get("blocks", [])
        return [BlockSpec.model_validate(item) for item in items]

    def load_evidence(self) -> list[Evidence]:
        data = self._load_yaml(self.evidence_path)
        items = data.get("evidence", [])
        return [Evidence.model_validate(item) for item in items]

    def load_all(
        self,
    ) -> Tuple[SourceRegistry, FactorRegistry, BlockRegistry, EvidenceRegistry]:
        """Load all catalogs and return populated registries."""
        source_registry = SourceRegistry()
        factor_registry = FactorRegistry()
        block_registry = BlockRegistry()
        evidence_registry = EvidenceRegistry()

        for src in self.load_sources():
            source_registry.register(src)

        for fac in self.load_factors():
            factor_registry.register(fac)

        for blk in self.load_blocks():
            block_registry.register(blk)

        for ev in self.load_evidence():
            evidence_registry.register(ev)

        return source_registry, factor_registry, block_registry, evidence_registry

    def load_all_catalogs(self) -> dict:
        """Load all catalogs and return raw dict of lists."""
        return {
            "sources": self.load_sources(),
            "factors": self.load_factors(),
            "blocks": self.load_blocks(),
            "evidence": self.load_evidence(),
        }


def load_catalogs(
    config_dir: Path | None = None,
) -> Tuple[SourceRegistry, FactorRegistry, BlockRegistry, EvidenceRegistry]:
    """Convenience function: load all catalogs from config directory."""
    return CatalogLoader(config_dir).load_all()
