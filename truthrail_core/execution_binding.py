from __future__ import annotations

import re
from copy import deepcopy
from collections.abc import Mapping, Sequence
from typing import Any

from agent_hub_core.validation import _canonical_digest as canonical_digest
from .validation import ProtocolValidationError, validate_document, validate_run_bundle


ROUTE_ORDER = {"direct": 0, "branch_pr": 1}

__all__ = [
    "ExecutionBindingError", "StaleExecutionResultError", "assert_plan_current",
    "assert_receipt_fresh", "assert_receipt_matches_plan", "authorize_repository_route",
    "bind_execution_plan", "bind_execution_receipt", "bind_verification_result",
    "canonical_digest", "compute_state_fingerprint", "render_pr_summary",
]


class ExecutionBindingError(ValueError):
    """Raised when a v0.2 execution binding cannot be issued or accepted."""


class StaleExecutionResultError(ExecutionBindingError):
    """Raised when a receipt no longer matches the active authoritative state."""


def _validate_bundle(documents: Sequence[tuple[str, dict[str, Any]]]) -> None:
    try:
        validate_run_bundle(documents)
    except ProtocolValidationError as exc:
        raise ExecutionBindingError(str(exc)) from exc


def authorize_repository_route(
    proposed_route: str,
    *,
    policy_minimum: str = "direct",
) -> dict[str, str]:
    if proposed_route not in ROUTE_ORDER:
        raise ExecutionBindingError(
            f"unsupported proposed repository route: {proposed_route}"
        )
    if policy_minimum not in ROUTE_ORDER:
        raise ExecutionBindingError(
            f"unsupported policy minimum repository route: {policy_minimum}"
        )
    authorized = max(
        (proposed_route, policy_minimum),
        key=lambda value: ROUTE_ORDER[value],
    )
    return {
        "proposed": proposed_route,
        "policy_minimum": policy_minimum,
        "authorized": authorized,
    }


