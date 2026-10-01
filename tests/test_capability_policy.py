import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import yaml

from agent_hub_core.capability_diff import diff_control_planes
from agent_hub_core.capability_policy import (
    POLICY_ID,
    evaluate_capability_policy,
    evaluate_control_plane_policy,
    format_capability_policy_markdown,
)
from agent_hub_core.cli import main


ROOT = Path(__file__).resolve().parents[1]


def contract(operation):
    return {"version": 1, "operations": {"op": operation}}


class CapabilityPolicyTests(unittest.TestCase):
    def test_permission_expansion_requires_review(self):
        decision = evaluate_control_plane_policy(
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "github_permissions": {"contents": "read"},
                }
            ),
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "github_permissions": {"contents": "write"},
                }
            ),
        )
        self.assertEqual(decision["decision"], "REVIEW")
        self.assertEqual(decision["findings"][0]["rule_id"], "TRP100")

    def test_new_credential_requires_review(self):
        decision = evaluate_control_plane_policy(
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "credential_refs": [],
                }
            ),
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "credential_refs": ["NEW_TOKEN"],
                }
            ),
        )
        self.assertEqual(decision["decision"], "REVIEW")

    def test_human_gate_removal_blocks(self):
        decision = evaluate_control_plane_policy(
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "human_gate": "approval",
                }
            ),
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "human_gate": "none",
                }
            ),
        )
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertEqual(decision["findings"][0]["rule_id"], "TRP003")

    def test_enabling_agent_routing_blocks(self):
        decision = evaluate_control_plane_policy(
            contract(
                {
                    "agent_routable": False,
                    "trigger": "[op]",
                    "reason": "operator only",
                }
            ),
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                }
            ),
        )
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertEqual(decision["findings"][0]["rule_id"], "TRP002")

    def test_new_agent_routable_operation_blocks(self):
        before = {
            "version": 1,
            "operations": {
                "existing": {"agent_routable": True, "trigger": "[existing]"}
            },
        }
        after = {
            "version": 1,
            "operations": {
                "existing": {"agent_routable": True, "trigger": "[existing]"},
                "new-op": {
                    "agent_routable": True,
                    "trigger": "[new-op]",
                },
            },
        }
        decision = evaluate_control_plane_policy(before, after)
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertEqual(decision["findings"][0]["rule_id"], "TRP001")

    def test_reduction_passes(self):
        decision = evaluate_control_plane_policy(
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "github_permissions": {"contents": "write"},
                }
            ),
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "github_permissions": {"contents": "read"},
                }
            ),
        )
        self.assertEqual(decision["decision"], "PASS")
        self.assertEqual(decision["findings"], [])

    def test_legacy_baseline_declaration_is_review(self):
        before = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
            }
        )
        after = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "runtime_auth": "reviewed-token",
            }
        )
        decision = evaluate_control_plane_policy(before, after)
        self.assertEqual(decision["decision"], "REVIEW")
        self.assertEqual(decision["findings"][0]["rule_id"], "TRP101")

    def test_policy_file_matches_runtime_id(self):
        payload = yaml.safe_load(
            (ROOT / "capabilities" / "policy-v1.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["id"], POLICY_ID)
        self.assertEqual(
            {rule["decision"] for rule in payload["rules"].values()},
            {"BLOCK", "REVIEW"},
        )
        self.assertTrue(payload["principles"]["no_llm_judgment"])

    def test_markdown_surfaces_decision(self):
        report = diff_control_planes(
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "cost_ceiling": {"amount": 10, "unit": "usd"},
                }
            ),
            contract(
                {
                    "agent_routable": True,
                    "trigger": "[op]",
                    "cost_ceiling": {"amount": 20, "unit": "usd"},
                }
            ),
        )
        rendered = format_capability_policy_markdown(
            evaluate_capability_policy(report)
        )
        self.assertIn("Decision: **REVIEW**", rendered)
        self.assertIn("TRP100", rendered)

    def test_cli_fail_on_block(self):
        before = contract(
            {
                "agent_routable": False,
                "trigger": "[op]",
                "reason": "operator only",
            }
        )
        after = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            before_path = root / "before.json"
            after_path = root / "after.json"
            before_path.write_text(json.dumps(before), encoding="utf-8")
            after_path.write_text(json.dumps(after), encoding="utf-8")
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(
                    [
                        "capability-policy",
                        str(before_path),
                        str(after_path),
                        "--format",
                        "json",
                        "--fail-on",
                        "block",
                    ]
                )
        self.assertEqual(code, 2)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["decision"], "BLOCK")

    def test_cli_review_is_nonblocking_when_fail_on_block(self):
        before = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "github_permissions": {"contents": "read"},
            }
        )
        after = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "github_permissions": {"contents": "write"},
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            before_path = root / "before.json"
            after_path = root / "after.json"
            before_path.write_text(json.dumps(before), encoding="utf-8")
            after_path.write_text(json.dumps(after), encoding="utf-8")
            with redirect_stdout(StringIO()):
                code = main(
                    [
                        "capability-policy",
                        str(before_path),
                        str(after_path),
                        "--fail-on",
                        "block",
                    ]
                )
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
