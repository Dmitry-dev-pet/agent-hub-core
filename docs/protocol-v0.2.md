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
`validate_run_bundle()` validates each document with the v0.2 schema and proves
that all documents belong to one run.

## Source and approval

WorkPacket adds:

- `source.channel` and optional `source.reference`;
- `created_at`;
- `approval.policy`: `none`, `if_required`, or `required`.

ExecutionPlan records whether approval is required and why. ExecutionReceipt records
`not_required` or `approved`; an approved receipt must carry a reference to the
approval evidence.

Approval never grants generic authority. The owning capability or reviewed control
plane still defines the exact operation and remains responsible for execution.

## State-bound execution

For mutation or other freshness-sensitive work, an ExecutionPlan may carry an
`execution_binding`. This is not a second work-order document: the WorkPacket remains
the root work order for the run.

The binding records:

- the canonical SHA-256 digest of the WorkPacket;
- a state fingerprint over the WorkPacket digest plus authoritative live inputs such
  as repository HEAD, reviewed control-plane contract, provider state, or policy;
- repository route proposal, policy minimum, and authorized route
  (`direct` or `branch_pr`);
- an optional execution venue.

The agent or planner may propose a repository route, but policy owns authorization.
Policy may strengthen `direct` to `branch_pr`; it may not silently weaken a route.

Approval is deliberately not encoded as a repository route. v0.2 already owns that
boundary through `approval.required` and `waiting_approval`.

A bound ExecutionReceipt echoes the state fingerprint, authorized route, and canonical
digest of the bound ExecutionPlan. `validate_run_bundle()` rejects mismatches. Clients
that re-read live state can also call `assert_receipt_fresh()` with current state
inputs; a changed HEAD or other authoritative input makes the old result stale.

Unbound v0.2 bundles remain valid for compatibility.

### Review projection

`render_pr_summary()` produces an ACR-like Markdown review summary over the WorkPacket,
bound plan, receipt, and verification result. The summary is a projection only. It is
not an evidence store or attestation; authoritative provider/verifier references remain
the source of truth.

When a stronger verifier such as APatch owns a frozen contract or signed attestation,
Truthrail should carry its authoritative reference rather than duplicating or weakening
that proof.

## Lifecycle

The v0.2 state path is intentionally small:

```text
resolved -> planned -> [waiting_approval] -> executing -> executed -> verifying -> verified
```

The protocol also supports bounded terminal outcomes: `blocked`, `failed`,
`rejected`, and `cancelled`.

A rejection can occur only from `waiting_approval`; this prevents a free-form
"reject" event from masquerading as an approval decision for an unbound plan.

## Compatibility

v0.1 schemas remain unchanged. Callers opt into the new continuity schemas with
`schema_version="0.2"` or the CLI `--schema-version 0.2`.

v0.2 currently extends only the six continuity document kinds. Control-plane,
admission, onboarding, and capability schemas remain v0.1 until separately revised.
