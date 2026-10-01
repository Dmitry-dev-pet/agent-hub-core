from __future__ import annotations

from typing import Any

from .validation import validate_document


_PERMISSION_ORDER = {"none": 0, "read": 1, "write": 2}
_LEVEL_ORDER = {f"L{i}": i for i in range(6)}
_SET_FIELDS = (
    "credential_refs",
    "network_destinations",
    "external_side_effects",
)
_SCALAR_FIELDS = (
    "runtime_auth",
    "execution_venue",
    "execution_contract",
)


def _change(field: str, classification: str, before: Any, after: Any, **extra: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "field": field,
        "classification": classification,
        "before": before,
        "after": after,
    }
    item.update(extra)
    return item


def _diff_set(field: str, before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    old = set(before.get(field, []))
    new = set(after.get(field, []))
    changes: list[dict[str, Any]] = []
    added = sorted(new - old)
    removed = sorted(old - new)
    if added:
        changes.append(
            _change(
                field,
                "expansion",
                sorted(old),
                sorted(new),
                added=added,
                removed=[],
            )
        )
    if removed:
        changes.append(
            _change(
                field,
                "reduction",
                sorted(old),
                sorted(new),
                added=[],
                removed=removed,
            )
        )
    return changes


def _diff_permissions(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    old = before.get("github_permissions", {})
    new = after.get("github_permissions", {})
    changes: list[dict[str, Any]] = []
    for scope in sorted(set(old) | set(new)):
        old_value = old.get(scope, "none")
        new_value = new.get(scope, "none")
        if old_value == new_value:
            continue
        old_rank = _PERMISSION_ORDER[old_value]
        new_rank = _PERMISSION_ORDER[new_value]
        classification = "expansion" if new_rank > old_rank else "reduction"
        changes.append(
            _change(
                f"github_permissions.{scope}",
                classification,
                old_value,
                new_value,
            )
        )
    return changes


def _diff_level(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    old = before.get("execution_level")
    new = after.get("execution_level")
    if old == new:
        return []
    if old is None or new is None:
        classification = "changed"
    else:
        classification = "expansion" if _LEVEL_ORDER[new] > _LEVEL_ORDER[old] else "reduction"
    return [_change("execution_level", classification, old, new)]


def _diff_agent_routable(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    old = before.get("agent_routable")
    new = after.get("agent_routable")
    if old == new:
        return []
    classification = "expansion" if new is True else "reduction"
    return [_change("agent_routable", classification, old, new)]


def _diff_human_gate(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    old = before.get("human_gate")
    new = after.get("human_gate")
    if old == new:
        return []
    if old == "none" and new not in (None, "none"):
        classification = "reduction"
    elif new == "none" and old not in (None, "none"):
        classification = "expansion"
    else:
        classification = "changed"
    return [_change("human_gate", classification, old, new)]


def _diff_cost_ceiling(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    old = before.get("cost_ceiling")
    new = after.get("cost_ceiling")
    if old == new:
        return []
    classification = "changed"
    if isinstance(old, dict) and isinstance(new, dict) and old.get("unit") == new.get("unit"):
        old_amount = old.get("amount")
        new_amount = new.get("amount")
        if isinstance(old_amount, (int, float)) and isinstance(new_amount, (int, float)):
            if new_amount > old_amount:
                classification = "expansion"
            elif new_amount < old_amount:
                classification = "reduction"
    return [_change("cost_ceiling", classification, old, new)]


def diff_operation(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a deterministic capability diff for one operation.

    The classifier intentionally uses only explicit contract fields. It never infers
    authority from descriptions, trigger names, shell text, or model judgment.
    """

    changes: list[dict[str, Any]] = []
    changes.extend(_diff_agent_routable(before, after))
    changes.extend(_diff_level(before, after))
    for field in _SET_FIELDS:
        changes.extend(_diff_set(field, before, after))
    changes.extend(_diff_permissions(before, after))
    changes.extend(_diff_human_gate(before, after))
    changes.extend(_diff_cost_ceiling(before, after))
    for field in _SCALAR_FIELDS:
        old = before.get(field)
        new = after.get(field)
        if old != new:
            changes.append(_change(field, "changed", old, new))
    return sorted(changes, key=lambda item: (item["field"], item["classification"]))


def _operation_classification(changes: list[dict[str, Any]]) -> str:
    classes = {item["classification"] for item in changes}
    if "expansion" in classes:
        return "expansion"
    if "changed" in classes:
        return "changed"
    if "reduction" in classes:
        return "reduction"
    return "none"


def diff_control_planes(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compare two validated reviewed-control-plane contracts."""

    validate_document("control_plane", before)
    validate_document("control_plane", after)

    old_ops = before["operations"]
    new_ops = after["operations"]
    operations: list[dict[str, Any]] = []

    for name in sorted(set(old_ops) | set(new_ops)):
        old = old_ops.get(name)
        new = new_ops.get(name)
        if old is None:
            classification = "expansion" if new.get("agent_routable") is True else "changed"
            operations.append(
                {
                    "operation": name,
                    "status": "added",
                    "classification": classification,
                    "changes": [
                        _change("operation", classification, None, "present")
                    ],
                }
            )
            continue
        if new is None:
            classification = "reduction" if old.get("agent_routable") is True else "changed"
            operations.append(
                {
                    "operation": name,
                    "status": "removed",
                    "classification": classification,
                    "changes": [
                        _change("operation", classification, "present", None)
                    ],
                }
            )
            continue

        changes = diff_operation(old, new)
        if changes:
            operations.append(
                {
                    "operation": name,
                    "status": "changed",
                    "classification": _operation_classification(changes),
                    "changes": changes,
                }
            )

    counts = {"expansion": 0, "reduction": 0, "changed": 0}
    for operation in operations:
        for item in operation["changes"]:
            classification = item["classification"]
            if classification in counts:
                counts[classification] += 1

    return {
        "version": 1,
        "kind": "capability_diff",
        "summary": {
            "operations_changed": len(operations),
            "expansions": counts["expansion"],
            "reductions": counts["reduction"],
            "other_changes": counts["changed"],
        },
        "operations": operations,
    }


def _render_value(value: Any) -> str:
    if value is None:
        return "∅"
    if isinstance(value, (dict, list)):
        import json

        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def format_capability_diff_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "## Capability diff",
        "",
        (
            f"Operations changed: **{summary['operations_changed']}** · "
            f"expansions: **{summary['expansions']}** · "
            f"reductions: **{summary['reductions']}** · "
            f"other: **{summary['other_changes']}**"
        ),
    ]
    if not report["operations"]:
        lines.extend(["", "No explicit capability changes detected."])
        return "\n".join(lines)

    for operation in report["operations"]:
        lines.extend(
            [
                "",
                f"### `{operation['operation']}` — {operation['classification']}",
            ]
        )
        for item in operation["changes"]:
            lines.append(
                f"- **{item['field']}** · {item['classification']}: "
                f"`{_render_value(item['before'])}` → "
                f"`{_render_value(item['after'])}`"
            )
    return "\n".join(lines)
