import unittest

from agent_hub_core.validation import (
    ProtocolValidationError,
    validate_document,
    validate_run_bundle,
)


RUN_ID = "run-coimbra-0001"


def work_packet():
    return {
        "version": 2,
        "run_id": RUN_ID,
        "source": {"channel": "chatgpt", "reference": "conversation"},
        "created_at": "2026-10-04T20:30:00Z",
        "project": "coimbra-video",
        "outcome": {"description": "Render and verify a preview."},
        "acceptance_proof": {
            "kind": "composite",
            "checks": ["workflow succeeds", "artifact exists"],
        },
        "execution_envelope": {
            "repositories": ["example/coimbra-video"],
            "allowed": ["workflow_dispatch", "artifact_read"],
            "forbidden": ["credential_change"],
        },
        "approval": {"policy": "if_required"},
        "preferred_level": "L3",
        "maximum_level": "L5",
    }


class WorkOrderV02Tests(unittest.TestCase):
    def test_work_packet_v02_validates(self):
        validate_document("work_packet", work_packet(), schema_version="0.2")

    def test_v02_requires_run_id(self):
        payload = work_packet()
        del payload["run_id"]
        with self.assertRaises(ProtocolValidationError):
            validate_document("work_packet", payload, schema_version="0.2")

    def test_approved_receipt_requires_reference(self):
        receipt = {
            "version": 2,
            "run_id": RUN_ID,
            "status": "executed",
            "capability": "mac-access",
            "approval": {"status": "approved"},
            "authoritative_refs": [{"type": "workflow_run", "value": "123"}],
            "observations": [],
        }
        with self.assertRaises(ProtocolValidationError):
            validate_document("execution_receipt", receipt, schema_version="0.2")

    def test_waiting_approval_can_be_rejected(self):
        validate_document(
            "lifecycle_transition",
            {
                "version": 2,
                "run_id": RUN_ID,
                "from": "waiting_approval",
                "to": "rejected",
            },
            schema_version="0.2",
        )

    def test_planned_cannot_skip_to_rejected(self):
        with self.assertRaises(ProtocolValidationError):
            validate_document(
                "lifecycle_transition",
                {
                    "version": 2,
                    "run_id": RUN_ID,
                    "from": "planned",
                    "to": "rejected",
                },
                schema_version="0.2",
            )

    def test_bundle_requires_one_run_id(self):
        plan = {
            "version": 2,
            "run_id": RUN_ID,
            "project": "coimbra-video",
            "selected_level": "L3",
            "reason": "A workflow runtime is sufficient.",
            "capability": "github-actions",
            "acceptance_proof": ["workflow succeeds"],
            "approval": {
                "required": False,
                "reason": "Read-only preview generation.",
                "basis": "work_packet_policy",
            },
        }
        receipt = {
            "version": 2,
            "run_id": RUN_ID,
            "status": "executed",
            "capability": "github-actions",
            "approval": {"status": "not_required"},
            "authoritative_refs": [{"type": "workflow_run", "value": "123"}],
            "observations": ["preview rendered"],
        }
        verification = {
            "version": 2,
            "run_id": RUN_ID,
            "status": "verified",
            "checks": [{"name": "workflow succeeds", "passed": True}],
            "authoritative_refs": [{"type": "workflow_run", "value": "123"}],
        }
        self.assertEqual(
            validate_run_bundle(
                [
                    ("work_packet", work_packet()),
                    ("execution_plan", plan),
                    ("execution_receipt", receipt),
                    ("verification_result", verification),
                ]
            ),
            RUN_ID,
        )

        receipt["run_id"] = "run-other"
        with self.assertRaises(ProtocolValidationError):
            validate_run_bundle(
                [
                    ("work_packet", work_packet()),
                    ("execution_plan", plan),
                    ("execution_receipt", receipt),
                ]
            )


if __name__ == "__main__":
    unittest.main()
