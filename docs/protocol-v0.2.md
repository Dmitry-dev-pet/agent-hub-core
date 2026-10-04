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
