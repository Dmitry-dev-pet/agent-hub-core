"""Portable protocol and reference implementation for Agent Hub Core."""

__version__ = "0.1.0"

from .conformance import run_scenario
from .reference import ReferenceAdapter, RoutingError
from .validation import (
    ProtocolValidationError,
    check_schemas,
    validate_document,
    validate_file,
)

__all__ = [
    "__version__",
    "ProtocolValidationError",
    "ReferenceAdapter",
    "RoutingError",
    "check_schemas",
    "run_scenario",
    "validate_document",
    "validate_file",
]
