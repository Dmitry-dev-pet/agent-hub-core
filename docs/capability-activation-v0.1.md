# Capability readiness and activation protocol v0.1

Core onboarding and capability activation are separate lifecycles.

A Hub can be fully onboarded and recoverable while optional capabilities remain
degraded, dormant, or blocked. Missing an optional capability must not invalidate a
verified core onboarding receipt.

## Readiness states

```text
ready
  capability is fully usable

degraded
  capability is usable in a reduced mode with explicit limitations

dormant
  capability is known and activatable but not currently enabled

blocked
  requested activation cannot currently proceed or be verified
```

The canonical machine-readable state contract is `capabilities/contract.yaml`.

## CapabilityReadiness

Persist a `capability_readiness` document when readiness is important enough to
survive chat/session boundaries.

Every readiness snapshot declares:

- capability id;
- current state;
- whether it is required for core Hub operation;
- prerequisites and their current status;
- explicit limitations;
- activation route and whether user action is required;
- authoritative evidence.

### ready

A `ready` capability has no missing prerequisite marked `required_for_ready` and no
remaining limitations.

### degraded

A `degraded` capability must have at least one missing prerequisite required for full
readiness and at least one explicit limitation. It may still be usable for outcomes
that fit the reduced mode.

### dormant

A `dormant` capability has an activation route but cannot be used yet. At least one
prerequisite required for readiness is missing.

### blocked

Use `blocked` when the requested activation cannot currently proceed. Do not confuse
a merely optional dormant capability with a failed core onboarding.

## Progressive activation

When a requested outcome needs a capability that is not ready:

1. Read the live readiness snapshot and authoritative provider state.
2. Confirm that the capability is actually required for the requested outcome.
3. Prefer an already-ready lower-level capability when it can satisfy the outcome.
4. Identify missing prerequisites without retrieving secret values.
5. Perform all safe connector/control-plane/workflow steps that do not require user
   interaction.
6. If an external provider requires explicit user interaction, stop at that exact
   boundary and present the single remaining action.
7. After the prerequisite is satisfied, execute the narrow verification path.
8. Re-read authoritative state.
9. Emit a `capability_activation_receipt`.

## CapabilityActivationReceipt

A receipt records state transition, prerequisite checks, actions performed,
limitations remaining, credential-boundary compliance, verification, and authoritative
references.

### verified

Use only when:

- `state_after=ready`;
- all prerequisites required for readiness are satisfied;
- no activation action failed;
- no limitations remain;
- independent verification was performed and passed;
- no credential value was copied into Hub/chat/receipt.

### partial

Use when the requested capability is demonstrably usable but remains `degraded`.
Verification must pass for the degraded mode and the remaining limitations must be
listed explicitly.

### blocked

Use when the activation ends in `blocked` or remains `dormant`. A blocked receipt
must not claim successful verification.

## GitHub App example

A scheduled cross-repository watcher may be:

```text
degraded
  GitHub Actions workflow runs
  public repositories are visible
  private-repository completeness is not provable
  read-only GitHub App installation is missing
```

Core Hub onboarding can still be `verified`.

If the user later asks for complete unattended monitoring, the Hub should explain the
missing read-only App prerequisite and offer activation. After installation, verify
that the watcher uses an installation token and sees the full inventory before
declaring the capability `ready`.

## Credential boundary

Activation may configure secret *routes* and provider-managed secret storage. It must
not read, print, copy, commit, or persist the credential value itself.

A capability that cannot be activated without exposing a secret value to the model is
not safely activatable through this protocol.
