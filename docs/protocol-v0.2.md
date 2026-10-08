# Work continuity protocol v0.2

Truthrail v0.2 adds a durable work identity without changing the execution model.

The chat remains the user interface. A WorkPacket is the root **work order** for one
user-authorized outcome, while GitHub, reviewed control planes, workflows, coding
runtimes, and machine-bound executors remain interchangeable execution venues.

## Stable run identity

Every continuity document in v0.2 carries the same `run_id`:

- WorkPacket
- ExecutionPlan
- ExecutionReceipt
- VerificationResult
- HandoffPacket
- lifecycle transition

A consumer must reject a bundle that mixes run IDs. The portable helper
`validate_run_bundle()` validates one current snapshot rooted in the WorkPacket,
with at most one document of each kind. In Core 0.4.0 it also checks project,
acceptance proof, authority ceilings, approvals, execution bindings and evidence
consistency. Matching run IDs alone do not establish authorization or completion.
Use `validate_document()` for structural inspection of an individual document.

## Source and approval

WorkPacket adds:

- `source.channel` and optional `source.reference`;
- `created_at`;
- `approval.policy`: `none`, `if_required`, or `required`.

ExecutionPlan records whether approval is required and why. ExecutionReceipt records
`not_required` or `approved`; an approved receipt must carry a reference to the
approval evidence and the exact ExecutionPlan digest. The
`waiting_approval -> executing` transition carries the same bound approval reference.
The owning approval gate must authenticate this evidence; a digest is not an approval.

Approval never grants generic authority. The owning capability or reviewed control
plane still defines the exact operation and remains responsible for execution.

## Lifecycle

The v0.2 state path is intentionally small:

```text
resolved -> planned -> [waiting_approval] -> executing -> executed -> verifying -> verified
```

The protocol also supports bounded terminal outcomes: `blocked`, `failed`,
`rejected`, and `cancelled`.

A rejection can occur only from `waiting_approval`; this prevents a free-form
"reject" event from masquerading as an approval decision for an unbound plan.

### Execution is not verification

`executed` means that the selected executor or control plane reported that the planned
operation finished. It does **not** mean that the requested outcome was accepted.

After execution, the run enters `verifying`. Verification reads authoritative evidence
and produces a `VerificationResult`. The lifecycle may enter terminal `verified` only
when the relevant verification checks pass. A green workflow response, successful API
call, or completed tool invocation is therefore evidence of execution, not by itself
proof of the requested outcome.

The word `verified` appears in two related places:

- lifecycle state `verified` — the run is complete and accepted;
- `VerificationResult.status = verified` — the verification document says its checks passed.

These are not two lifecycle states. The verification result is the evidence that permits
the transition from lifecycle `verifying` to lifecycle `verified`.

For v0.2 in Core 0.4.0, verified results must cover every WorkPacket acceptance check
exactly once in its declared order, with non-empty evidence for each check. Those
references must also appear in `authoritative_refs`. The result carries
`execution_receipt_digest`; the terminal transition carries
`verification_result_digest`. Bundle validation rejects absent predecessor documents,
changed receipts, failed verification and detached terminal transitions.

Executable records are state-bound before execution. Freshness remains a separate
provider-read responsibility. See [execution binding](execution-binding-v0.2.md) for
the validation boundary, API, recovery rules and migration requirements.

## Durable run ledger and compact checkpoints

A deployment may keep one durable coordination record per `run_id`, for example a GitHub
issue in the user's Truthrail instance. The ledger is a coordination snapshot, not an
authoritative copy of GitHub, deployment, or runtime state.

An optional compact checkpoint may contain only `current_state`, `next_action`, and
`blocked_by`. A resumed session must refresh authoritative references before trusting
or executing the recorded next action. See [Run ledger v0.2](run-ledger-v0.2.md).

## Optional Watch advisories

Truthrail Watch may surface lifecycle/activity mismatches such as a project marked dormant
while multiple independent recent activity signals are present. Advisories request review;
they do not mutate lifecycle state, grant authority, or infer dormancy from silence. See
[Watch semantics v0.2](watch-v0.2.md).

## Compatibility

v0.1 schemas remain unchanged. Callers opt into the new continuity schemas with
`schema_version="0.2"` or the CLI `--schema-version 0.2`.

v0.2 currently extends only the six continuity document kinds. Control-plane,
admission, onboarding, and capability schemas remain v0.1 until separately revised.

Core 0.4.0 intentionally tightens v0.2 validation. Previously accepted unbound execution
bundles or evidence-free verified records are no longer accepted as completed work.
Historical records must not be upgraded by inventing approval or verification evidence.
