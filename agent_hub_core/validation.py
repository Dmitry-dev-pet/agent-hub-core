from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


LEVEL_ORDER = {f"L{i}": i for i in range(6)}
SCHEMA_FILES = {
    "work_packet": "work-packet.schema.json",
    "handoff_packet": "handoff-packet.schema.json",
    "execution_plan": "execution-plan.schema.json",
    "execution_receipt": "execution-receipt.schema.json",
    "verification_result": "verification-result.schema.json",
    "lifecycle_transition": "lifecycle-transition.schema.json",
    "control_plane": "control-plane.schema.json",
    "onboarding_receipt": "onboarding-receipt.schema.json",
    "capability_readiness": "capability-readiness.schema.json",
    "capability_activation_receipt": "capability-activation-receipt.schema.json",
    "capability_policy_decision": "capability-policy-decision.schema.json",
    "operation_admission_decision": "operation-admission-decision.schema.json",
}

CONTINUITY_SCHEMA_FILES = {
    kind: SCHEMA_FILES[kind]
    for kind in (
        "work_packet",
        "handoff_packet",
        "execution_plan",
        "execution_receipt",
        "verification_result",
        "lifecycle_transition",
    )
}
SCHEMA_FILES_BY_VERSION = {
    "0.1": SCHEMA_FILES,
    "0.2": CONTINUITY_SCHEMA_FILES,
}
SCHEMA_PACKAGES = {
    "0.1": "agent_hub_core.schemas.v0_1",
    "0.2": "agent_hub_core.schemas.v0_2",
}


class ProtocolValidationError(ValueError):
    """Raised when a protocol document violates schema or semantic rules."""


def load_schema(kind: str, schema_version: str = "0.1") -> dict[str, Any]:
    try:
        version_files = SCHEMA_FILES_BY_VERSION[schema_version]
        package = SCHEMA_PACKAGES[schema_version]
    except KeyError as exc:
        raise ProtocolValidationError(
            f"unknown protocol schema version: {schema_version}"
        ) from exc

    try:
        filename = version_files[kind]
    except KeyError as exc:
        raise ProtocolValidationError(
            f"{kind} is not defined in protocol schema version {schema_version}"
        ) from exc

    resource = files(package).joinpath(filename)
    return json.loads(resource.read_text(encoding="utf-8"))


def check_schemas(schema_version: str | None = None) -> None:
    versions = [schema_version] if schema_version is not None else list(SCHEMA_FILES_BY_VERSION)
    for version in versions:
        if version not in SCHEMA_FILES_BY_VERSION:
            raise ProtocolValidationError(
                f"unknown protocol schema version: {version}"
            )
        for kind in SCHEMA_FILES_BY_VERSION[version]:
            Draft202012Validator.check_schema(load_schema(kind, version))


