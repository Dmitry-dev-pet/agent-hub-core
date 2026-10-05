# Truthrail Core

**English** | [Русский](README.ru.md)

**One source of truth. Any AI.**

> **Developer preview.** Truthrail is currently an open protocol and reference
> implementation. The repository is usable from a source checkout; a packaged
> end-user installer is not published yet.

**Keep using your AI chat. Make the chat disposable.**

Truthrail lets a fresh AI session recover ongoing work from durable external state,
route the next step through the narrowest available capability, and verify the result
against the live system instead of trusting conversation memory.

```text
ChatGPT / another AI chat
          │
          ▼
      Truthrail
   ┌──────┼────────┐
   ▼      ▼        ▼
 GitHub  reviewed  ephemeral /
 live    control   machine-bound
 state   planes    executors
```

Truthrail itself does **not** require a permanent central agent daemon or an
always-on local computer. Machine-bound capabilities can still be attached when a
task genuinely needs a specific host, GPU, GUI application, or local-only asset.

The core rules are deliberately small:

- chat is the user interface, not the source of truth;
- live target systems outrank cached or conversational state;
- durable work identity can survive a completely new chat session;
- privileged actions stay inside reviewed, scoped capability contracts;
- successful execution is not complete until the requested outcome is verified.

> Formerly **Agent Hub Core**. The v0.1 technical identifiers (`agent-hub-core`,
> `agent_hub_core`, `.agent-hub/`, and existing schema IDs) remain supported
> during the rename.

Version: **0.1.1**

## Core model

```text
GitHub/live systems are authoritative state.
Chat is the interface.
Use the lowest sufficient execution level.
Privileged operations come from live reviewed contracts.
Executed does not mean verified.
```

Truthrail Core is deliberately not a universal privileged agent runtime. It defines
how to resolve a project, hydrate current evidence, plan an execution route, hand work
between execution venues, record execution, and verify the requested outcome.

## Execution levels

| Level | Purpose |
| --- | --- |
| L0 | Read/reason from authoritative live state |
| L1 | Direct connector/API mutation |
| L2 | Reviewed control-plane operation |
| L3 | Ephemeral workflow/runtime |
| L4 | Coding-agent/runtime |
| L5 | Machine-bound execution such as GPU/GUI/local-only assets |

Escalation should be monotonic for one attempt: move upward only when the lower level
cannot satisfy the outcome or its acceptance proof.

## Public demos

Two small demos isolate the two most important properties.

### Cross-vendor execution

The public [`demo/`](demo/) proves the vendor-neutral interaction model without a
special Truthrail connector:

```text
ChatGPT or Grok
  -> normal GitHub connection
  -> same demo policy
  -> same public issue shape
  -> same issue-create mutation
  -> read-back verification
```

The demo uses no custom secrets, workflow runner, or coding-agent runtime. The
published contract selects the lowest sufficient level: one direct GitHub issue
creation followed by read-back verification.

### Fresh-session continuity

[`docs/fresh-session-demo.md`](docs/fresh-session-demo.md) gives a reproducible
two-chat scenario: the first chat leaves a durable work item, the second chat starts
without the old transcript, refreshes authoritative GitHub state, performs the pending
action, verifies it by reading it back, and only then completes the run.

The bundled deterministic conformance harness also proves fresh-session recovery
without conversation memory.

## Developer setup

There is no packaged end-user installer yet. From a source checkout:

```bash
python -m pip install -e .
```

For development:

```bash
python -m pip install -e ".[dev]"
```

## CLI

`truthrail` is the preferred CLI name. The legacy `agent-hub-core` command remains an alias for v0.1 compatibility.

Validate a WorkPacket:

```bash
truthrail validate \
  --kind work_packet \
  examples/v0.1/work-packet.json
```

Check every bundled schema:

```bash
truthrail check-schemas
```

Run the deterministic v0.1 conformance scenario:

```bash
truthrail conformance
```

Compare the explicit authority surface of two reviewed control-plane contracts:

```bash
truthrail capability-diff before-control-plane.json after-control-plane.json
```

