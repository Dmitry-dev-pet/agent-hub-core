# Run ledger reference pattern for Truthrail v0.2

Truthrail may keep one durable coordination record per `run_id` so that a new chat can
resume multi-step work without relying on conversation memory.

A GitHub issue is a convenient reference implementation because it is durable, reviewable,
linkable, and available through common AI/GitHub integrations. Other stores may implement
the same semantics.

## One durable record per run

A ledger record should contain the current coordination snapshot for one run:

- `run_id`;
- current lifecycle state;
- source channel/reference;
- project or work scope;
- requested outcome;
- approval state;
- selected execution route or capability;
- acceptance proof;
- authoritative references to live systems.

The ledger is **not** an authoritative replica of GitHub, deployment, workflow, or runtime
state. Freshness-sensitive facts must be re-read from their authoritative source.

## Lifecycle

The ledger uses the Truthrail v0.2 lifecycle:

```text
resolved
  -> planned
  -> waiting_approval (optional)
  -> executing
  -> executed
  -> verifying
  -> verified
```

Bounded outcomes are `blocked`, `failed`, `rejected`, and `cancelled`.

A successful run closes only after lifecycle `verified`. Reaching `executed` means the
operation finished; it does not prove that the requested outcome is correct.

Before accepting a v0.2 checkpoint transition, validate a snapshot containing its root
WorkPacket and the predecessor documents required by its phase. Core 0.4.0 requires a
bound plan for execution, a receipt for executed/verifying phases, and exact passing
verification for terminal verified. A snapshot contains one current transition;
validate each historical transition with the documents that supported it at that time.

If a session stops after an external side effect but before saving its receipt, do not
blindly repeat the operation from `next_action`. The owning capability must reconcile
its durable operation identifier and provider state first. It may recover an existing
receipt or retry through its reviewed idempotent route. Core does not provide a
distributed lock or guarantee exactly-once external execution.

## Compact checkpoint

A ledger may carry one optional checkpoint with exactly three resume hints:

- `current_state`: short human-readable summary, up to 500 characters;
- `next_action`: one intended next action, up to 300 characters;
- `blocked_by`: up to 10 concrete blockers, each up to 200 characters.

The checkpoint is deliberately small. It should not duplicate branches, pull requests,
workflow runs, deployments, or runtime state already referenced elsewhere.

Before using `next_action`, a resumed session must refresh the relevant authoritative
references and revise the checkpoint if live evidence disagrees with it.

## When to create a ledger

Create or reuse a durable run when work is multi-step and likely to outlive the current
response, crosses into an external executor/control plane, may pause for human approval,
or must be resumable from another chat.

Ordinary one-step read-only questions do not need a durable run.

## Approval and authority

The ledger records approval state but never grants authority. Approval remains bound to the
owning capability or reviewed control plane. A checkpoint cannot broaden permissions.

## Secret boundary

Do not store credential values, tokens, session material, private keys, or runtime secret
values in a ledger. Store references, names, scopes, and authoritative links instead.

See also the portable example at [`examples/run-ledger.yaml`](../examples/run-ledger.yaml).