def validate_document(
    kind: str,
    document: dict[str, Any],
    schema_version: str = "0.1",
) -> None:
    schema = load_schema(kind, schema_version)
    try:
        Draft202012Validator(schema).validate(document)
    except ValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path)
        label = f"{kind}.{path}" if path else kind
        raise ProtocolValidationError(f"{label}: {exc.message}") from exc

    if kind == "work_packet":
        preferred = document["preferred_level"]
        maximum = document["maximum_level"]
        if LEVEL_ORDER[preferred] > LEVEL_ORDER[maximum]:
            raise ProtocolValidationError(
                "work_packet: preferred_level must not exceed maximum_level"
            )
        envelope = document["execution_envelope"]
        overlap = set(envelope["allowed"]) & set(envelope["forbidden"])
        if overlap:
            raise ProtocolValidationError(
                "work_packet: allowed and forbidden overlap: "
                + ", ".join(sorted(overlap))
            )

    if kind == "onboarding_receipt":
        unresolved = document["unresolved"]
        inventory = document["inventory"]
        phases = document["phases"]
        recovery = document["fresh_recovery"]

        if inventory["repositories_recorded"] > inventory["repositories_seen"]:
            raise ProtocolValidationError(
                "onboarding_receipt: repositories_recorded cannot exceed repositories_seen"
            )

        if document["status"] == "verified":
            if inventory["repositories_recorded"] != inventory["repositories_seen"]:
                raise ProtocolValidationError(
                    "onboarding_receipt: verified onboarding must record every discovered repository"
                )
            if unresolved:
                raise ProtocolValidationError(
                    "onboarding_receipt: verified onboarding cannot contain unresolved items"
                )
            for phase in ("discover", "classify", "build", "validate", "receipt"):
                if phases[phase] != "completed":
                    raise ProtocolValidationError(
                        f"onboarding_receipt: verified onboarding requires {phase}=completed"
                    )
            if phases["watch"] not in {"completed", "skipped"}:
                raise ProtocolValidationError(
                    "onboarding_receipt: verified onboarding requires watch completed or skipped"
                )
            if not recovery["performed"] or not recovery["passed"]:
                raise ProtocolValidationError(
                    "onboarding_receipt: verified onboarding requires successful fresh recovery"
                )

        if document["status"] == "partial":
            if inventory["repositories_recorded"] != inventory["repositories_seen"]:
                raise ProtocolValidationError(
                    "onboarding_receipt: partial onboarding must still record every discovered repository"
                )
            if not unresolved:
                raise ProtocolValidationError(
                    "onboarding_receipt: partial onboarding requires at least one unresolved item"
                )
            for phase in ("discover", "classify", "build", "validate", "receipt"):
                if phases[phase] != "completed":
                    raise ProtocolValidationError(
                        f"onboarding_receipt: partial onboarding requires {phase}=completed"
                    )
            if phases["watch"] not in {"completed", "skipped"}:
                raise ProtocolValidationError(
                    "onboarding_receipt: partial onboarding requires watch completed or skipped"
                )
            if not recovery["performed"] or not recovery["passed"]:
                raise ProtocolValidationError(
                    "onboarding_receipt: partial onboarding requires successful fresh recovery"
                )


    if kind == "capability_readiness":
        state = document["state"]
        prerequisites = document["prerequisites"]
        limitations = document["limitations"]
        activation = document["activation"]
        missing_required = [
            item
            for item in prerequisites
            if item["required_for_ready"] and item["status"] == "missing"
        ]

        if state == "ready":
            if missing_required:
                raise ProtocolValidationError(
                    "capability_readiness: ready capability cannot have missing required prerequisites"
                )
            if limitations:
                raise ProtocolValidationError(
                    "capability_readiness: ready capability cannot have limitations"
                )

        if state == "degraded":
            if not missing_required:
                raise ProtocolValidationError(
                    "capability_readiness: degraded capability requires a missing prerequisite required_for_ready"
                )
            if not limitations:
                raise ProtocolValidationError(
                    "capability_readiness: degraded capability requires at least one limitation"
                )

        if state == "dormant":
            if not activation["available"]:
                raise ProtocolValidationError(
                    "capability_readiness: dormant capability must have an available activation route"
                )
            if not missing_required:
                raise ProtocolValidationError(
                    "capability_readiness: dormant capability requires a missing prerequisite required_for_ready"
                )

        if state == "blocked":
            if not missing_required and activation["available"]:
                raise ProtocolValidationError(
                    "capability_readiness: blocked capability requires a missing prerequisite or unavailable activation route"
                )

    if kind == "capability_activation_receipt":
        status = document["status"]
        after = document["state_after"]
        prerequisites = document["prerequisites_checked"]
        actions = document["actions"]
        limitations = document["limitations_remaining"]
        verification = document["verification"]

        missing_required = [
            item
            for item in prerequisites
            if item["required_for_ready"] and item["status"] == "missing"
        ]
        failed_actions = [item for item in actions if item["result"] == "failed"]

        if status == "verified":
            if after != "ready":
                raise ProtocolValidationError(
                    "capability_activation_receipt: verified activation must end in ready"
                )
            if missing_required:
                raise ProtocolValidationError(
                    "capability_activation_receipt: verified activation cannot have missing required prerequisites"
                )
            if failed_actions:
                raise ProtocolValidationError(
                    "capability_activation_receipt: verified activation cannot contain failed actions"
                )
            if limitations:
                raise ProtocolValidationError(
                    "capability_activation_receipt: verified activation cannot have remaining limitations"
                )
            if not verification["performed"] or not verification["passed"]:
                raise ProtocolValidationError(
                    "capability_activation_receipt: verified activation requires successful verification"
                )

        if status == "partial":
            if after != "degraded":
                raise ProtocolValidationError(
                    "capability_activation_receipt: partial activation must end in degraded"
                )
            if not limitations:
                raise ProtocolValidationError(
                    "capability_activation_receipt: partial activation requires remaining limitations"
                )
            if not verification["performed"] or not verification["passed"]:
                raise ProtocolValidationError(
                    "capability_activation_receipt: partial activation requires successful verification of degraded mode"
                )

        if status == "blocked":
            if after not in {"blocked", "dormant", "degraded"}:
                raise ProtocolValidationError(
                    "capability_activation_receipt: blocked activation must preserve degraded/dormant state or end blocked"
                )
            if verification["passed"]:
                raise ProtocolValidationError(
                    "capability_activation_receipt: blocked activation cannot claim passed verification"
                )


def validate_file(
    kind: str,
    path: str | Path,
    schema_version: str = "0.1",
) -> None:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ProtocolValidationError(
            f"{source}: protocol document must be an object"
        )
    validate_document(kind, payload, schema_version=schema_version)


def validate_run_bundle(
    documents: Sequence[tuple[str, dict[str, Any]]],
) -> str:
    if not documents:
        raise ProtocolValidationError("run bundle must contain at least one document")

    run_ids: set[str] = set()
    for kind, document in documents:
        if kind not in CONTINUITY_SCHEMA_FILES:
            raise ProtocolValidationError(
                f"run bundle does not support document kind: {kind}"
            )
        validate_document(kind, document, schema_version="0.2")
        run_ids.add(str(document["run_id"]))

    if len(run_ids) != 1:
        raise ProtocolValidationError(
            "run bundle mixes run_id values: " + ", ".join(sorted(run_ids))
        )
    return next(iter(run_ids))
