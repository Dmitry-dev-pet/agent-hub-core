from __future__ import annotations

from typing import Any

from .reference import ReferenceAdapter, RoutingError
from .validation import validate_document


def run_scenario() -> dict[str, Any]:
    instance = {
        "projects": [
            {"id": "demo-app", "repo": "example-org/demo-app", "aliases": ["demo app"]},
            {"id": "docs", "repo": "example-org/docs", "aliases": ["documentation"]},
            {"id": "build", "repo": "example-org/build", "aliases": ["builder"]},
            {"id": "runtime", "repo": "example-org/runtime", "aliases": ["runtime"]},
            {"id": "gpu-demo", "repo": "example-org/gpu-demo", "aliases": ["gpu demo"]},
        ]
    }
    live_state = {
        route["repo"]: {
            "default_branch": "main",
            "head": f"authoritative-{route['id']}-head",
        }
        for route in instance["projects"]
    }
    contracts = {
        "repo-admin": {
            "version": 1,
            "operations": {
                "create-repository": {
                    "agent_routable": True,
                    "trigger_prefix": "[create-repo] ",
                },
                "credential-export": {
                    "agent_routable": False,
                    "trigger_prefix": "[credential-export] ",
                    "reason": "Operator-only operation.",
                },
            },
        }
    }
    validate_document("control_plane", contracts["repo-admin"])

    first = ReferenceAdapter(instance, live_state, contracts)
    route = first.resolve("What is happening with demo app?")
    hydrated = first.hydrate(route)

    read_plan = first.plan(
        route["id"], "read", "github", ["live repository state was read"]
    )
    direct_plan = first.plan(
        route["id"],
        "direct_mutation",
        "github",
        ["issue metadata reflects requested change"],
    )
    privileged = first.resolve_control_plane_operation(
        "repo-admin", "create-repository"
    )
    privileged_plan = first.plan(
        route["id"],
        "privileged_mutation",
        "repo-admin",
        ["created repository exists in authoritative state"],
        operation="create-repository",
    )
    runtime_plan = first.plan(
        route["id"],
        "runtime",
        "workflow-runtime",
        ["workflow succeeds", "artifact exists"],
    )
    for plan in (read_plan, direct_plan, privileged_plan, runtime_plan):
        validate_document("execution_plan", plan)

    operator_only_rejected = False
    try:
        first.resolve_control_plane_operation(
            "repo-admin", "credential-export"
        )
    except RoutingError:
        operator_only_rejected = True
    if not operator_only_rejected:
        raise AssertionError("operator-only operation was not rejected")

    work_packet = {
        "version": 1,
        "project": route["id"],
        "outcome": {"description": "Build the validated project artifact."},
        "acceptance_proof": {
            "kind": "composite",
            "checks": ["workflow succeeds", "artifact exists"],
        },
        "execution_envelope": {
            "repositories": [route["repo"]],
            "allowed": ["workflow_dispatch", "artifact_read"],
            "forbidden": ["credential_change", "unrelated_repository_change"],
        },
        "preferred_level": "L1",
        "maximum_level": "L3",
    }
    validate_document("work_packet", work_packet)

    handoff = {
        "version": 1,
        "project": route["id"],
        "outcome": "Build the validated project artifact.",
        "verified_facts": [
            f"authoritative head is {hydrated['live']['head']}"
        ],
        "remaining_work": ["run build workflow", "verify artifact"],
        "acceptance_proof": ["workflow succeeds", "artifact exists"],
        "execution_envelope": {
            "repositories": [route["repo"]],
            "allowed": ["workflow_dispatch", "artifact_read"],
            "forbidden": ["credential_change"],
        },
        "authoritative_refs": [
            {"type": "repository", "value": route["repo"]}
        ],
    }
    validate_document("handoff_packet", handoff)

    receipt = {
        "version": 1,
        "status": "executed",
        "capability": "workflow-runtime",
        "authoritative_refs": [
            {"type": "workflow_run", "value": "fixture-run-1"}
        ],
        "observations": ["build workflow completed"],
    }
    validate_document("execution_receipt", receipt)

    for transition in [
        {"version": 1, "from": "resolved", "to": "planned"},
        {"version": 1, "from": "planned", "to": "executing"},
        {"version": 1, "from": "executing", "to": "executed"},
        {"version": 1, "from": "executed", "to": "verifying"},
        {"version": 1, "from": "verifying", "to": "verified"},
    ]:
        validate_document("lifecycle_transition", transition)

    verification = {
        "version": 1,
        "status": "verified",
        "checks": [
            {
                "name": "workflow succeeds",
                "passed": True,
                "evidence": [
                    {"type": "workflow_run", "value": "fixture-run-1"}
                ],
            },
            {
                "name": "artifact exists",
                "passed": True,
                "evidence": [
                    {"type": "artifact", "value": "fixture-artifact-1"}
                ],
            },
        ],
        "authoritative_refs": [
            {"type": "workflow_run", "value": "fixture-run-1"},
            {"type": "artifact", "value": "fixture-artifact-1"},
        ],
    }
    validate_document("verification_result", verification)

    second = ReferenceAdapter(instance, live_state, contracts)
    fresh_route = second.resolve("What is happening with demo app?")
    fresh_hydrated = second.hydrate(fresh_route)

    result = {
        "configured_repositories": len(instance["projects"]),
        "first_resolution": route["id"],
        "fresh_resolution": fresh_route["id"],
        "fresh_recovery_matches": fresh_hydrated == hydrated,
        "read_level": read_plan["selected_level"],
        "direct_mutation_level": direct_plan["selected_level"],
        "privileged_operation": privileged["trigger_prefix"].strip(),
        "privileged_level": privileged_plan["selected_level"],
        "operator_only_rejected": operator_only_rejected,
        "runtime_level": runtime_plan["selected_level"],
        "coding_agent_level": first.select_level("coding_agent"),
        "machine_bound_level": first.select_level("machine_bound"),
        "receipt_status": receipt["status"],
        "verification_status": verification["status"],
    }
    expected = {
        "configured_repositories": 5,
        "first_resolution": "demo-app",
        "fresh_resolution": "demo-app",
        "fresh_recovery_matches": True,
        "read_level": "L0",
        "direct_mutation_level": "L1",
        "privileged_operation": "[create-repo]",
        "privileged_level": "L2",
        "operator_only_rejected": True,
        "runtime_level": "L3",
        "coding_agent_level": "L4",
        "machine_bound_level": "L5",
        "receipt_status": "executed",
        "verification_status": "verified",
    }
    if result != expected:
        raise AssertionError(f"v0.1 conformance mismatch: {result!r}")
    return result
