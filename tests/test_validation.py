import json
import unittest
from pathlib import Path

import yaml

from agent_hub_core.validation import (
    ProtocolValidationError,
    check_schemas,
    validate_document,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "v0.1"


class ProtocolValidationTests(unittest.TestCase):
    def load(self, filename):
        return json.loads((EXAMPLES / filename).read_text(encoding="utf-8"))

    def test_bundled_schemas_are_valid(self):
        check_schemas()

    def test_examples_validate(self):
        mapping = {
            "work-packet.json": "work_packet",
            "handoff-packet.json": "handoff_packet",
            "execution-plan.json": "execution_plan",
            "execution-receipt.json": "execution_receipt",
            "verification-result.json": "verification_result",
            "lifecycle-transition.json": "lifecycle_transition",
            "control-plane.json": "control_plane",
            "onboarding-receipt.json": "onboarding_receipt",
            "capability-readiness.json": "capability_readiness",
            "capability-activation-receipt.json": "capability_activation_receipt",
            "capability-policy-decision.json": "capability_policy_decision",
        }
        for filename, kind in mapping.items():
            with self.subTest(filename=filename):
                validate_document(kind, self.load(filename))

    def test_preferred_level_cannot_exceed_maximum(self):
        packet = self.load("work-packet.json")
        packet["preferred_level"] = "L4"
        packet["maximum_level"] = "L3"
        with self.assertRaises(ProtocolValidationError):
            validate_document("work_packet", packet)

    def test_allowed_and_forbidden_must_not_overlap(self):
        packet = self.load("work-packet.json")
        packet["execution_envelope"]["forbidden"].append("workflow_dispatch")
        with self.assertRaises(ProtocolValidationError):
            validate_document("work_packet", packet)

    def test_execution_receipt_cannot_claim_verified(self):
        receipt = self.load("execution-receipt.json")
        receipt["status"] = "verified"
        with self.assertRaises(ProtocolValidationError):
            validate_document("execution_receipt", receipt)

    def test_verified_result_requires_passing_checks(self):
        result = self.load("verification-result.json")
        result["checks"][0]["passed"] = False
        with self.assertRaises(ProtocolValidationError):
            validate_document("verification_result", result)

    def test_lifecycle_cannot_skip_verifying(self):
        with self.assertRaises(ProtocolValidationError):
            validate_document(
                "lifecycle_transition",
                {"version": 1, "from": "executed", "to": "verified"},
            )

    def test_non_routable_control_operation_requires_reason(self):
        contract = self.load("control-plane.json")
        contract["operations"]["credential-export"].pop("reason")
        with self.assertRaises(ProtocolValidationError):
            validate_document("control_plane", contract)

    def test_verified_onboarding_requires_complete_inventory(self):
        receipt = self.load("onboarding-receipt.json")
        receipt["inventory"]["repositories_recorded"] -= 1
        with self.assertRaises(ProtocolValidationError):
            validate_document("onboarding_receipt", receipt)

    def test_verified_onboarding_rejects_unresolved_items(self):
        receipt = self.load("onboarding-receipt.json")
        receipt["unresolved"].append(
            {
                "kind": "project_family",
                "subject": "example-org/app-ui + example-org/app-api",
                "question": "Are these one project family?",
            }
        )
        with self.assertRaises(ProtocolValidationError):
            validate_document("onboarding_receipt", receipt)

    def test_verified_onboarding_requires_fresh_recovery(self):
        receipt = self.load("onboarding-receipt.json")
        receipt["fresh_recovery"]["passed"] = False
        with self.assertRaises(ProtocolValidationError):
            validate_document("onboarding_receipt", receipt)

    def test_partial_onboarding_keeps_explicit_ambiguity(self):
        receipt = self.load("onboarding-receipt.json")
        receipt["status"] = "partial"
        receipt["unresolved"] = [
            {
                "kind": "alias",
                "subject": "example-org/legacy-ui",
                "question": "Which current project alias should resolve this repository?",
            }
        ]
        validate_document("onboarding_receipt", receipt)

    def test_partial_onboarding_requires_unresolved_item(self):
        receipt = self.load("onboarding-receipt.json")
        receipt["status"] = "partial"
        with self.assertRaises(ProtocolValidationError):
            validate_document("onboarding_receipt", receipt)

    def test_ready_capability_rejects_missing_required_prerequisite(self):
        readiness = self.load("capability-readiness.json")
        readiness["state"] = "ready"
        readiness["limitations"] = []
        with self.assertRaises(ProtocolValidationError):
            validate_document("capability_readiness", readiness)

    def test_degraded_capability_requires_limitation(self):
        readiness = self.load("capability-readiness.json")
        readiness["limitations"] = []
        with self.assertRaises(ProtocolValidationError):
            validate_document("capability_readiness", readiness)

    def test_verified_activation_must_end_ready(self):
        receipt = self.load("capability-activation-receipt.json")
        receipt["state_after"] = "degraded"
        receipt["limitations_remaining"] = ["still limited"]
        with self.assertRaises(ProtocolValidationError):
            validate_document("capability_activation_receipt", receipt)

    def test_verified_activation_rejects_failed_action(self):
        receipt = self.load("capability-activation-receipt.json")
        receipt["actions"][0]["result"] = "failed"
        with self.assertRaises(ProtocolValidationError):
            validate_document("capability_activation_receipt", receipt)

    def test_partial_activation_requires_degraded_mode_and_limitation(self):
        receipt = self.load("capability-activation-receipt.json")
        receipt["status"] = "partial"
        receipt["state_after"] = "degraded"
        receipt["limitations_remaining"] = ["private repositories are not covered"]
        receipt["prerequisites_checked"][0]["status"] = "missing"
        validate_document("capability_activation_receipt", receipt)

    def test_blocked_activation_may_preserve_degraded_readiness(self):
        receipt = self.load("capability-activation-receipt.json")
        receipt["status"] = "blocked"
        receipt["state_after"] = "degraded"
        receipt["prerequisites_checked"][0]["status"] = "missing"
        receipt["limitations_remaining"] = ["private repositories remain unavailable"]
        receipt["verification"]["performed"] = False
        receipt["verification"]["passed"] = False
        validate_document("capability_activation_receipt", receipt)

    def test_machine_readable_capability_contract_matches_protocol(self):
        contract = yaml.safe_load(
            (ROOT / "capabilities" / "contract.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["version"], 1)
        self.assertEqual(
            set(contract["states"]),
            {"ready", "degraded", "dormant", "blocked"},
        )
        self.assertTrue(
            contract["principles"]["core_onboarding_must_not_require_optional_capabilities"]
        )
        self.assertTrue(contract["principles"]["never_copy_credential_values"])
        self.assertEqual(
            contract["activation"]["receipt_kind"],
            "capability_activation_receipt",
        )

    def test_machine_readable_onboarding_contract_matches_protocol(self):
        contract = yaml.safe_load(
            (ROOT / "onboarding" / "contract.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["version"], 1)
        self.assertEqual(contract["default_mode"], "brownfield")
        self.assertEqual(
            [phase["id"] for phase in contract["phases"]],
            ["discover", "classify", "build", "validate", "watch", "receipt"],
        )
        self.assertFalse(contract["rules"]["guess_ambiguous_relationships"])
        self.assertFalse(contract["rules"]["copy_credential_values"])
        self.assertFalse(contract["fresh_recovery"]["previous_conversation_allowed"])


if __name__ == "__main__":
    unittest.main()
