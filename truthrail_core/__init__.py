"""Canonical Python namespace for Truthrail Core.

The implementation remains in :mod:`agent_hub_core` during the compatibility
window. New code should import :mod:`truthrail_core`; the legacy namespace is
kept working for existing consumers.
"""

from agent_hub_core import *  # noqa: F401,F403
from agent_hub_core import __all__ as _legacy_all
from agent_hub_core import __version__
from .execution_binding import (
    ExecutionBindingError,
    StaleExecutionResultError,
    assert_plan_current,
    assert_receipt_fresh,
    assert_receipt_matches_plan,
    authorize_repository_route,
    bind_execution_plan,
    bind_execution_receipt,
    bind_verification_result,
    canonical_digest,
    compute_state_fingerprint,
    render_pr_summary,
)

__all__ = list(_legacy_all) + [
    "ExecutionBindingError", "StaleExecutionResultError", "assert_plan_current",
    "assert_receipt_fresh", "assert_receipt_matches_plan", "authorize_repository_route",
    "bind_execution_plan", "bind_execution_receipt", "bind_verification_result",
    "canonical_digest", "compute_state_fingerprint", "render_pr_summary",
]
