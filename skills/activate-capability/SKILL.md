---
name: activate-capability
description: Inspect and progressively activate an Truthrail capability using readiness states, narrow prerequisites, provider-safe credential routes, and verified activation receipts.
---

# Activate an Truthrail capability

Use this skill when a requested outcome requires a capability that is not currently
`ready`, or when the user explicitly asks to enable/complete/configure a capability.

Read `capabilities/contract.yaml` from the current Truthrail Core before acting.

## 1. Establish readiness

Use live provider evidence plus durable Hub metadata to classify the capability as:

- `ready`;
- `degraded`;
- `dormant`;
- `blocked`.

Do not downgrade core Hub onboarding merely because an optional capability is not
ready.

## 2. Confirm the capability is necessary

Apply the lowest-sufficient-capability rule.

If an already-ready capability can satisfy the requested outcome, use it instead of
activating a broader or more privileged capability.

## 3. Resolve prerequisites

For each prerequisite record:

- id and kind;
- current status;
- whether it is required for full readiness;
- whether explicit user action is required.

Prefer provider-managed credentials and reviewed control planes. Never ask the user to
paste a secret value when a safe provider route exists.

## 4. Perform safe activation work

Complete every non-interactive step available through connected provider surfaces.

If the provider requires a browser confirmation, app installation approval, payment,
hardware presence, or other explicit human action, stop exactly there. Explain the one
remaining action and do not claim activation succeeded.

## 5. Verify from authoritative state

After activation, re-read the provider state and test the actual capability.

For a watcher, verification should test the watcher itself, not merely the existence
of a secret/variable name.

## 6. Emit a receipt

Create and validate a `capability_activation_receipt`.

- `verified` only when state becomes `ready` and verification passes;
- `partial` only when state is `degraded`, degraded behavior is verified, and
  limitations remain explicit;
- `blocked` when activation cannot proceed or verify.

Never put secret values in the readiness snapshot or receipt.
