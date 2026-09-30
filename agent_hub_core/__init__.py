"""Portable protocol and reference implementation for Agent Hub Core."""

__version__ = "0.1.1"

from .conformance import run_scenario
from .instance import (
    InstanceValidationError,
    bootstrap_acceptance,
    doctor_instance,
    init_instance,
    validate_instance,
)
from .reference import ReferenceAdapter, RoutingError
from .validation import (
    ProtocolValidationError,
    check_schemas,
    validate_document,
    validate_file,
)

__all__ = [
    "__version__",
    "InstanceValidationError",
    "ProtocolValidationError",
    "ReferenceAdapter",
    "RoutingError",
    "bootstrap_acceptance",
    "check_schemas",
    "doctor_instance",
    "init_instance",
    "run_scenario",
    "validate_document",
    "validate_file",
    "validate_instance",
]
