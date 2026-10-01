import unittest

from agent_hub_core.capability_diff import (
    diff_control_planes,
    format_capability_diff_markdown,
)


def contract(operation):
    return {"version": 1, "operations": {"op": operation}}


class CapabilityDiffTests(unittest.TestCase):
    def test_read_to_write_is_expansion(self):
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
        report = diff_control_planes(before, after)
        self.assertEqual(report["summary"]["expansions"], 1)
        change = report["operations"][0]["changes"][0]
        self.assertEqual(change["field"], "github_permissions.contents")
        self.assertEqual(change["classification"], "expansion")

    def test_new_credential_and_side_effect_are_expansions(self):
        before = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "credential_refs": [],
                "external_side_effects": [],
            }
        )
        after = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "credential_refs": ["DEPLOY_TOKEN"],
                "external_side_effects": ["deployment.production"],
            }
        )
        report = diff_control_planes(before, after)
        self.assertEqual(report["summary"]["expansions"], 2)
        fields = {item["field"] for item in report["operations"][0]["changes"]}
        self.assertEqual(fields, {"credential_refs", "external_side_effects"})

    def test_removing_human_gate_is_expansion(self):
        before = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "human_gate": "approval",
            }
        )
        after = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "human_gate": "none",
            }
        )
        report = diff_control_planes(before, after)
        self.assertEqual(report["operations"][0]["classification"], "expansion")

    def test_adding_human_gate_is_reduction(self):
        before = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "human_gate": "none",
            }
        )
        after = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "human_gate": "review",
            }
        )
        report = diff_control_planes(before, after)
        self.assertEqual(report["summary"]["reductions"], 1)

    def test_cost_ceiling_increase_is_expansion(self):
        before = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "cost_ceiling": {"amount": 5, "unit": "usd"},
            }
        )
        after = contract(
            {
                "agent_routable": True,
                "trigger": "[op]",
                "cost_ceiling": {"amount": 10, "unit": "usd"},
            }
        )
        report = diff_control_planes(before, after)
        self.assertEqual(report["summary"]["expansions"], 1)

    def test_non_routable_operation_addition_is_not_agent_expansion(self):
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
                "operator-only": {
                    "agent_routable": False,
                    "trigger": "[operator-only]",
                    "reason": "Operator only.",
                },
            },
        }
        report = diff_control_planes(before, after)
        self.assertEqual(report["summary"]["expansions"], 0)
        self.assertEqual(report["operations"][0]["classification"], "changed")

    def test_markdown_is_compact_and_deterministic(self):
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
        rendered = format_capability_diff_markdown(diff_control_planes(before, after))
        self.assertIn("## Capability diff", rendered)
        self.assertIn("github_permissions.contents", rendered)
        self.assertIn("read", rendered)
        self.assertIn("write", rendered)


if __name__ == "__main__":
    unittest.main()
