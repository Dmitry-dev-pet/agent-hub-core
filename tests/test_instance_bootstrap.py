import tempfile
import unittest
from pathlib import Path

import yaml

from agent_hub_core.instance import (
    InstanceValidationError,
    bootstrap_acceptance,
    doctor_instance,
    init_instance,
    validate_instance,
)


class InstanceBootstrapTests(unittest.TestCase):
    def test_init_is_zero_custom_secret_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".agent-hub"
            result = init_instance(
                root,
                owner="example-org",
                projects=[
                    "example-org/project-one",
                    "example-org/project-two",
                ],
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["projects"], 2)
            self.assertEqual(result["credential_routes"], 0)
            self.assertEqual(result["custom_credentials_required"], 0)
            self.assertEqual(result["credential_mode"], "zero-custom-secret")

            credentials = yaml.safe_load(
                (root / "credentials.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual(credentials["credential_routes"], {})

            capabilities = yaml.safe_load(
                (root / "capabilities.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual(
                capabilities["capabilities"]["github-public"]["authentication"],
                "none",
            )
            self.assertEqual(
                capabilities["capabilities"]["github-actions"]["authentication"],
                "provider_managed",
            )

    def test_doctor_offline_needs_no_custom_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".agent-hub"
            init_instance(root, owner="example-org")
            result = doctor_instance(root, network=False)

            self.assertTrue(result["ok"])
            self.assertEqual(result["network_mode"], "offline")
            self.assertEqual(result["custom_credentials_required"], 0)
            self.assertEqual(result["project_checks"], [])

    def test_init_refuses_nonempty_directory_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".agent-hub"
            root.mkdir()
            (root / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(InstanceValidationError):
                init_instance(root, owner="example-org")

    def test_validate_rejects_secret_value_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".agent-hub"
            init_instance(root, owner="example-org")
            credentials_path = root / "credentials.yaml"
            credentials = yaml.safe_load(
                credentials_path.read_text(encoding="utf-8")
            )
            credentials["credential_routes"]["ADMIN"] = {
                "store": "provider",
                "value_access": "forbidden",
                "token": "not-allowed-here",
            }
            credentials_path.write_text(
                yaml.safe_dump(credentials, sort_keys=False),
                encoding="utf-8",
            )
            with self.assertRaises(InstanceValidationError):
                validate_instance(root)

    def test_duplicate_aliases_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".agent-hub"
            init_instance(root, owner="example-org")
            projects_path = root / "projects.yaml"
            projects = yaml.safe_load(projects_path.read_text(encoding="utf-8"))
            projects["routing"] = [
                {
                    "id": "one",
                    "repo": "example-org/one",
                    "aliases": ["shared"],
                },
                {
                    "id": "two",
                    "repo": "example-org/two",
                    "aliases": ["shared"],
                },
            ]
            projects_path.write_text(
                yaml.safe_dump(projects, sort_keys=False),
                encoding="utf-8",
            )
            with self.assertRaises(InstanceValidationError):
                validate_instance(root)

    def test_bootstrap_acceptance(self):
        result = bootstrap_acceptance()
        self.assertEqual(result["configured_repositories"], 5)
        self.assertEqual(result["custom_credentials_required"], 0)
        self.assertTrue(result["doctor_ok"])
        self.assertTrue(result["protocol_conformance_verified"])


if __name__ == "__main__":
    unittest.main()
