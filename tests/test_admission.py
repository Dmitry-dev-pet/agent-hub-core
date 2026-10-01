import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import yaml

from agent_hub_core.admission import (
    POLICY_ID,
    evaluate_operation_admission,
    format_operation_admission_markdown,
)
from agent_hub_core.cli import main


ROOT = Path(__file__).resolve().parents[1]


def contract(operation, *, name="op"):
    return {"version": 1, "operations": {name: operation}}


class RuntimeAdmissionTests(unittest.TestCase):
    def test_owner_agent_route_is_admitted(self):
        decision = evaluate_operation_admission(
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "admission": {
                        "mode": "automatic",
                        "requester": "repository_owner"
                    }
                }
            ),
            "op",
            actor="owner",
            owner="owner",
            route="agent",
        )
        self.assertEqual(decision["decision"], "ADMIT")
        self.assertEqual(decision["requirements"], [])

    def test_wrong_actor_is_denied_before_authority(self):
        decision = evaluate_operation_admission(
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "admission": {
                        "mode": "automatic",
                        "requester": "repository_owner"
                    }
                }
            ),
            "op",
            actor="other-user",
            owner="owner",
            route="agent",
        )
        self.assertEqual(decision["decision"], "DENY")
        self.assertEqual(decision["findings"][0]["rule_id"], "TRA003")

    def test_agent_route_to_operator_only_is_denied(self):
        decision = evaluate_operation_admission(
            contract(
                {
                    "agent_routable": False,
                    "trigger": "[op]",
                    "reason": "operator only",
                    "admission": {
                        "mode": "operator_only",
                        "requester": "repository_owner"
                    }
                }
            ),
            "op",
            actor="owner",
            owner="owner",
            route="agent",
        )
        self.assertEqual(decision["decision"], "DENY")
        rules = {item["rule_id"] for item in decision["findings"]}
        self.assertIn("TRA002", rules)
        self.assertIn("TRA005", rules)

    def test_operator_route_can_admit_operator_only(self):
        decision = evaluate_operation_admission(
            contract(
                {
                    "agent_routable": False,
                    "trigger": "[op]",
                    "reason": "operator only",
                    "admission": {
                        "mode": "operator_only",
                        "requester": "repository_owner"
                    }
                }
            ),
            "op",
            actor="owner",
            owner="owner",
            route="operator",
        )
        self.assertEqual(decision["decision"], "ADMIT")
        self.assertEqual(decision["findings"][0]["rule_id"], "TRA102")

    def test_manual_approval_requires_human(self):
        decision = evaluate_operation_admission(
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "admission": {
                        "mode": "manual_approval",
                        "requester": "repository_owner"
                    }
                }
            ),
            "op",
            actor="owner",
            owner="owner",
            route="agent",
        )
        self.assertEqual(decision["decision"], "REQUIRE_HUMAN")
        self.assertEqual(decision["requirements"], ["manual_approval"])

    def test_provider_interaction_is_admitted_with_requirement(self):
        decision = evaluate_operation_admission(
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "admission": {
                        "mode": "provider_interaction",
                        "requester": "repository_owner"
                    }
                }
            ),
            "op",
            actor="owner",
            owner="owner",
            route="agent",
        )
        self.assertEqual(decision["decision"], "ADMIT")
        self.assertEqual(decision["requirements"], ["provider_interaction"])

    def test_missing_admission_is_denied(self):
        decision = evaluate_operation_admission(
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]"
                }
            ),
            "op",
            actor="owner",
            owner="owner",
            route="agent",
        )
        self.assertEqual(decision["decision"], "DENY")
        self.assertEqual(decision["findings"][0]["rule_id"], "TRA004")

    def test_unknown_operation_is_denied(self):
        decision = evaluate_operation_admission(
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "admission": {
                        "mode": "automatic",
                        "requester": "repository_owner"
                    }
                }
            ),
            "missing",
            actor="owner",
            owner="owner",
            route="agent",
        )
        self.assertEqual(decision["decision"], "DENY")
        self.assertEqual(decision["findings"][0]["rule_id"], "TRA001")

    def test_decision_has_stable_hashes(self):
        payload = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "admission": {
                    "mode": "automatic",
                    "requester": "repository_owner"
                }
            }
        )
        first = evaluate_operation_admission(
            payload, "op", actor="owner", owner="owner"
        )
        second = evaluate_operation_admission(
            payload, "op", actor="owner", owner="owner"
        )
        self.assertEqual(first["contract_sha256"], second["contract_sha256"])
        self.assertEqual(first["operation_sha256"], second["operation_sha256"])

    def test_policy_file_matches_runtime(self):
        policy = yaml.safe_load(
            (ROOT / "capabilities" / "admission-v1.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(policy["version"], 1)
        self.assertEqual(policy["id"], POLICY_ID)
        self.assertTrue(policy["principles"]["fail_closed_on_missing_contract_metadata"])

    def test_markdown_surfaces_admission(self):
        decision = evaluate_operation_admission(
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "admission": {
                        "mode": "provider_interaction",
                        "requester": "repository_owner"
                    }
                }
            ),
            "op",
            actor="owner",
            owner="owner",
        )
        rendered = format_operation_admission_markdown(decision)
        self.assertIn("Decision: **ADMIT**", rendered)
        self.assertIn("provider_interaction", rendered)

    def test_cli_require_admit_fails_on_deny(self):
        payload = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "admission": {
                    "mode": "automatic",
                    "requester": "repository_owner"
                }
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "control-plane.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with redirect_stdout(StringIO()):
                code = main(
                    [
                        "admit-operation",
                        str(path),
                        "--operation",
                        "op",
                        "--actor",
                        "other",
                        "--owner",
                        "owner",
                        "--route",
                        "agent",
                        "--require-admit",
                    ]
                )
        self.assertEqual(code, 2)

    def test_cli_require_admit_accepts_admit(self):
        payload = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "admission": {
                    "mode": "automatic",
                    "requester": "repository_owner"
                }
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "control-plane.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(
                    [
                        "admit-operation",
                        str(path),
                        "--operation",
                        "op",
                        "--actor",
                        "owner",
                        "--owner",
                        "owner",
                        "--route",
                        "agent",
                        "--format",
                        "json",
                        "--require-admit",
                    ]
                )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["decision"], "ADMIT")


if __name__ == "__main__":
    unittest.main()
