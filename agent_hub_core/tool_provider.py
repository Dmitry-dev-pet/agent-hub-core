from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from .admission import evaluate_operation_admission
from .reference import ReferenceAdapter, RoutingError


class ToolProviderError(ValueError):
    """Raised when a tool request cannot be resolved safely."""


def _stable_id(payload: Any) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:24]


TOOL_DEFINITIONS = [
    {
        "name": "truthrail_status",
        "description": (
            "Read current authoritative state for one Truthrail project. "
            "This tool never mutates external systems."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string", "minLength": 1}},
            "required": ["project"],
            "additionalProperties": False,
        },
    },
    {
        "name": "truthrail_dispatch",
        "description": (
            "Build the lowest-sufficient Truthrail execution plan and evaluate "
            "runtime admission for an optional reviewed control-plane operation. "
            "This tool never executes the operation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "minLength": 1},
                "requirement": {
                    "type": "string",
                    "enum": [
                        "read",
                        "direct_mutation",
                        "privileged_mutation",
                        "runtime",
                        "coding_agent",
                        "machine_bound",
                    ],
                },
                "capability": {"type": "string", "minLength": 1},
                "operation": {"type": "string", "minLength": 1},
                "acceptance_proof": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                    "minItems": 1,
                },
            },
            "required": [
                "project",
                "requirement",
                "capability",
                "acceptance_proof",
            ],
            "additionalProperties": False,
        },
    },
    {
        "name": "truthrail_approve",
        "description": (
            "Resolve a pending manual-approval gate created by truthrail_dispatch. "
            "Approval releases a handoff; it does not execute the privileged action."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "approval_id": {"type": "string", "minLength": 1},
                "approve": {"type": "boolean"},
            },
            "required": ["approval_id", "approve"],
            "additionalProperties": False,
        },
    },
]


class TruthrailToolProvider:
    """Small, execution-free tool boundary for conversational agent UIs.

    The provider exposes STATUS -> DISPATCH -> APPROVE semantics while preserving
    Truthrail's core invariant that privileged execution belongs to the reviewed
    control plane that owns the capability.
    """

    def __init__(
        self,
        adapter: ReferenceAdapter,
        control_plane_contracts: dict[str, Any],
        *,
        actor: str,
        owner: str,
    ) -> None:
        if not actor:
            raise ValueError("actor must be non-empty")
        if not owner:
            raise ValueError("owner must be non-empty")
        self.adapter = adapter
        self.control_plane_contracts = deepcopy(control_plane_contracts)
        self.actor = actor
        self.owner = owner
        self._pending: dict[str, dict[str, Any]] = {}
        self._resolved: dict[str, dict[str, Any]] = {}

    def list_tools(self) -> list[dict[str, Any]]:
        return deepcopy(TOOL_DEFINITIONS)

    def _resolve_project(self, project: str) -> dict[str, Any]:
        if not isinstance(project, str) or not project.strip():
            raise ToolProviderError("project must be a non-empty string")
        needle = project.strip().casefold()
        exact = [
            route
            for route in self.adapter.instance.get("projects", [])
            if route.get("id", "").casefold() == needle
            or route.get("repo", "").casefold() == needle
        ]
        if len(exact) == 1:
            return deepcopy(exact[0])
        try:
            return self.adapter.resolve(project)
        except RoutingError as exc:
            raise ToolProviderError(str(exc)) from exc

    def status(self, project: str) -> dict[str, Any]:
        route = self._resolve_project(project)
        try:
            hydrated = self.adapter.hydrate(route)
        except RoutingError as exc:
            raise ToolProviderError(str(exc)) from exc
        return {
            "state": "current",
            "project": hydrated["project"],
            "repo": hydrated["repo"],
            "live": hydrated["live"],
            "executed": False,
        }

    def dispatch(
        self,
        *,
        project: str,
        requirement: str,
        capability: str,
        acceptance_proof: list[str],
        operation: str | None = None,
    ) -> dict[str, Any]:
        route = self._resolve_project(project)
        if not isinstance(capability, str) or not capability.strip():
            raise ToolProviderError("capability must be a non-empty string")
        if (
            not isinstance(acceptance_proof, list)
            or not acceptance_proof
            or not all(isinstance(item, str) and item.strip() for item in acceptance_proof)
        ):
            raise ToolProviderError("acceptance_proof must contain non-empty strings")
        try:
            plan = self.adapter.plan(
                route["id"],
                requirement,
                capability,
                acceptance_proof,
                operation=operation,
            )
        except RoutingError as exc:
            raise ToolProviderError(str(exc)) from exc

        response: dict[str, Any] = {
            "state": "planned",
            "plan": plan,
            "executed": False,
        }
        if operation is None:
            return response

        contract = self.control_plane_contracts.get(capability)
        if not isinstance(contract, dict):
            raise ToolProviderError(
                f"missing live operation contract for {capability}"
            )
        admission = evaluate_operation_admission(
            contract,
            operation,
            actor=self.actor,
            owner=self.owner,
            route="agent",
        )
        response["admission"] = admission

        if admission["decision"] == "DENY":
            response["state"] = "denied"
            return response
        if admission["decision"] == "ADMIT":
            response["state"] = "admitted_for_handoff"
            return response

        pending = {
            "plan": plan,
            "admission": admission,
            "actor": self.actor,
            "owner": self.owner,
        }
        approval_id = _stable_id(pending)
        self._pending[approval_id] = pending
        response["state"] = "approval_required"
        response["approval_id"] = approval_id
        return response

    def approve(self, approval_id: str, approve: bool) -> dict[str, Any]:
        if not isinstance(approval_id, str) or not approval_id:
            raise ToolProviderError("approval_id must be a non-empty string")
        if not isinstance(approve, bool):
            raise ToolProviderError("approve must be a boolean")
        if approval_id in self._resolved:
            return deepcopy(self._resolved[approval_id])

        pending = self._pending.pop(approval_id, None)
        if pending is None:
            raise ToolProviderError("unknown or expired approval_id")

        result = {
            "approval_id": approval_id,
            "state": "approved_for_handoff" if approve else "rejected",
            "plan": pending["plan"],
            "admission": pending["admission"],
            "executed": False,
        }
        self._resolved[approval_id] = result
        return deepcopy(result)

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise ToolProviderError("tool arguments must be an object")
        if name == "truthrail_status":
            if set(arguments) != {"project"}:
                raise ToolProviderError("truthrail_status expects only project")
            return self.status(arguments["project"])
        if name == "truthrail_dispatch":
            allowed = {
                "project",
                "requirement",
                "capability",
                "acceptance_proof",
                "operation",
            }
            required = {
                "project",
                "requirement",
                "capability",
                "acceptance_proof",
            }
            if not required.issubset(arguments) or not set(arguments).issubset(allowed):
                raise ToolProviderError("invalid truthrail_dispatch arguments")
            return self.dispatch(**arguments)
        if name == "truthrail_approve":
            if set(arguments) != {"approval_id", "approve"}:
                raise ToolProviderError(
                    "truthrail_approve expects approval_id and approve"
                )
            return self.approve(arguments["approval_id"], arguments["approve"])
        raise ToolProviderError(f"unknown tool: {name}")
