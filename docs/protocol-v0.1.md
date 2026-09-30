# Agent Hub Core protocol v0.1

## 1. Source precedence

For current operational facts:

```text
live target-system evidence
  > reviewed control-plane configuration
  > instance routing/capability metadata
  > lifecycle inventory
  > reconciliation cache
  > conversation memory
```

Durable context can store goals, decisions, rejected options, constraints, and
authoritative pointers. It must not become a second database for current HEAD, PR,
workflow, deployment, or runtime state.

## 2. Work lifecycle

```text
resolved
→ planned
→ executing
→ executed
→ verifying
→ verified
```

`blocked` may be entered from any non-terminal stage.

An ExecutionReceipt has status `executed`. It cannot claim `verified`.
Verification is represented by a separate VerificationResult whose checks evaluate
the declared acceptance proof.

## 3. Execution levels

- **L0** — read/reason from authoritative live state.
- **L1** — direct connector/API operation.
- **L2** — reviewed control-plane operation.
- **L3** — ephemeral workflow/runtime.
- **L4** — coding-agent/runtime.
- **L5** — machine-bound execution.

Select the lowest level that can satisfy the outcome and acceptance proof.

## 4. WorkPacket

Use a WorkPacket for substantial work that benefits from explicit outcome,
acceptance-proof, execution-envelope, and escalation boundaries. Trivial reads and
small direct operations may skip persistence.

The schema also enforces that `preferred_level <= maximum_level` and that an action
cannot appear in both the allowed and forbidden execution envelope.

## 5. HandoffPacket

A HandoffPacket carries only the minimum bounded state required by the next executor:

- project;
- outcome;
- verified facts;
- remaining work;
- acceptance proof;
- execution envelope;
- authoritative references.

Do not forward entire conversations, secret values, or stale live-state copies.

## 6. Reviewed control-plane contract

Privileged capabilities point to a live `control-plane.json` owned by the reviewed
control plane. The contract is authoritative for its operation surface.

Every operation must explicitly declare `agent_routable`. A router must reject an
operation unless the value is exactly `true`. An operation with
`agent_routable: false` must include a reason.

This allows operator-only workflows to coexist with AI-routable operations without
silently expanding agent privilege.

## 7. Credential boundary

Credential routes may contain metadata such as:

- credential name;
- store;
- owner/scope;
- consumer capability;
- status;
- `value_access: forbidden`.

Credential values are outside the core protocol.

## 8. Reconciliation

Scheduled watchers and snapshots are acceleration and reconciliation loops, not the
primary source of truth. Event-driven fast paths can be added without changing this
correctness model.

## 9. Reference conformance

`agent-hub-core conformance` runs a deterministic end-to-end scenario over five
example repositories. It covers fresh resolution, hydration, L0-L5 level selection,
live control-plane routing, operator-only rejection, handoff, execution receipts,
verification, and fresh-session recovery.
