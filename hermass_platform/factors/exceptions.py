"""Registry layer custom exceptions."""


class RegistryError(Exception):
    """Base registry exception."""
    pass


class DuplicateSourceError(RegistryError):
    """source_id already exists."""
    pass


class DuplicateFactorError(RegistryError):
    """factor_id already exists."""
    pass


class DuplicateBlockError(RegistryError):
    """block_id already exists."""
    pass


class DuplicateEvidenceError(RegistryError):
    """evidence_id already exists."""
    pass


class SourceNotFoundError(RegistryError):
    """source_id does not exist."""
    pass


class FactorNotFoundError(RegistryError):
    """factor_id does not exist."""
    pass


class BlockNotFoundError(RegistryError):
    """block_id does not exist."""
    pass


class InvalidSourceTypeError(RegistryError):
    """source_type not in canonical enum."""
    pass


class EvidenceGateError(RegistryError):
    """Evidence level does not meet production requirements."""
    pass


class FutureLeakageError(RegistryError):
    """Future leakage risk detected."""
    pass


class DataUnavailableError(RegistryError):
    """Data is not available."""
    pass


class SourceValidationError(RegistryError):
    """Source validation failed."""
    pass


class FactorValidationError(RegistryError):
    """Factor validation failed."""
    pass


class BlockValidationError(RegistryError):
    """Block validation failed."""
    pass


class CatalogLoadError(RegistryError):
    """Catalog loading failed."""
    pass


class RegistryValidationError(RegistryError):
    """Cross-registry validation failed."""
    pass
