"""Portable protocol and reference implementation for Agent Hub Core."""

__version__ = "0.1.1"

from .admission import evaluate_operation_admission, format_operation_admission_markdown
from .capability_diff import diff_control_planes, format_capability_diff_markdown
from .capability_policy import evaluate_capability_policy, evaluate_control_plane_policy, format_capability_policy_markdown
from .conformance import run_scenario
from .execution_binding import (
    ExecutionBindingError,
    StaleExecutionResultError,
    assert_receipt_fresh,
    authorize_repository_route,
    bind_execution_plan,
    bind_execution_receipt,
    canonical_digest,
    compute_state_fingerprint,
    render_pr_summary,
)
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
    validate_run_bundle,
)

__all__ = [
    "__version__",
    "ExecutionBindingError",
    "StaleExecutionResultError",
    "assert_receipt_fresh",
    "authorize_repository_route",
    "bind_execution_plan",
    "bind_execution_receipt",
    "canonical_digest",
    "compute_state_fingerprint",
    "render_pr_summary",
    "InstanceValidationError",
    "ProtocolValidationError",
    "ReferenceAdapter",
    "RoutingError",
    "bootstrap_acceptance",
    "check_schemas",
    "diff_control_planes",
    "doctor_instance",
    "evaluate_operation_admission",
    "evaluate_capability_policy",
    "evaluate_control_plane_policy",
    "format_capability_policy_markdown",
    "format_capability_diff_markdown",
    "format_operation_admission_markdown",
    "init_instance",
    "run_scenario",
    "validate_document",
    "validate_file",
    "validate_run_bundle",
    "validate_instance",
]
