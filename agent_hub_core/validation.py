from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

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
}


class ProtocolValidationError(ValueError):
    """Raised when a protocol document violates schema or semantic rules."""


def load_schema(kind: str) -> dict[str, Any]:
    try:
        filename = SCHEMA_FILES[kind]
    except KeyError as exc:
        raise ProtocolValidationError(
            f"unknown protocol document kind: {kind}"
        ) from exc

    resource = files("agent_hub_core.schemas.v0_1").joinpath(filename)
    return json.loads(resource.read_text(encoding="utf-8"))


def check_schemas() -> None:
    for kind in SCHEMA_FILES:
        Draft202012Validator.check_schema(load_schema(kind))


def validate_document(kind: str, document: dict[str, Any]) -> None:
    schema = load_schema(kind)
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
            if after not in {"blocked", "dormant"}:
                raise ProtocolValidationError(
                    "capability_activation_receipt: blocked activation must end in blocked or dormant"
                )
            if verification["passed"]:
                raise ProtocolValidationError(
                    "capability_activation_receipt: blocked activation cannot claim passed verification"
                )


def validate_file(kind: str, path: str | Path) -> None:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ProtocolValidationError(
            f"{source}: protocol document must be an object"
        )
    validate_document(kind, payload)