Use `--format json` for machine-readable output. CI may opt into
`--fail-on-expansion`; the default command is advisory and never executes either
contract.

Evaluate the portable default policy:

```bash
truthrail capability-policy before-control-plane.json after-control-plane.json
```

The default v1 policy emits `PASS`, `REVIEW`, or `BLOCK`. It blocks only narrow
boundary removals (new AI-routable operations, enabling agent routing on an existing
operator-only operation, or removing an explicit human gate). Other authority
expansions require review. CI can enforce only `BLOCK` with
`--fail-on block`, or require a clean `PASS` with `--fail-on review`.

Evaluate runtime admission before an operation reaches credential-bearing or
consequential execution:

```bash
truthrail admit-operation control-plane.json \
  --operation deploy \
  --actor example-owner \
  --owner example-owner \
  --route agent \
  --require-admit
```

Runtime admission emits `ADMIT`, `REQUIRE_HUMAN`, or `DENY` from the live
reviewed operation contract. It verifies requester policy and agent routability, fails
closed when admission metadata is absent, and records deterministic contract/operation
SHA-256 digests. Provider interaction and post-execution review remain separate gates.

## Python API

```python
from agent_hub_core import validate_document

plan = {
    "version": 1,
    "project": "demo-app",
    "selected_level": "L1",
    "reason": "A direct API mutation is sufficient.",
    "capability": "github",
    "acceptance_proof": ["updated state is visible from the authoritative API"],
}

validate_document("execution_plan", plan)
```

## Protocol documents

v0.1 includes executable JSON Schemas for:

- WorkPacket
- HandoffPacket
- ExecutionPlan
- ExecutionReceipt
- VerificationResult
- lifecycle transitions
- reviewed control-plane contracts
- onboarding receipts
- capability readiness snapshots
- capability activation receipts
- capability policy decisions

See `docs/protocol-v0.1.md` and `examples/v0.1/`.

### Work continuity v0.2

v0.2 is an additive continuity layer for chat-first operators. A WorkPacket becomes
the durable work-order root for one user-authorized outcome. The six continuity
documents carry one stable `run_id`, WorkPacket records the source channel and
approval policy, and the lifecycle can pause at `waiting_approval` before execution.

v0.1 remains unchanged and is still the compatibility default. Opt into v0.2 with:

```bash
truthrail validate --schema-version 0.2 --kind work_packet work-packet.json
```

Python clients can use `validate_run_bundle()` to reject mixed-run packets before
execution or handoff. See `docs/protocol-v0.2.md`.

## Reviewed control planes

A privileged capability points to the owning repository's live operation contract
instead of copying its command list into a central registry.

```yaml
id: repo-admin
kind: reviewed_control_plane
operations_contract:
  provider: github
  repo: example-org/repo-admin
  path: control-plane.json
execution_levels: [L2]
```

An operation is available to an AI router only when the owning contract explicitly
sets `agent_routable: true`. Operator-only or legacy operations can remain present
without becoming AI-accessible.

A control-plane operation may also explicitly describe its authority surface:
`credential_refs`, `execution_level`, `runtime_auth`, `execution_venue`,
`github_permissions`, `network_destinations`, `external_side_effects`,
`cost_ceiling`, and `human_gate`. Truthrail's capability diff compares only these
declared fields; it does not infer privilege from descriptions or ask an LLM to judge
a diff. Expansions such as `read -> write`, a new credential reference, a new
external side effect, a higher same-unit cost ceiling, or removal of a human gate are
reported deterministically.

Runtime admission is declared separately with an `admission` object containing a
`mode` (`automatic`, `manual_approval`, `provider_interaction`, or
`operator_only`) and requester policy. This is intentionally separate from
`human_gate`, which may describe a later review boundary.

The machine-readable default policy is `capabilities/policy-v1.yaml`. Policy
evaluation is deterministic and uses only the capability diff; no LLM judgment or
secret values participate.

## Brownfield onboarding

The default product path is not an empty account. It is an existing GitHub account
with repositories, workflows, old experiments, project families, and ambiguous
relationships.

The portable onboarding protocol is:

