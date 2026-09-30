from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CrossVendorDemoTests(unittest.TestCase):
    def test_control_plane_is_narrow_and_routable(self) -> None:
        payload = json.loads(
            (ROOT / "demo" / "control-plane.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["version"], 1)
        self.assertEqual(set(payload["operations"]), {"demo-record"})
        operation = payload["operations"]["demo-record"]
        self.assertTrue(operation["agent_routable"])
        self.assertEqual(operation["credential_refs"], [])
        self.assertEqual(operation["execution_level"], "L1")
        self.assertEqual(operation["execution_surface"], "github_issue_create")
        self.assertEqual(operation["index_issue"], 5)

    def test_policy_requires_read_back_verification(self) -> None:
        policy = (ROOT / "demo" / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Re-read the newly created issue", policy)
        self.assertIn("Executed is not verified", policy)
        self.assertIn("Do not edit repository files", policy)

    def test_public_readme_keeps_same_operation_for_both_hosts(self) -> None:
        readme = (ROOT / "demo" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Client: chatgpt.", readme)
        self.assertIn("Client: grok.", readme)
        self.assertIn("The operation and policy are identical", readme)
        self.assertIn("[agent-hub-demo] <client>", readme)


if __name__ == "__main__":
    unittest.main()
