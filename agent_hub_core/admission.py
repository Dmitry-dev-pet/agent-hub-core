from __future__ import annotations

import hashlib
import json
from typing import Any

from .validation import validate_document


POLICY_ID = "truthrail-admission-v1"


def _digest(payload: Any) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _finding(rule_id: str, reason: str) -> dict[str, str]:
    return {"rule_id": rule_id, "reason": reason}


def evaluate_operation_admission(
    contract: dict[str, Any],
    operation: str,
    *,
    actor: str,
    owner: str,
    route: str = "agent",
) -> dict[str, Any]:
    """Fail-closed runtime admission for one reviewed control-plane operation.

    This function evaluates only reviewed contract metadata and invocation context.
    It never reads credential values and never executes the target operation.
    """

    validate_document("control_plane", contract)

    if route not in {"agent", "operator"}:
        raise ValueError("route must be 'agent' or 'operator'")
    if not actor:
        raise ValueError("actor must be non-empty")
    if not owner:
        raise ValueError("owner must be non-empty")
    if not operation:
        raise ValueError("operation must be non-empty")

    findings: list[dict[str, str]] = []
    requirements: list[str] = []
    decision = "ADMIT"

    spec = contract["operations"].get(operation)
    if not isinstance(spec, dict):
        decision = "DENY"
        findings.append(
            _finding("TRA001", "Operation is not present in the reviewed control-plane contract.")
        )
        spec_for_digest: dict[str, Any] = {}
    else:
        spec_for_digest = spec
        admission = spec.get("admission")
        if not isinstance(admission, dict):
            decision = "DENY"
            findings.append(
                _finding(
                    "TRA004",
                    "Operation has no explicit runtime admission declaration; admission fails closed.",
                )
            )
        else:
            requester = admission.get("requester")
            mode = admission.get("mode")

            if requester == "repository_owner" and actor != owner:
                decision = "DENY"
                findings.append(
                    _finding(
                        "TRA003",
                        "Requester does not match the repository owner required by the operation.",
                    )
                )

            if route == "agent" and spec.get("agent_routable") is not True:
                decision = "DENY"
                findings.append(
                    _finding(
                        "TRA002",
                        "Operation is not agent-routable in the reviewed contract.",
                    )
                )

            if mode == "operator_only" and route == "agent":
                decision = "DENY"
                findings.append(
                    _finding(
                        "TRA005",
                        "Operator-only admission mode rejects agent-routed execution.",
                    )
                )

            if decision != "DENY":
                if mode == "manual_approval":
                    decision = "REQUIRE_HUMAN"
                    requirements.append("manual_approval")
                    findings.append(
                        _finding(
                            "TRA100",
                            "Operation requires a trusted human approval before execution.",
                        )
                    )
                elif mode == "provider_interaction":
                    requirements.append("provider_interaction")
                    findings.append(
                        _finding(
                            "TRA101",
                            "Operation may start, but its reviewed provider-interaction gate remains mandatory.",
                        )
                    )
                elif mode == "operator_only" and route == "operator":
                    findings.append(
                        _finding(
                            "TRA102",
                            "Operator route is admitted for an operator-only operation.",
                        )
                    )
                elif mode == "automatic":
                    pass
                else:
                    decision = "DENY"
                    findings.append(
                        _finding(
                            "TRA006",
                            "Admission mode is missing or unsupported.",
                        )
                    )

    result = {
        "version": 1,
        "kind": "operation_admission_decision",
        "policy": POLICY_ID,
        "decision": decision,
        "operation": operation,
        "actor": actor,
        "owner": owner,
        "route": route,
        "contract_sha256": _digest(contract),
        "operation_sha256": _digest(spec_for_digest),
        "requirements": requirements,
        "findings": findings,
    }
    validate_document("operation_admission_decision", result)
    return result


def format_operation_admission_markdown(decision: dict[str, Any]) -> str:
    lines = [
        "## Runtime admission",
        "",
        f"Decision: **{decision['decision']}** · policy: `{decision['policy']}`",
        "",
        f"- operation: `{decision['operation']}`",
        f"- actor: `{decision['actor']}`",
        f"- owner: `{decision['owner']}`",
        f"- route: `{decision['route']}`",
        f"- contract SHA-256: `{decision['contract_sha256']}`",
        f"- operation SHA-256: `{decision['operation_sha256']}`",
    ]
    if decision["requirements"]:
        lines.append(
            "- remaining reviewed requirement(s): "
            + ", ".join(f"`{item}`" for item in decision["requirements"])
        )

    if decision["findings"]:
        lines.extend(["", "Findings:"])
        for item in decision["findings"]:
            lines.append(f"- `{item['rule_id']}`: {item['reason']}")
    else:
        lines.extend(["", "No admission findings."])
    return "\n".join(lines)