```text
DISCOVER -> CLASSIFY -> BUILD -> VALIDATE -> WATCH -> RECEIPT
```

A client should discover the complete visible repository set, preserve every
repository, normalize only high-confidence project relationships, record ambiguities
instead of guessing, build/validate the Truthrail instance, and then prove fresh-session recovery.

The machine-readable `onboarding_receipt` has three outcomes:

- `verified` — complete inventory, no unresolved items, fresh recovery passed;
- `partial` — complete and recoverable, but explicit semantic ambiguities remain;
- `blocked` — trustworthy completeness/build/validation/recovery could not be
  established.

The single machine-readable entry point is `onboarding/contract.yaml`. See also `docs/onboarding-v0.1.md` and `skills/bootstrap-instance/SKILL.md`.

## Progressive capability activation

Core onboarding and optional capability activation are separate lifecycles.

A Truthrail instance can be fully verified while optional capabilities are:

```text
ready     — fully usable
degraded  — usable with explicit limitations
dormant   — known and activatable, but not enabled
blocked   — requested activation cannot currently proceed or verify
```

The machine-readable entry point is `capabilities/contract.yaml`.

When a requested outcome needs a non-ready capability, the client should identify the
narrow prerequisites, complete every safe non-interactive step, stop exactly at any
provider-required human action, then verify the real capability before emitting a
`capability_activation_receipt`.

Missing optional capabilities do not invalidate a verified Hub onboarding.

See `docs/capability-activation-v0.1.md` and
`skills/activate-capability/SKILL.md`.

## Zero-custom-secret bootstrap

A new instance does not need a PAT, API key, SSH key, or other custom secret:

```bash
truthrail init --owner example-org \
  --project example-org/public-repo-one \
  --project example-org/public-repo-two

truthrail validate-instance
truthrail doctor
```

The generated `.agent-hub/` contains:

```text
.agent-hub/
├── agent-hub.yaml
├── projects.yaml
├── capabilities.yaml
├── credentials.yaml
└── context/
```

The initial `credentials.yaml` has an empty `credential_routes` mapping. The
default capabilities are public GitHub reads (L0), optional ambient connected GitHub
access (L0/L1), and GitHub Actions with provider-managed `GITHUB_TOKEN` (L3).
No custom secret is created or requested.

`doctor` uses GitHub's public API without an Authorization header to check public
repositories. Use `doctor --offline` for a configuration-only check.

Privileged L2 capabilities are opt-in. Add one only when its reviewed control plane
exists; any credential metadata then belongs to that capability route, while the
secret value stays in the provider's secret store.

CI also runs:

```bash
truthrail bootstrap-acceptance
```

This creates a fresh five-repository instance in a temporary directory, verifies that
zero custom credentials are required, runs the offline doctor, and completes protocol
conformance.

## Instance configuration

The core is user-agnostic. An installation supplies its own project inventory,
aliases, capability pointers, credential metadata, and durable context. A sanitized
example lives in `examples/instance/`.

Secret **values** are outside the protocol. Only names, scopes, stores, and safe
consumer routes belong in a Truthrail instance.

## Conformance

The reference scenario proves:

1. fresh natural-language project resolution;
2. hydration from authoritative live-state fixtures;
3. L0 read routing;
4. L1 direct mutation routing;
5. L2 reviewed control-plane routing;
6. rejection of an operator-only operation;
7. L3 runtime escalation only when required;
8. L4/L5 level selection;
9. WorkPacket and HandoffPacket validation;
10. `executed != verified`;
11. acceptance-proof verification;
12. fresh-session recovery without conversation memory.

The reference adapter uses deterministic in-memory fixtures. It is a conformance
harness, not a production privileged executor.

## Portable skills

Generic agent-facing instructions are under `skills/`. They preserve the same
source-precedence, live-contract, lowest-sufficient-level, credential-boundary, and
verification rules without depending on one AI vendor.

## Non-goals

- a proprietary task database;
- a permanent central agent daemon;
- a secret manager;
- a generic remote shell;
- mandatory coding-agent execution;
- replacing GitHub Issues, pull requests, Actions, or provider APIs.

## License

MIT.
