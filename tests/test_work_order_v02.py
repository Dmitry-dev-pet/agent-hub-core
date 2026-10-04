import unittest

from agent_hub_core.execution_binding import (
    ExecutionBindingError,
    StaleExecutionResultError,
    assert_receipt_fresh,
    bind_execution_plan,
    bind_execution_receipt,
    compute_state_fingerprint,
    render_pr_summary,
)
from agent_hub_core.validation import (
    ProtocolValidationError,
    validate_document,
    validate_run_bundle,
)


RUN_ID = "run-demo-0001"


def work_packet():
    return {
        "version": 2,
        "run_id": RUN_ID,
        "source": {"channel": "chatgpt", "reference": "conversation"},
        "created_at": "2026-10-04T20:30:00Z",
        "project": "demo-video",
        "outcome": {"description": "Render and verify a preview."},
        "acceptance_proof": {
            "kind": "composite",
            "checks": ["workflow succeeds", "artifact exists"],
        },
        "execution_envelope": {
            "repositories": ["example/demo-video"],
            "allowed": ["workflow_dispatch", "artifact_read"],
            "forbidden": ["credential_change"],
        },
        "approval": {"policy": "if_required"},
        "preferred_level": "L3",
        "maximum_level": "L5",
    }


def execution_plan():
    return {
        "version": 2,
        "run_id": RUN_ID,
        "project": "demo-video",
        "selected_level": "L3",
        "reason": "A workflow runtime is sufficient.",
        "capability": "github-actions",
        "acceptance_proof": ["workflow succeeds", "artifact exists"],
        "approval": {
            "required": False,
            "reason": "No additional approval is required.",
            "basis": "work_packet_policy",
        },
    }


def execution_receipt():
    return {
        "version": 2,
        "run_id": RUN_ID,
        "status": "executed",
        "capability": "github-actions",
        "approval": {"status": "not_required"},
        "authoritative_refs": [{"type": "workflow_run", "value": "123"}],
        "observations": ["preview rendered"],
    }


def verification_result():
    return {
        "version": 2,
        "run_id": RUN_ID,
        "status": "verified",
        "checks": [
            {"name": "workflow succeeds", "passed": True},
            {"name": "artifact exists", "passed": True},
        ],
        "authoritative_refs": [{"type": "workflow_run", "value": "123"}],
    }


def state_inputs(head="head-1"):
    return [
        {
            "kind": "repository_head",
            "ref": "example/demo-video@main",
            "value": head,
        }
    ]


