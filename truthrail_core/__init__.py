"""Canonical Python namespace for Truthrail Core.

The implementation remains in :mod:`agent_hub_core` during the compatibility
window. New code should import :mod:`truthrail_core`; the legacy namespace is
kept working for existing consumers.
"""

from agent_hub_core import *  # noqa: F401,F403
from agent_hub_core import __all__ as _legacy_all
from agent_hub_core import __version__

__all__ = list(_legacy_all)
