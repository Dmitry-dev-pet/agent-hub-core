from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .capability_diff import diff_control_planes, format_capability_diff_markdown
from .capability_policy import evaluate_control_plane_policy, format_capability_policy_markdown
from .conformance import run_scenario
from .instance import (
    InstanceValidationError,
    bootstrap_acceptance,
    doctor_instance,
    init_instance,
    validate_instance,
)
from .validation import ProtocolValidationError, SCHEMA_FILES, check_schemas, validate_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-hub-core",
        description="Bootstrap, validate, and exercise Agent Hub Core.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser(
        "init",
        help="Create a zero-custom-secret Agent Hub instance.",
    )
    init.add_argument("path", nargs="?", type=Path, default=Path(".agent-hub"))
    init.add_argument("--owner", required=True)
    init.add_argument(
        "--project",
        action="append",
        default=[],
        help="Public owner/repository to add; repeat for multiple projects.",
    )
    init.add_argument("--force", action="store_true")

    validate_instance_cmd = sub.add_parser(
        "validate-instance",
        help="Validate an Agent Hub instance directory.",
    )
    validate_instance_cmd.add_argument(
        "path", nargs="?", type=Path, default=Path(".agent-hub")
    )

    doctor = sub.add_parser(
        "doctor",
        help="Validate an instance and optionally check public GitHub reachability.",
    )
    doctor.add_argument(
        "path", nargs="?", type=Path, default=Path(".agent-hub")
    )
    doctor.add_argument(
        "--offline",
        action="store_true",
        help="Skip network checks.",
    )

    validate = sub.add_parser(
        "validate", help="Validate one protocol JSON document."
    )
    validate.add_argument("--kind", choices=sorted(SCHEMA_FILES), required=True)
    validate.add_argument("path", type=Path)

    sub.add_parser("check-schemas", help="Validate all bundled JSON Schemas.")
    sub.add_parser(
        "conformance", help="Run the deterministic v0.1 protocol scenario."
    )
    sub.add_parser(
        "bootstrap-acceptance",
        help="Prove a second instance starts with zero custom secrets.",
    )
    capability_diff = sub.add_parser(
        "capability-diff",
        help="Compare two reviewed control-plane contracts without executing them.",
    )
    capability_diff.add_argument("before", type=Path)
    capability_diff.add_argument("after", type=Path)
    capability_diff.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
    )
    capability_diff.add_argument(
        "--fail-on-expansion",
        action="store_true",
        help="Exit with status 2 when explicit authority expands.",
    )

    capability_policy = sub.add_parser(
        "capability-policy",
        help="Evaluate the default v1 policy for a reviewed control-plane change.",
    )
    capability_policy.add_argument("before", type=Path)
    capability_policy.add_argument("after", type=Path)
    capability_policy.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
    )
    capability_policy.add_argument(
        "--fail-on",
        choices=("none", "block", "review"),
        default="none",
        help="Optional CI enforcement threshold.",
    )

    sub.add_parser("list-kinds", help="List supported protocol document kinds.")
    return parser


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            _print_json(
                init_instance(
                    args.path,
                    owner=args.owner,
                    projects=args.project,
                    force=args.force,
                )
            )
            return 0
        if args.command == "validate-instance":
            _print_json(validate_instance(args.path))
            return 0
        if args.command == "doctor":
            result = doctor_instance(args.path, network=not args.offline)
            _print_json(result)
            return 0 if result["ok"] else 1
        if args.command == "validate":
            validate_file(args.kind, args.path)
            print(f"OK: {args.kind} {args.path}")
            return 0
        if args.command == "check-schemas":
            check_schemas()
            print(f"OK: {len(SCHEMA_FILES)} schemas")
            return 0
        if args.command == "conformance":
            _print_json(run_scenario())
            return 0
        if args.command == "bootstrap-acceptance":
            _print_json(bootstrap_acceptance())
            return 0
        if args.command == "capability-diff":
            before = json.loads(args.before.read_text(encoding="utf-8"))
            after = json.loads(args.after.read_text(encoding="utf-8"))
            if not isinstance(before, dict) or not isinstance(after, dict):
                raise ProtocolValidationError(
                    "capability-diff inputs must both be JSON objects"
                )
            report = diff_control_planes(before, after)
            if args.format == "json":
                _print_json(report)
            else:
                print(format_capability_diff_markdown(report))
            if args.fail_on_expansion and report["summary"]["expansions"]:
                return 2
            return 0
        if args.command == "capability-policy":
            before = json.loads(args.before.read_text(encoding="utf-8"))
            after = json.loads(args.after.read_text(encoding="utf-8"))
            if not isinstance(before, dict) or not isinstance(after, dict):
                raise ProtocolValidationError(
                    "capability-policy inputs must both be JSON objects"
                )
            decision = evaluate_control_plane_policy(before, after)
            if args.format == "json":
                _print_json(decision)
            else:
                print(format_capability_policy_markdown(decision))
            if args.fail_on == "block" and decision["decision"] == "BLOCK":
                return 2
            if args.fail_on == "review" and decision["decision"] in {"REVIEW", "BLOCK"}:
                return 3
            return 0
        if args.command == "list-kinds":
            for kind in sorted(SCHEMA_FILES):
                print(kind)
            return 0
    except (InstanceValidationError, ProtocolValidationError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    raise AssertionError(args.command)
