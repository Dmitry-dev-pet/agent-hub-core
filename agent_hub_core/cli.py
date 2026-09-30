from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .conformance import run_scenario
from .validation import SCHEMA_FILES, check_schemas, validate_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-hub-core",
        description="Validate and exercise the Agent Hub Core v0.1 protocol.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate one protocol JSON document.")
    validate.add_argument("--kind", choices=sorted(SCHEMA_FILES), required=True)
    validate.add_argument("path", type=Path)

    sub.add_parser("check-schemas", help="Validate all bundled JSON Schemas.")
    sub.add_parser("conformance", help="Run the deterministic v0.1 conformance scenario.")
    sub.add_parser("list-kinds", help="List supported protocol document kinds.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate":
        validate_file(args.kind, args.path)
        print(f"OK: {args.kind} {args.path}")
        return 0
    if args.command == "check-schemas":
        check_schemas()
        print(f"OK: {len(SCHEMA_FILES)} schemas")
        return 0
    if args.command == "conformance":
        print(json.dumps(run_scenario(), indent=2, sort_keys=True))
        return 0
    if args.command == "list-kinds":
        for kind in sorted(SCHEMA_FILES):
            print(kind)
        return 0
    raise AssertionError(args.command)
