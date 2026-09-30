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


def validate_file(kind: str, path: str | Path) -> None:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ProtocolValidationError(
            f"{source}: protocol document must be an object"
        )
    validate_document(kind, payload)
