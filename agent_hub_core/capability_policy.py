from __future__ import annotations

from typing import Any

from .capability_diff import diff_control_planes
from .validation import validate_document


POLICY_ID = "truthrail-default-v1"
_DECISION_ORDER = {"PASS": 0, "REVIEW": 1, "BLOCK": 2}

_REVIEW_CHANGED_FIELDS = {
    "credential_refs",
    "execution_level",
    "runtime_auth",
    "execution_venue",
    "execution_repository",
    "execution_contract",
    "github_permissions",
    "network_destinations",
    "external_side_effects",
    "cost_ceiling",
    "human_gate",
    "admission",
}


def _finding(
    operation: str,
    field: str,
    decision: str,
    rule_id: str,
    reason: str,
    before: Any,
    after: Any,
) -> dict[str, Any]:
    return {
        "operation": operation,
        "field": field,
        "decision": decision,
        "rule_id": rule_id,
        "reason": reason,
        "before": before,
        "after": after,
    }


def evaluate_capability_policy(report: dict[str, Any]) -> dict[str, Any]:
    """Apply Truthrail's deterministic default v1 review policy to a capability diff."""

    if report.get("kind") != "capability_diff" or report.get("version") != 1:
        raise ValueError("policy input must be a capability_diff v1 report")

    findings: list[dict[str, Any]] = []

    for operation in report.get("operations", []):
        name = operation["operation"]
        status = operation["status"]
        classification = operation["classification"]

        if status == "added" and classification == "expansion":
            findings.append(
                _finding(
                    name,
                    "operation",
                    "BLOCK",
                    "TRP001",
                    "A new AI-routable operation expands the agent command surface.",
                    None,
                    "present",
                )
            )
            continue

        if status == "added" and classification == "changed":
            findings.append(
                _finding(
                    name,
                    "operation",
                    "REVIEW",
                    "TRP101",
                    "A new non-routable reviewed operation changes the control-plane surface.",
                    None,
                    "present",
                )
            )

        for change in operation.get("changes", []):
            field = change["field"]
            kind = change["classification"]
            before = change.get("before")
            after = change.get("after")

            # The operation-level finding above already covers a newly added operation.
            if status == "added" and field == "operation":
                continue

            if field == "agent_routable" and kind == "expansion":
                findings.append(
                    _finding(
                        name,
                        field,
                        "BLOCK",
                        "TRP002",
                        "An existing operator-only operation becomes AI-routable.",
                        before,
                        after,
                    )
                )
                continue

            if field == "human_gate" and kind == "expansion":
                findings.append(
                    _finding(
                        name,
                        field,
                        "BLOCK",
                        "TRP003",
                        "A previously explicit human gate is removed.",
                        before,
                        after,
                    )
                )
                continue

            if kind == "expansion":
                findings.append(
                    _finding(
                        name,
                        field,
                        "REVIEW",
                        "TRP100",
                        "Explicit operation authority expands and requires human review.",
                        before,
                        after,
                    )
                )
                continue

            if kind == "changed" and field in _REVIEW_CHANGED_FIELDS:
                findings.append(
                    _finding(
                        name,
                        field,
                        "REVIEW",
                        "TRP101",
                        "Security-relevant execution context changed without a provable monotonic direction.",
                        before,
                        after,
                    )
                )

    decision = "PASS"
    for finding in findings:
        if _DECISION_ORDER[finding["decision"]] > _DECISION_ORDER[decision]:
            decision = finding["decision"]

    counts = {"PASS": 0, "REVIEW": 0, "BLOCK": 0}
    for finding in findings:
        counts[finding["decision"]] += 1

    result = {
        "version": 1,
        "kind": "capability_policy_decision",
        "policy": POLICY_ID,
        "decision": decision,
        "summary": {
            "block_findings": counts["BLOCK"],
            "review_findings": counts["REVIEW"],
            "operations_changed": report["summary"]["operations_changed"],
        },
        "findings": findings,
    }
    validate_document("capability_policy_decision", result)
    return result


def evaluate_control_plane_policy(
    before: dict[str, Any], after: dict[str, Any]
) -> dict[str, Any]:
    return evaluate_capability_policy(diff_control_planes(before, after))


def _render_value(value: Any) -> str:
    if value is None:
        return "∅"
    if isinstance(value, (dict, list)):
        import json

        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def format_capability_policy_markdown(decision: dict[str, Any]) -> str:
    summary = decision["summary"]
    lines = [
        "## Capability policy",
        "",
        f"Decision: **{decision['decision']}** · policy: `{decision['policy']}`",
        "",
        (
            f"Block findings: **{summary['block_findings']}** · "
            f"review findings: **{summary['review_findings']}**"
        ),
    ]

    if not decision["findings"]:
        lines.extend(["", "No policy findings."])
        return "\n".join(lines)

    for finding in decision["findings"]:
        lines.extend(
            [
                "",
                (
                    f"- **{finding['decision']}** `{finding['rule_id']}` "
                    f"`{finding['operation']}` / `{finding['field']}`: "
                    f"{finding['reason']} "
                    f"(`{_render_value(finding['before'])}` → "
                    f"`{_render_value(finding['after'])}`)"
                ),
            ]
        )
    return "\n".join(lines)