class WorkOrderV02Tests(unittest.TestCase):
    def test_work_packet_v02_validates(self):
        validate_document("work_packet", work_packet(), schema_version="0.2")

    def test_v02_requires_run_id(self):
        payload = work_packet()
        del payload["run_id"]
        with self.assertRaises(ProtocolValidationError):
            validate_document("work_packet", payload, schema_version="0.2")

    def test_approved_receipt_requires_reference(self):
        receipt = execution_receipt()
        receipt["approval"] = {"status": "approved"}
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

    def test_legacy_unbound_v02_bundle_remains_valid(self):
        self.assertEqual(
            validate_run_bundle(
                [
                    ("work_packet", work_packet()),
                    ("execution_plan", execution_plan()),
                    ("execution_receipt", execution_receipt()),
                    ("verification_result", verification_result()),
                ]
            ),
            RUN_ID,
        )

    def test_bundle_requires_one_run_id(self):
        receipt = execution_receipt()
        receipt["run_id"] = "run-other"
        with self.assertRaises(ProtocolValidationError):
            validate_run_bundle(
                [
                    ("work_packet", work_packet()),
                    ("execution_plan", execution_plan()),
                    ("execution_receipt", receipt),
                ]
            )

    def test_bound_bundle_validates(self):
        plan = bind_execution_plan(
            work_packet(),
            execution_plan(),
            state_inputs=state_inputs(),
            proposed_route="direct",
            policy_minimum_route="branch_pr",
            execution_venue="github-actions",
        )
        receipt = bind_execution_receipt(
            plan,
            approval={"status": "not_required"},
            authoritative_refs=[{"type": "workflow_run", "value": "123"}],
            observations=["preview rendered"],
            observed_effects=["workflow_dispatch"],
            actor="github-actions",
        )
        self.assertEqual(plan["execution_binding"]["route"]["authorized"], "branch_pr")
        self.assertEqual(
            validate_run_bundle(
                [
                    ("work_packet", work_packet()),
                    ("execution_plan", plan),
                    ("execution_receipt", receipt),
                    ("verification_result", verification_result()),
                ]
            ),
            RUN_ID,
        )

    def test_real_state_change_makes_receipt_stale(self):
        plan = bind_execution_plan(
            work_packet(),
            execution_plan(),
            state_inputs=state_inputs("head-before"),
        )
        receipt = bind_execution_receipt(
            plan,
            approval={"status": "not_required"},
            authoritative_refs=[{"type": "commit", "value": "commit-1"}],
            observations=["change committed"],
        )
        assert_receipt_fresh(
            plan,
            receipt,
            current_state_inputs=state_inputs("head-before"),
        )
        with self.assertRaises(StaleExecutionResultError):
            assert_receipt_fresh(
                plan,
                receipt,
                current_state_inputs=state_inputs("head-after"),
            )

    def test_tampered_state_fingerprint_is_rejected(self):
        plan = bind_execution_plan(
            work_packet(),
            execution_plan(),
            state_inputs=state_inputs(),
        )
        plan["execution_binding"]["state_fingerprint"]["digest"] = (
            "sha256:" + "f" * 64
        )
        with self.assertRaises(ProtocolValidationError):
            validate_document("execution_plan", plan, schema_version="0.2")

    def test_duplicate_state_identity_is_rejected(self):
        with self.assertRaises(ExecutionBindingError):
            compute_state_fingerprint(
                "sha256:" + "1" * 64,
                [
                    {
                        "kind": "repository_head",
                        "ref": "example/demo-video@main",
                        "value": "head-1",
                    },
                    {
                        "kind": "repository_head",
                        "ref": "example/demo-video@main",
                        "value": "head-2",
                    },
                ],
            )

    def test_route_cannot_be_weakened_below_policy_minimum(self):
        plan = bind_execution_plan(
            work_packet(),
            execution_plan(),
            state_inputs=state_inputs(),
            proposed_route="direct",
            policy_minimum_route="branch_pr",
        )
        plan["execution_binding"]["route"]["authorized"] = "direct"
        with self.assertRaises(ProtocolValidationError):
            validate_document("execution_plan", plan, schema_version="0.2")

    def test_packet_plan_acceptance_mismatch_is_rejected(self):
        plan = execution_plan()
        plan["acceptance_proof"] = ["workflow succeeds"]
        with self.assertRaises(ExecutionBindingError):
            bind_execution_plan(
                work_packet(),
                plan,
                state_inputs=state_inputs(),
            )
        with self.assertRaises(ProtocolValidationError):
            validate_run_bundle(
                [
                    ("work_packet", work_packet()),
                    ("execution_plan", plan),
                ]
            )

    def test_packet_plan_project_mismatch_is_rejected(self):
        plan = execution_plan()
        plan["project"] = "other-project"
        with self.assertRaises(ExecutionBindingError):
            bind_execution_plan(
                work_packet(),
                plan,
                state_inputs=state_inputs(),
            )

    def test_bound_plan_requires_bound_receipt_in_bundle(self):
        plan = bind_execution_plan(
            work_packet(),
            execution_plan(),
            state_inputs=state_inputs(),
        )
        with self.assertRaises(ProtocolValidationError):
            validate_run_bundle(
                [
                    ("work_packet", work_packet()),
                    ("execution_plan", plan),
                    ("execution_receipt", execution_receipt()),
                ]
            )

    def test_receipt_capability_must_match_bound_plan(self):
        plan = bind_execution_plan(
            work_packet(),
            execution_plan(),
            state_inputs=state_inputs(),
        )
        receipt = bind_execution_receipt(
            plan,
            approval={"status": "not_required"},
            authoritative_refs=[{"type": "commit", "value": "commit-1"}],
            observations=[],
        )
        receipt["capability"] = "other-capability"
        with self.assertRaises(ProtocolValidationError):
            validate_run_bundle(
                [
                    ("work_packet", work_packet()),
                    ("execution_plan", plan),
                    ("execution_receipt", receipt),
                ]
            )

    def test_required_approval_blocks_unapproved_receipt(self):
        packet = work_packet()
        packet["approval"]["policy"] = "required"
        plan = execution_plan()
        plan["approval"] = {
            "required": True,
            "reason": "User approval is required.",
            "basis": "work_packet_policy",
        }
        plan = bind_execution_plan(
            packet,
            plan,
            state_inputs=state_inputs(),
        )
        with self.assertRaises(ExecutionBindingError):
            bind_execution_receipt(
                plan,
                approval={"status": "not_required"},
                authoritative_refs=[{"type": "commit", "value": "commit-1"}],
                observations=[],
            )

    def test_verified_bundle_must_cover_exact_acceptance_proof(self):
        verification = verification_result()
        verification["checks"] = [
            {"name": "workflow succeeds", "passed": True},
        ]
        with self.assertRaises(ProtocolValidationError):
            validate_run_bundle(
                [
                    ("work_packet", work_packet()),
                    ("verification_result", verification),
                ]
            )

    def test_pr_summary_is_projection_only(self):
        plan = bind_execution_plan(
            work_packet(),
            execution_plan(),
            state_inputs=state_inputs(),
            proposed_route="direct",
            policy_minimum_route="branch_pr",
        )
        receipt = bind_execution_receipt(
            plan,
            approval={"status": "not_required"},
            authoritative_refs=[
                {"type": "pull_request", "value": "https://example.invalid/pr/1"}
            ],
            observations=["PR opened"],
            observed_effects=["repository_write"],
        )
        summary = render_pr_summary(
            work_packet(),
            plan,
            receipt=receipt,
            verification_result=verification_result(),
        )
        self.assertIn("Projection only", summary)
        self.assertIn("https://example.invalid/pr/1", summary)
        self.assertIn(
            plan["execution_binding"]["state_fingerprint"]["digest"],
            summary,
        )


if __name__ == "__main__":
    unittest.main()
