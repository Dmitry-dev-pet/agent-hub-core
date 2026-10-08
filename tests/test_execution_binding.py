"""Protocol and local Git recovery checks; these do not run an AI host."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from truthrail_core import (
    ExecutionBindingError,
    ProtocolValidationError,
    StaleExecutionResultError,
    assert_plan_current,
    assert_receipt_fresh,
    assert_receipt_matches_plan,
    authorize_repository_route,
    bind_execution_plan,
    bind_execution_receipt,
    bind_verification_result,
    canonical_digest,
    compute_state_fingerprint,
    render_pr_summary,
    validate_document,
    validate_run_bundle,
)


ROOT = Path(__file__).resolve().parents[1]


def packet():
    return {
        "version": 2,
        "run_id": "run-example-001",
        "source": {"channel": "chat"},
        "created_at": "2026-10-08T00:00:00Z",
        "project": "example-project",
        "outcome": {"description": "Publish and verify one artifact."},
        "acceptance_proof": {
            "kind": "composite",
            "checks": ["build passes", "artifact exists"],
        },
        "execution_envelope": {
            "repositories": ["example/project"],
            "allowed": ["build", "artifact_read"],
            "forbidden": ["credential_change"],
        },
        "approval": {"policy": "if_required"},
        "preferred_level": "L3",
        "maximum_level": "L3",
    }


def proposal():
    return {
        "version": 2,
        "run_id": "run-example-001",
        "project": "example-project",
        "selected_level": "L3",
        "reason": "The reviewed build capability is sufficient.",
        "capability": "build-runtime",
        "acceptance_proof": ["build passes", "artifact exists"],
        "approval": {"required": False, "reason": "Within the authorized scope."},
    }


def state(head="head-before"):
    return [{"kind": "repository_head", "ref": "example/project", "value": head}]


def completed_bundle():
    work = packet()
    plan = bind_execution_plan(work, proposal(), state_inputs=state(), execution_venue="build-worker")
    receipt = bind_execution_receipt(
        plan,
        approval={"status": "not_required"},
        authoritative_refs=[{"type": "workflow_run", "value": "run-42"}],
        observations=["The build completed."],
        observed_effects=["build"],
    )
    refs = [
        {"type": "workflow_run", "value": "run-42"},
        {"type": "artifact", "value": "artifact-42"},
    ]
    verification = bind_verification_result(work, plan, receipt, {
        "version": 2,
        "run_id": work["run_id"],
        "status": "verified",
        "checks": [
            {"name": "build passes", "passed": True, "evidence": [refs[0]]},
            {"name": "artifact exists", "passed": True, "evidence": [refs[1]]},
        ],
        "authoritative_refs": refs,
    })
    transition = {
        "version": 2,
        "run_id": work["run_id"],
        "from": "verifying",
        "to": "verified",
        "verification_result_digest": canonical_digest(verification),
    }
    return dict(work_packet=work, execution_plan=plan, execution_receipt=receipt,
                verification_result=verification, lifecycle_transition=transition)


class BundleValidationTests(unittest.TestCase):
    def test_complete_bundle_and_published_example_validate(self):
        data = completed_bundle()
        self.assertEqual(validate_run_bundle(list(data.items())), packet()["run_id"])
        example = json.loads((ROOT / "examples/v0.2/verified-run.json").read_text())
        self.assertEqual(validate_run_bundle(list(example.items())), example["work_packet"]["run_id"])

    def test_same_run_id_does_not_allow_changed_task(self):
        data = completed_bundle()
        data["work_packet"]["outcome"]["description"] = "A different requested outcome."
        with self.assertRaisesRegex(ProtocolValidationError, "different WorkPacket"):
            validate_run_bundle(list(data.items()))

    def test_plan_cannot_change_project_proof_level_or_approval(self):
        cases = {
            "project": "another-project",
            "acceptance_proof": ["build passes"],
            "selected_level": "L5",
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                work, plan = packet(), proposal()
                plan[field] = value
                with self.assertRaises(ProtocolValidationError):
                    validate_run_bundle([("work_packet", work), ("execution_plan", plan)])
                with self.assertRaises(ExecutionBindingError):
                    bind_execution_plan(work, plan, state_inputs=state())
        work = packet()
        work["approval"]["policy"] = "required"
        with self.assertRaisesRegex(ProtocolValidationError, "requires approval"):
            validate_run_bundle([("work_packet", work), ("execution_plan", proposal())])

    def test_bundle_requires_root_predecessors_and_unique_documents(self):
        data = completed_bundle()
        for missing in ("work_packet", "execution_plan", "execution_receipt", "verification_result"):
            with self.subTest(missing=missing):
                partial = [(kind, doc) for kind, doc in data.items() if kind != missing]
                with self.assertRaises(ProtocolValidationError):
                    validate_run_bundle(partial)
        with self.assertRaisesRegex(ProtocolValidationError, "duplicate document kind"):
            validate_run_bundle(list(data.items()) + [("execution_receipt", data["execution_receipt"])])

    def test_unbound_execution_cannot_be_accepted(self):
        data = completed_bundle()
        del data["execution_plan"]["execution_binding"]
        del data["execution_receipt"]["execution_binding"]
        with self.assertRaisesRegex(ProtocolValidationError, "bound ExecutionPlan"):
            validate_run_bundle(list(data.items()))

    def test_receipt_cannot_change_capability_route_venue_or_plan(self):
        edits = (
            ("capability", "other-runtime"),
            ("execution_venue", "other-worker"),
            ("observed_effects", ["credential_change"]),
        )
        for field, value in edits:
            with self.subTest(field=field):
                data = completed_bundle()
                data["execution_receipt"][field] = value
                with self.assertRaises(ProtocolValidationError):
                    validate_run_bundle(list(data.items()))
        for field, value in (("route", "branch_pr"), ("execution_plan_digest", "sha256:" + "0" * 64),
                             ("state_fingerprint", "sha256:" + "0" * 64)):
            with self.subTest(binding_field=field):
                data = completed_bundle()
                data["execution_receipt"]["execution_binding"][field] = value
                with self.assertRaises(ProtocolValidationError):
                    validate_run_bundle(list(data.items()))

    def test_verified_requires_evidence_for_every_exact_check(self):
        variants = ("empty_refs", "missing_evidence", "empty_evidence", "unlisted_evidence",
                    "missing_check", "duplicate_check", "wrong_check", "failed_check")
        for variant in variants:
            with self.subTest(variant=variant):
                data = completed_bundle()
                result = data["verification_result"]
                if variant == "empty_refs": result["authoritative_refs"] = []
                elif variant == "missing_evidence": del result["checks"][0]["evidence"]
                elif variant == "empty_evidence": result["checks"][0]["evidence"] = []
                elif variant == "unlisted_evidence": result["checks"][0]["evidence"][0] = {"type": "issue", "value": "unrelated"}
                elif variant == "missing_check": result["checks"].pop()
                elif variant == "duplicate_check": result["checks"].append(deepcopy(result["checks"][0]))
                elif variant == "wrong_check": result["checks"][0]["name"] = "An easier check."
                elif variant == "failed_check": result["checks"][0]["passed"] = False
                with self.assertRaises(ProtocolValidationError):
                    validate_run_bundle(list(data.items()))

    def test_verified_is_bound_to_one_receipt_and_transition(self):
        for variant in ("changed_receipt", "changed_verification", "missing_digest"):
            with self.subTest(variant=variant):
                data = completed_bundle()
                if variant == "changed_receipt": data["execution_receipt"]["observations"].append("Changed after verification.")
                elif variant == "changed_verification": data["lifecycle_transition"]["verification_result_digest"] = "sha256:" + "0" * 64
                else: del data["verification_result"]["execution_receipt_digest"]
                with self.assertRaises(ProtocolValidationError):
                    validate_run_bundle(list(data.items()))
        with self.assertRaises(ProtocolValidationError):
            validate_document("lifecycle_transition", {
                "version": 2, "run_id": "run-example-001", "from": "verifying", "to": "verified"
            }, schema_version="0.2")

    def test_interrupted_execution_cannot_claim_completion_without_receipt(self):
        data = completed_bundle()
        interrupted = [("work_packet", data["work_packet"]), ("execution_plan", data["execution_plan"])]
        for source, target in (("executing", "executed"), ("executed", "verifying")):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ProtocolValidationError, "execution evidence is missing"):
                    validate_run_bundle(interrupted + [("lifecycle_transition", {
                        "version": 2, "run_id": packet()["run_id"], "from": source, "to": target
                    })])

    def test_handoff_cannot_change_work_or_broaden_scope(self):
        work = packet()
        handoff = {
            "version": 2, "run_id": work["run_id"], "project": work["project"],
            "outcome": work["outcome"]["description"], "verified_facts": [],
            "remaining_work": ["Build the artifact."], "acceptance_proof": work["acceptance_proof"]["checks"],
            "execution_envelope": deepcopy(work["execution_envelope"]),
            "authoritative_refs": [{"type": "repository", "value": "example/project"}],
        }
        validate_run_bundle([("work_packet", work), ("handoff_packet", handoff)])
        for field, value in (("repositories", ["example/unrelated"]), ("allowed", ["credential_change"]), ("forbidden", [])):
            with self.subTest(field=field):
                changed = deepcopy(handoff)
                changed["execution_envelope"][field] = value
                with self.assertRaises(ProtocolValidationError):
                    validate_run_bundle([("work_packet", work), ("handoff_packet", changed)])

    def test_required_approval_is_bound_before_execution(self):
        work, plan = packet(), proposal()
        work["approval"]["policy"] = "required"
        plan["approval"]["required"] = True
        plan = bind_execution_plan(work, plan, state_inputs=state())
        transition = {"version": 2, "run_id": work["run_id"], "from": "planned", "to": "executing"}
        with self.assertRaisesRegex(ProtocolValidationError, "approval cannot be skipped"):
            validate_run_bundle([("work_packet", work), ("execution_plan", plan), ("lifecycle_transition", transition)])
        transition["from"] = "waiting_approval"
        transition["approval"] = {"reference": "approval-record-1", "execution_plan_digest": canonical_digest(plan)}
        validate_run_bundle([("work_packet", work), ("execution_plan", plan), ("lifecycle_transition", transition)])
        with self.assertRaises(ExecutionBindingError):
            bind_execution_receipt(plan, approval={"status": "not_required"}, authoritative_refs=[{"type":"issue", "value":"result"}], observations=[])
        receipt = bind_execution_receipt(plan, approval={"status":"approved", "reference":"approval-record-1", "execution_plan_digest":canonical_digest(plan)}, authoritative_refs=[{"type":"issue", "value":"result"}], observations=[])
        validate_run_bundle([("work_packet", work), ("execution_plan", plan), ("execution_receipt", receipt)])
        receipt["approval"]["execution_plan_digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ProtocolValidationError, "approval belongs to another"):
            validate_run_bundle([("work_packet", work), ("execution_plan", plan), ("execution_receipt", receipt)])

    def test_receipt_helper_cannot_rebind_old_or_unbound_approval(self):
        work, plan = packet(), proposal()
        work["approval"]["policy"] = "required"
        plan["approval"]["required"] = True
        before = bind_execution_plan(work, plan, state_inputs=state("before"))
        after = bind_execution_plan(work, plan, state_inputs=state("after"))
        trusted_approval = {
            "status": "approved",
            "reference": "approval-for-before",
            "execution_plan_digest": canonical_digest(before),
        }
        missing_binding = dict(trusted_approval)
        del missing_binding["execution_plan_digest"]
        for approval in (trusted_approval, missing_binding):
            with self.subTest(bound="execution_plan_digest" in approval):
                with self.assertRaisesRegex(ExecutionBindingError, "approval gate"):
                    bind_execution_receipt(
                        after, approval=approval,
                        authoritative_refs=[{"type": "workflow_run", "value": "run-after"}],
                        observations=[],
                    )
        self.assertEqual(trusted_approval["execution_plan_digest"], canonical_digest(before))

    def test_verification_helper_cannot_rebind_an_existing_result(self):
        data = completed_bundle()
        original_result = deepcopy(data["verification_result"])
        other_receipt = deepcopy(data["execution_receipt"])
        other_receipt["observations"] = ["A different completed execution."]
        other_receipt["authoritative_refs"] = [{"type": "workflow_run", "value": "run-other"}]
        with self.assertRaisesRegex(ExecutionBindingError, "already bound"):
            bind_verification_result(
                data["work_packet"], data["execution_plan"], other_receipt,
                data["verification_result"],
            )
        self.assertEqual(data["verification_result"], original_result)
        self.assertEqual(
            bind_verification_result(
                data["work_packet"], data["execution_plan"], data["execution_receipt"],
                original_result,
            ), original_result,
        )

    def test_projection_cannot_print_mismatched_verified_work(self):
        data = completed_bundle()
        summary = render_pr_summary(data["work_packet"], data["execution_plan"], receipt=data["execution_receipt"], verification_result=data["verification_result"])
        self.assertIn("Projection only", summary)
        self.assertIn("PASS: artifact exists", summary)
        data["work_packet"]["project"] = "other"
        with self.assertRaises(ExecutionBindingError):
            render_pr_summary(data["work_packet"], data["execution_plan"], receipt=data["execution_receipt"])


class FingerprintTests(unittest.TestCase):
    def test_fingerprint_is_order_independent_and_rejects_duplicate_inputs(self):
        inputs = state() + [{"kind": "policy", "ref": "policy-v1", "value": "reviewed"}]
        digest = canonical_digest(packet())
        self.assertEqual(compute_state_fingerprint(digest, inputs), compute_state_fingerprint(digest, inputs[::-1]))
        for invalid in ([], inputs + [inputs[0]], [{"kind": "unknown", "ref": "x", "value": "y"}]):
            with self.assertRaises(ExecutionBindingError):
                compute_state_fingerprint(digest, invalid)

    def test_policy_can_strengthen_but_cannot_be_tampered_weaker(self):
        self.assertEqual(authorize_repository_route("direct", policy_minimum="branch_pr")["authorized"], "branch_pr")
        plan = bind_execution_plan(packet(), proposal(), state_inputs=state(), policy_minimum_route="branch_pr")
        plan["execution_binding"]["route"]["authorized"] = "direct"
        with self.assertRaises(ProtocolValidationError):
            validate_document("execution_plan", plan, schema_version="0.2")

    def test_freshness_requires_explicit_current_inputs(self):
        data = completed_bundle()
        assert_receipt_matches_plan(data["execution_plan"], data["execution_receipt"])
        with self.assertRaises(TypeError):
            assert_receipt_fresh(data["execution_plan"], data["execution_receipt"])
        with self.assertRaises(StaleExecutionResultError):
            assert_receipt_fresh(data["execution_plan"], data["execution_receipt"], current_state_inputs=state("head-after"))

    def test_actual_local_git_change_rejects_stale_reuse_but_preserves_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def git(*args):
                return subprocess.run(["git", *args], cwd=root, check=True, text=True, capture_output=True).stdout.strip()
            git("init", "-q")
            git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Initial", "--allow-empty")
            before = git("rev-parse", "HEAD")
            work = packet()
            plan = bind_execution_plan(work, proposal(), state_inputs=state(before))
            assert_plan_current(plan, current_state_inputs=state(git("rev-parse", "HEAD")))
            receipt = bind_execution_receipt(plan, approval={"status":"not_required"}, authoritative_refs=[{"type":"commit", "value":before}], observations=[])
            git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Changed", "--allow-empty")
            after = git("rev-parse", "HEAD")
            self.assertNotEqual(before, after)
            with self.assertRaises(StaleExecutionResultError):
                assert_receipt_fresh(plan, receipt, current_state_inputs=state(after))
            # A historical receipt remains linked to its original plan. This does
            # not verify the new HEAD or repeat the external action.
            assert_receipt_matches_plan(plan, receipt)
            fresh_plan = bind_execution_plan(work, proposal(), state_inputs=state(after))
            with self.assertRaises(StaleExecutionResultError):
                assert_receipt_matches_plan(fresh_plan, receipt)


if __name__ == "__main__":
    unittest.main()
