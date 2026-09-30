from __future__ import annotations

from copy import deepcopy
from typing import Any


LEVEL_BY_REQUIREMENT = {
    "read": "L0",
    "direct_mutation": "L1",
    "privileged_mutation": "L2",
    "runtime": "L3",
    "coding_agent": "L4",
    "machine_bound": "L5",
}


class RoutingError(ValueError):
    """Raised when intent or capability routing cannot be resolved safely."""


class ReferenceAdapter:
    """Deterministic reference adapter for the Agent Hub Core v0.1 protocol."""

    def __init__(
        self,
        instance: dict[str, Any],
        live_state: dict[str, Any],
        control_plane_contracts: dict[str, Any],
    ) -> None:
        self.instance = deepcopy(instance)
        self.live_state = deepcopy(live_state)
        self.control_plane_contracts = deepcopy(control_plane_contracts)

    def resolve(self, user_intent: str) -> dict[str, Any]:
        normalized = user_intent.casefold()
        matches: list[dict[str, Any]] = []
        for route in self.instance["projects"]:
            aliases = [route["id"], *route.get("aliases", [])]
            if any(alias.casefold() in normalized for alias in aliases):
                matches.append(route)
        unique = {route["id"]: route for route in matches}
        if len(unique) != 1:
            raise RoutingError(
                f"intent must resolve to exactly one project, got {sorted(unique)}"
            )
        return deepcopy(next(iter(unique.values())))

    def hydrate(self, route: dict[str, Any]) -> dict[str, Any]:
        repo = route["repo"]
        if repo not in self.live_state:
            raise RoutingError(f"missing authoritative live state for {repo}")
        return {
            "project": route["id"],
            "repo": repo,
            "live": deepcopy(self.live_state[repo]),
        }

    def select_level(self, requirement: str) -> str:
        try:
            return LEVEL_BY_REQUIREMENT[requirement]
        except KeyError as exc:
            raise RoutingError(
                f"unknown execution requirement: {requirement}"
            ) from exc

    def resolve_control_plane_operation(
        self, capability: str, operation: str
    ) -> dict[str, Any]:
        contract = self.control_plane_contracts.get(capability)
        if not isinstance(contract, dict):
            raise RoutingError(
                f"missing live operation contract for {capability}"
            )
        spec = contract.get("operations", {}).get(operation)
        if not isinstance(spec, dict):
            raise RoutingError(f"unknown operation {capability}:{operation}")
        if spec.get("agent_routable") is not True:
            raise RoutingError(
                f"operation {capability}:{operation} is not agent-routable"
            )
        return deepcopy(spec)

    def plan(
        self,
        project: str,
        requirement: str,
        capability: str,
        acceptance_proof: list[str],
        operation: str | None = None,
    ) -> dict[str, Any]:
        plan: dict[str, Any] = {
            "version": 1,
            "project": project,
            "selected_level": self.select_level(requirement),
            "reason": (
                f"{requirement} requires the lowest sufficient execution level."
            ),
            "capability": capability,
            "acceptance_proof": acceptance_proof,
        }
        if operation is not None:
            plan["operation"] = operation
        return plan
