import unittest

from agent_hub_core.reference import ReferenceAdapter
from agent_hub_core.tool_provider import (
    ToolProviderError,
    TruthrailToolProvider,
)


def control_plane(mode="manual_approval"):
    return {
        "version": 1,
        "operations": {
            "deploy": {
                "agent_routable": True,
                "trigger": "[deploy]",
                "admission": {
                    "mode": mode,
                    "requester": "repository_owner",
                },
            },
            "operator-only": {
                "agent_routable": False,
                "trigger": "[operator-only]",
                "reason": "Operator-only test operation.",
                "admission": {
                    "mode": "operator_only",
                    "requester": "repository_owner",
                },
            },
        },
    }


def provider(mode="manual_approval"):
    instance = {
        "projects": [
            {
                "id": "demo-app",
                "repo": "example-org/demo-app",
                "aliases": ["demo", "demo app"],
            }
        ]
    }
    live_state = {
        "example-org/demo-app": {
            "default_branch": "main",
            "head": "abc123",
            "open_prs": 1,
        }
    }
    contracts = {"repo-admin": control_plane(mode)}
    adapter = ReferenceAdapter(instance, live_state, contracts)
    return TruthrailToolProvider(
        adapter,
        contracts,
        actor="example-owner",
        owner="example-owner",
    )


class TruthrailToolProviderTests(unittest.TestCase):
    def test_lists_three_bounded_tools(self):
        names = [item["name"] for item in provider().list_tools()]
        self.assertEqual(
            names,
            [
                "truthrail_status",
                "truthrail_dispatch",
                "truthrail_approve",
            ],
        )

    def test_status_reads_live_state_without_execution(self):
        result = provider().call("truthrail_status", {"project": "demo"})
        self.assertEqual(result["state"], "current")
        self.assertEqual(result["project"], "demo-app")
        self.assertEqual(result["live"]["head"], "abc123")
        self.assertFalse(result["executed"])

    def test_manual_approval_end_to_end_releases_handoff_only(self):
        tools = provider()
        dispatched = tools.call(
            "truthrail_dispatch",
            {
                "project": "demo-app",
                "requirement": "privileged_mutation",
                "capability": "repo-admin",
                "operation": "deploy",
                "acceptance_proof": ["deployment state is visible from the provider"],
            },
        )
        self.assertEqual(dispatched["state"], "approval_required")
        self.assertEqual(dispatched["admission"]["decision"], "REQUIRE_HUMAN")
        self.assertFalse(dispatched["executed"])

        approved = tools.call(
            "truthrail_approve",
            {
                "approval_id": dispatched["approval_id"],
                "approve": True,
            },
        )
        self.assertEqual(approved["state"], "approved_for_handoff")
        self.assertFalse(approved["executed"])

        repeated = tools.call(
            "truthrail_approve",
            {
                "approval_id": dispatched["approval_id"],
                "approve": True,
            },
        )
        self.assertEqual(repeated, approved)

    def test_rejection_closes_pending_approval(self):
        tools = provider()
        dispatched = tools.dispatch(
            project="demo",
            requirement="privileged_mutation",
            capability="repo-admin",
            operation="deploy",
            acceptance_proof=["provider state is checked"],
        )
        rejected = tools.approve(dispatched["approval_id"], False)
        self.assertEqual(rejected["state"], "rejected")
        self.assertFalse(rejected["executed"])

    def test_automatic_operation_is_admitted_but_not_executed(self):
        result = provider("automatic").dispatch(
            project="demo",
            requirement="privileged_mutation",
            capability="repo-admin",
            operation="deploy",
            acceptance_proof=["provider state is checked"],
        )
        self.assertEqual(result["state"], "admitted_for_handoff")
        self.assertEqual(result["admission"]["decision"], "ADMIT")
        self.assertFalse(result["executed"])

    def test_operator_only_operation_is_denied(self):
        result = provider().dispatch(
            project="demo",
            requirement="privileged_mutation",
            capability="repo-admin",
            operation="operator-only",
            acceptance_proof=["provider state is checked"],
        )
        self.assertEqual(result["state"], "denied")
        self.assertEqual(result["admission"]["decision"], "DENY")
        self.assertFalse(result["executed"])

    def test_unknown_approval_fails_closed(self):
        with self.assertRaises(ToolProviderError):
            provider().approve("missing", True)


if __name__ == "__main__":
    unittest.main()
