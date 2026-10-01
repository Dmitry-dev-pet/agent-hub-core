# Truthrail Core protocol v0.1

> Compatibility note: v0.1 schema IDs and package identifiers retain the historical `agent-hub-core` namespace.

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

### 6.1 Capability authority diff

Reviewed operations may declare an explicit authority surface using:

- `credential_refs`;
- `execution_level`;
- `runtime_auth`;
- `execution_venue`;
- `github_permissions` with `none | read | write` per scope;
- `network_destinations`;
- `external_side_effects`;
- `cost_ceiling` as an amount plus unit;
- `human_gate` as `none | review | approval | provider_interaction`.

`truthrail capability-diff BEFORE AFTER` validates both contracts and compares only
those explicit fields. It must not derive authority from prose descriptions, trigger
names, shell commands, or model judgment.

Deterministic expansions include:

- `agent_routable: false -> true`;
- a higher execution level;
- a new credential, network destination, or external side effect;
- a GitHub permission moving toward `write`;
- a higher cost ceiling when both sides use the same unit;
- removal of an explicit human gate.

Changes whose security direction cannot be proven from the contract, such as switching
execution venue or changing cost units, are reported as `changed`, not guessed as
safe or dangerous. Policy owners may treat an expansion as advisory, require review,
or fail CI with `--fail-on-expansion`.

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


## 10. Onboarding receipt

Onboarding is a distinct lifecycle that converts existing GitHub state into a
portable Agent Hub instance:

```text
discover -> classify -> build -> validate -> watch -> receipt
```

The `onboarding_receipt` records completeness, unresolved ambiguity, secret-boundary
compliance, fresh-session recovery, and authoritative references.

A receipt may be:

- `verified` only when every discovered repository is recorded, no unresolved items
  remain, required phases completed, and fresh recovery passed;
- `partial` when every discovered repository is still recorded and fresh recovery
  passes, but explicit unresolved items remain;
- `blocked` when trustworthy completeness, build, validation, or recovery cannot be
  established.

WATCH is optional and may be skipped. It is a reconciliation mechanism, not a source
of truth.

See `docs/onboarding-v0.1.md` for the full discovery and recovery contract.


## 11. Capability readiness and activation

Core Hub onboarding does not imply that every optional capability is enabled.

A capability has one readiness state:

- `ready` — fully usable;
- `degraded` — usable with explicit limitations;
- `dormant` — known and activatable but not enabled;
- `blocked` — requested activation cannot currently proceed or verify.

A missing prerequisite on an optional capability must not invalidate a verified core
onboarding receipt.

`capability_readiness` snapshots record prerequisites, limitations, activation route,
and authoritative evidence.

`capability_activation_receipt` records a concrete activation attempt. A receipt is:

- `verified` only when the capability ends `ready`, all required prerequisites are
  satisfied, no activation action failed, no limitations remain, and verification
  passed;
- `partial` only when the capability ends `degraded`, degraded behavior was
  independently verified, and remaining limitations are explicit;
- `blocked` when activation ends `blocked` or remains `dormant`.

Credential values remain outside both documents.

See `capabilities/contract.yaml` and
`docs/capability-activation-v0.1.md`.
