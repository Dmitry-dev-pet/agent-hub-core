# Execution binding and v0.2 acceptance

Core 0.4.0 closes the gap between individually valid documents and an internally
consistent authorized run. The WorkPacket remains the single root work order. No
second lifecycle, task store, privileged executor or permission source is introduced.

## What bundle validation enforces

`validate_run_bundle(documents)` accepts one current snapshot: exactly one WorkPacket,
at most one document of each other kind, and at most one current lifecycle transition.
It rejects mixed run IDs and duplicate kinds, even when duplicate documents are equal.
Callers that keep a lifecycle history validate each transition with its supporting
snapshot; they must not silently select one of multiple competing plans or receipts.

| Relationship | Required checks |
| --- | --- |
| WorkPacket to plan | Same project and ordered acceptance proof; selected level within the WorkPacket ceiling; required approval preserved; exact WorkPacket digest for a bound plan |
| WorkPacket to handoff | Same outcome and acceptance proof; repository/effect scope may only narrow; forbidden effects cannot disappear |
| Plan to execution | Execution starts only with a bound plan; required approval cannot be skipped; the approval reference is bound to that exact plan |
| Plan to receipt | Same capability, exact plan digest, state fingerprint and authorized route; matching declared venue; required approval present; reported effects remain within the WorkPacket envelope |
| Receipt to verification | The verified result carries the exact receipt digest; every required check passes exactly once and carries non-empty evidence listed in authoritative references |
| Verification to completion | The current transition is verifying to verified, names the exact verification digest, and has all supporting predecessor documents |

A WorkPacket alone, or a WorkPacket plus an unbound draft plan, can be validated during
planning. A completed execution cannot omit its binding or its predecessor records.
Resolved work may become blocked or cancelled before a plan exists.

## Binding a plan and a receipt

The implementation lives in `truthrail_core.execution_binding`; the legacy module is
only a compatibility import. The package exports the same helpers directly.

```python
from truthrail_core import (
    assert_plan_current,
    bind_execution_plan,
    bind_execution_receipt,
    bind_verification_result,
    canonical_digest,
    validate_run_bundle,
)

plan = bind_execution_plan(
    work_packet,
    proposed_plan,
    state_inputs=authoritative_inputs,
    proposed_route="direct",
    policy_minimum_route="branch_pr",
)

# The reviewed capability supplies a fresh read immediately before execution.
assert_plan_current(plan, current_state_inputs=fresh_authoritative_inputs)

# After the reviewed capability actually executes and returns its evidence:
receipt = bind_execution_receipt(
    plan,
    approval=approval_from_the_owning_gate,
    authoritative_refs=execution_references,
    observations=execution_observations,
)

# The verifier supplies checks after reading the resulting authoritative state.
verification = bind_verification_result(
    work_packet, plan, receipt, verification_from_the_owning_verifier,
)
transition = {
    "version": 2,
    "run_id": work_packet["run_id"],
    "from": "verifying",
    "to": "verified",
    "verification_result_digest": canonical_digest(verification),
}
validate_run_bundle([
    ("work_packet", work_packet),
    ("execution_plan", plan),
    ("execution_receipt", receipt),
    ("verification_result", verification),
    ("lifecycle_transition", transition),
])
```

The complete [JSON example](../examples/v0.2/verified-run.json) is validated in CI.
Its generic references are fixtures, not a claim that a provider operation took place.

State inputs contain exactly `kind`, `ref` and `value`. Supported kinds are repository
HEAD, control-plane contract, policy, provider state and an explicit other category.
Input order does not change the fingerprint; duplicate kind/ref identities are rejected.
The owning capability decides which authoritative inputs are required. A planner cannot
weaken the supplied policy minimum from branch/PR to direct mutation.

## Freshness and an operation's expected effects

`assert_plan_current()` requires current inputs; it never defaults to cached state.
`assert_receipt_fresh()` checks both plan/receipt binding and unchanged planning
preconditions before a result is reused. Neither function makes a network request.

Changing a repository HEAD changes its fingerprint. An old receipt cannot be attached
to a newly bound plan. However, a permitted mutation may itself change the repository
HEAD. Do not compare its legitimate post-state with its pre-state and report a stale
failure. `assert_receipt_matches_plan()` checks historical receipt identity without
claiming freshness; a separate verifier must inspect the operation's resulting state
and bind that evidence to the receipt.

There can still be a race after the precondition read. The capability must apply the
provider's conditional update, transaction or compare-and-swap mechanism where needed.

## Interruptions and retries

The canonical plan digest is stable for one exact task, route and planning state. A
capability may use it in its durable execution record or idempotency key. A digest alone
does not prevent duplicate external actions and must not silently suppress an explicit
new user request; new work requires a new run identity.

When an action finished but its receipt was not persisted, a fresh session first
reconciles the capability's durable operation record and the provider result. It must
not mark the run executed/verified without the missing evidence, or blindly repeat a
non-idempotent operation. Concurrent ownership, locks and retry guarantees belong to
the capability/control plane, not this document validator.

## Trust boundary

Hashes bind supplied content; they are neither signatures nor proof that the content
was read from a provider. Core checks evidence presence, coverage and links between
documents. The owning capability/verifier must authenticate approval, fetch real
evidence, enforce permissions/effects, and decide whether each check actually passed.
The PR summary renderer validates its input snapshot and is a projection only.

CI covers invalid task/project/proof/ceiling/approval/capability combinations, missing
or changed evidence, detached completion, scope expansion, duplicate documents and
changed HEADs in a real temporary local Git repository. This is protocol/local Git
coverage. It does not establish AI-host reliability or distributed exactly-once behavior.

## Migration from Core 0.3.x

v0.1 schemas, defaults and validation behavior remain unchanged. Core 0.4.0 deliberately
tightens v0.2 acceptance without renaming the existing six document kinds or lifecycle.

Consumers must include the root WorkPacket and phase predecessors in each bundle, bind
plans before execution, persist matching receipt bindings, include a plan digest with
approved receipts, and attach evidence/digests before verification and completion.
The approval transition itself must carry the trusted approval reference and plan digest.

Individual legacy unbound plans/receipts can still be inspected structurally, but cannot
be accepted as executed work by bundle validation. Legacy evidence-free verified records
no longer pass the v0.2 schema. Keep them as historical records; obtain new authoritative
verification instead of manufacturing missing evidence or retroactive approvals.