def compute_state_fingerprint(
    work_packet_digest: str,
    inputs: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", work_packet_digest):
        raise ExecutionBindingError("work_packet_digest must be a canonical SHA-256 digest")
    normalized: list[dict[str, str]] = []
    allowed_keys = {"kind", "ref", "value"}

    for item in inputs:
        if set(item) != allowed_keys:
            raise ExecutionBindingError(
                "state fingerprint inputs must contain exactly kind/ref/value"
            )
        normalized_item = {
            "kind": item["kind"],
            "ref": item["ref"],
            "value": item["value"],
        }
        if not all(
            isinstance(normalized_item[key], str) and normalized_item[key]
            for key in ("kind", "ref", "value")
        ):
            raise ExecutionBindingError(
                "state fingerprint kind/ref/value must be non-empty strings"
            )
        if normalized_item["kind"] not in {
            "repository_head", "control_plane_contract", "policy", "provider_state", "other"
        }:
            raise ExecutionBindingError("unsupported authoritative state input kind")
        normalized.append(normalized_item)

    if not normalized:
        raise ExecutionBindingError(
            "state fingerprint requires at least one authoritative input"
        )

    identities = [(item["kind"], item["ref"]) for item in normalized]
    if len(identities) != len(set(identities)):
        raise ExecutionBindingError(
            "state fingerprint cannot contain duplicate kind/ref identities"
        )

    normalized.sort(key=lambda item: (item["kind"], item["ref"], item["value"]))
    digest = canonical_digest(
        {
            "work_packet_digest": work_packet_digest,
            "inputs": normalized,
        }
    )
    return {
        "algorithm": "sha256",
        "digest": digest,
        "inputs": normalized,
    }


def bind_execution_plan(
    work_packet: Mapping[str, Any],
    execution_plan: Mapping[str, Any],
    *,
    state_inputs: Sequence[Mapping[str, str]],
    proposed_route: str = "direct",
    policy_minimum_route: str = "direct",
    execution_venue: str | None = None,
) -> dict[str, Any]:
    packet = deepcopy(dict(work_packet))
    plan = deepcopy(dict(execution_plan))
    plan.pop("execution_binding", None)

    _validate_bundle([("work_packet", packet), ("execution_plan", plan)])

    work_packet_digest = canonical_digest(packet)
    binding: dict[str, Any] = {
        "work_packet_digest": work_packet_digest,
        "state_fingerprint": compute_state_fingerprint(
            work_packet_digest,
            state_inputs,
        ),
        "route": authorize_repository_route(
            proposed_route,
            policy_minimum=policy_minimum_route,
        ),
    }
    if execution_venue:
        binding["execution_venue"] = execution_venue

    plan["execution_binding"] = binding
    validate_document("execution_plan", plan, schema_version="0.2")
    return plan


def bind_execution_receipt(
    execution_plan: Mapping[str, Any],
    *,
    approval: Mapping[str, str],
    authoritative_refs: Sequence[Mapping[str, str]],
    observations: Sequence[str],
    observed_effects: Sequence[str] = (),
    actor: str | None = None,
    execution_venue: str | None = None,
) -> dict[str, Any]:
    plan = deepcopy(dict(execution_plan))
    validate_document("execution_plan", plan, schema_version="0.2")

    binding = plan.get("execution_binding")
    if not isinstance(binding, dict):
        raise ExecutionBindingError(
            "ExecutionPlan must be state-bound before issuing a bound receipt"
        )

    approval_doc = dict(approval)
    if plan["approval"]["required"] and approval_doc.get("status") != "approved":
        raise ExecutionBindingError(
            "ExecutionPlan requires approval before an executed receipt may be issued"
        )
    if approval_doc.get("status") == "approved":
        if approval_doc.get("execution_plan_digest") != canonical_digest(plan):
            raise ExecutionBindingError(
                "approved receipt requires an explicit matching plan digest from the approval gate"
            )
    if execution_venue and binding.get("execution_venue") not in (None, execution_venue):
        raise ExecutionBindingError("receipt venue differs from the bound execution venue")

    receipt: dict[str, Any] = {
        "version": 2,
        "run_id": plan["run_id"],
        "status": "executed",
        "capability": plan["capability"],
        "approval": approval_doc,
        "authoritative_refs": [dict(item) for item in authoritative_refs],
        "observations": list(observations),
        "execution_binding": {
            "state_fingerprint": binding["state_fingerprint"]["digest"],
            "execution_plan_digest": canonical_digest(plan),
            "route": binding["route"]["authorized"],
        },
        "observed_effects": list(observed_effects),
    }
    if actor:
        receipt["actor"] = actor
    if execution_venue or binding.get("execution_venue"):
        receipt["execution_venue"] = (
            execution_venue or binding["execution_venue"]
        )

    validate_document("execution_receipt", receipt, schema_version="0.2")
    return receipt


def assert_receipt_matches_plan(
    execution_plan: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> None:
    """Check receipt binding, without claiming to have re-read external state."""
    plan = deepcopy(dict(execution_plan))
    receipt_doc = deepcopy(dict(receipt))
    validate_document("execution_plan", plan, schema_version="0.2")
    validate_document("execution_receipt", receipt_doc, schema_version="0.2")

    binding = plan.get("execution_binding")
    receipt_binding = receipt_doc.get("execution_binding")
    if not isinstance(binding, dict) or not isinstance(receipt_binding, dict):
        raise ExecutionBindingError(
            "receipt checks require a bound ExecutionPlan and bound ExecutionReceipt"
        )

    if receipt_doc["run_id"] != plan["run_id"]:
        raise StaleExecutionResultError(
            "receipt run_id does not match the active ExecutionPlan"
        )
    if receipt_doc["capability"] != plan["capability"]:
        raise StaleExecutionResultError(
            "receipt capability does not match the active ExecutionPlan"
        )
    if receipt_binding["execution_plan_digest"] != canonical_digest(plan):
        raise StaleExecutionResultError(
            "receipt execution_plan_digest does not match the active ExecutionPlan"
        )
    if (
        receipt_binding["state_fingerprint"]
        != binding["state_fingerprint"]["digest"]
    ):
        raise StaleExecutionResultError(
            "receipt state_fingerprint does not match the active ExecutionPlan"
        )
    if receipt_binding["route"] != binding["route"]["authorized"]:
        raise StaleExecutionResultError(
            "receipt route does not match the active authorized route"
        )
    if plan["approval"]["required"] and receipt_doc["approval"]["status"] != "approved":
        raise ExecutionBindingError("receipt does not carry the required approval")
    if receipt_doc["approval"]["status"] == "approved":
        if receipt_doc["approval"]["execution_plan_digest"] != canonical_digest(plan):
            raise ExecutionBindingError("receipt approval belongs to another plan")
    if binding.get("execution_venue") is not None:
        if receipt_doc.get("execution_venue") != binding["execution_venue"]:
            raise ExecutionBindingError("receipt venue differs from the bound execution venue")


def assert_plan_current(
    execution_plan: Mapping[str, Any],
    *,
    current_state_inputs: Sequence[Mapping[str, str]],
) -> None:
    """Reject changed preconditions immediately before execution or result reuse.

    Callers must supply a fresh provider read. This helper makes no network calls.
    Do not compare an authorized mutation's post-state to its pre-state; verify the
    resulting resource separately and bind that verification to its receipt.
    """
    plan = deepcopy(dict(execution_plan))
    validate_document("execution_plan", plan, schema_version="0.2")
    binding = plan.get("execution_binding")
    if not isinstance(binding, dict):
        raise ExecutionBindingError("freshness checks require a bound ExecutionPlan")
    current = compute_state_fingerprint(binding["work_packet_digest"], current_state_inputs)
    if current["digest"] != binding["state_fingerprint"]["digest"]:
        raise StaleExecutionResultError("authoritative preconditions changed after the plan was bound")


def assert_receipt_fresh(
    execution_plan: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    current_state_inputs: Sequence[Mapping[str, str]],
) -> None:
    """Allow reuse only while the bound planning preconditions still match."""
    assert_receipt_matches_plan(execution_plan, receipt)
    assert_plan_current(execution_plan, current_state_inputs=current_state_inputs)


def bind_verification_result(
    work_packet: Mapping[str, Any],
    execution_plan: Mapping[str, Any],
    receipt: Mapping[str, Any],
    verification_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind supplied verification evidence to one receipt; never invent checks."""
    result = deepcopy(dict(verification_result))
    receipt_digest = canonical_digest(receipt)
    if "execution_receipt_digest" in result and result["execution_receipt_digest"] != receipt_digest:
        raise ExecutionBindingError("verification is already bound to another ExecutionReceipt")
    result["execution_receipt_digest"] = receipt_digest
    _validate_bundle([
        ("work_packet", dict(work_packet)),
        ("execution_plan", dict(execution_plan)),
        ("execution_receipt", dict(receipt)),
        ("verification_result", result),
    ])
    return result


def render_pr_summary(
    work_packet: Mapping[str, Any],
    execution_plan: Mapping[str, Any],
    *,
    receipt: Mapping[str, Any] | None = None,
    verification_result: Mapping[str, Any] | None = None,
) -> str:
    packet = deepcopy(dict(work_packet))
    plan = deepcopy(dict(execution_plan))
    validate_document("work_packet", packet, schema_version="0.2")
    validate_document("execution_plan", plan, schema_version="0.2")

    binding = plan.get("execution_binding")
    if not isinstance(binding, dict):
        raise ExecutionBindingError(
            "PR summary requires a state-bound ExecutionPlan"
        )

    receipt_doc: dict[str, Any] | None = None
    if receipt is not None:
        receipt_doc = deepcopy(dict(receipt))
        assert_receipt_matches_plan(plan, receipt_doc)

    verification_doc: dict[str, Any] | None = None
    if verification_result is not None:
        verification_doc = deepcopy(dict(verification_result))
        validate_document(
            "verification_result",
            verification_doc,
            schema_version="0.2",
        )
        if verification_doc["run_id"] != packet["run_id"]:
            raise ExecutionBindingError(
                "VerificationResult belongs to a different run"
            )

    documents = [("work_packet", packet), ("execution_plan", plan)]
    if receipt_doc is not None:
        documents.append(("execution_receipt", receipt_doc))
    if verification_doc is not None:
        documents.append(("verification_result", verification_doc))
    _validate_bundle(documents)

    route = binding["route"]["authorized"]
    lines = [
        "## Truthrail work record",
        "",
        "> Projection only. Authoritative state and evidence remain in the linked provider or verifier records; this summary is not an attestation.",
        "",
        f"**Run:** `{packet['run_id']}`",
        f"**Objective:** {packet['outcome']['description']}",
        f"**State fingerprint:** `{binding['state_fingerprint']['digest']}`",
        f"**Route:** `{route}`",
        f"**Capability:** `{plan['capability']}` at `{plan['selected_level']}`",
        "",
        "### Authority",
        "",
        "- Repositories: " + ", ".join(
            f"`{item}`" for item in packet["execution_envelope"]["repositories"]
        ),
        "- Allowed effects: " + ", ".join(
            f"`{item}`" for item in packet["execution_envelope"]["allowed"]
        ),
        "- Forbidden effects: " + (
            ", ".join(
                f"`{item}`" for item in packet["execution_envelope"]["forbidden"]
            )
            or "(none)"
        ),
    ]

    if receipt_doc is not None:
        lines.extend(["", "### Execution", ""])
        lines.append(f"- Status: `{receipt_doc['status']}`")
        for effect in receipt_doc.get("observed_effects", []):
            lines.append(f"- Observed effect: {effect}")
        lines.append("- Authoritative references:")
        for ref in receipt_doc["authoritative_refs"]:
            lines.append(f"  - `{ref['type']}`: {ref['value']}")

    if verification_doc is not None:
        lines.extend(["", "### Verification", ""])
        lines.append(f"- Status: `{verification_doc['status']}`")
        for check in verification_doc["checks"]:
            marker = "PASS" if check["passed"] else "FAIL"
            lines.append(f"- {marker}: {check['name']}")
        if verification_doc["authoritative_refs"]:
            lines.append("- Authoritative verification references:")
            for ref in verification_doc["authoritative_refs"]:
                lines.append(f"  - `{ref['type']}`: {ref['value']}")

    return "\n".join(lines) + "\n"
