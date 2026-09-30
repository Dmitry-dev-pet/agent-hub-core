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
        self.assertEqual(set(payload["operations"]), {"demo-increment"})
        operation = payload["operations"]["demo-increment"]
        self.assertTrue(operation["agent_routable"])
        self.assertEqual(operation["trigger_prefix"], "[demo-increment] ")
        self.assertEqual(operation["credential_refs"], [])
        self.assertEqual(operation["execution_level"], "L2")

    def test_state_is_well_formed(self) -> None:
        state = json.loads((ROOT / "demo" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["version"], 1)
        self.assertIsInstance(state["counter"], int)
        self.assertGreaterEqual(state["counter"], 0)
        self.assertIsInstance(state["history"], list)

    def test_workflow_references_public_state_and_owner_gate(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "cross-vendor-demo.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "github.event.issue.user.login == github.repository_owner", workflow
        )
        self.assertIn("demo/state.json", workflow)
        self.assertIn("git show origin/main:demo/state.json", workflow)


if __name__ == "__main__":
    unittest.main()
