# Agent Hub Core

Agent Hub Core is a portable, GitHub-native protocol and reference implementation
for routing AI-assisted work across repositories, APIs, reviewed control planes,
ephemeral runtimes, coding agents, and machine-bound executors.

Version: **0.1.1**

## Core model

```text
GitHub/live systems are authoritative state.
Chat is the interface.
Use the lowest sufficient execution level.
Privileged operations come from live reviewed contracts.
Executed does not mean verified.
```

Agent Hub Core is deliberately not a universal privileged agent runtime. It defines
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

## Live cross-vendor demo

A tiny public demo under [`demo/`](demo/) proves the vendor-neutral interaction
model without a special Agent Hub connector:

```text
ChatGPT or Grok
  -> normal GitHub connection
  -> same demo policy
  -> same public ledger issue
  -> same comment mutation
  -> read-back verification
```

The demo uses no custom secrets, workflow runner, or coding-agent runtime. The
published contract selects the lowest sufficient level: one direct GitHub comment
mutation followed by read-back verification.

## Install

From a checkout:

```bash
python -m pip install -e .
```

For development:

```bash
python -m pip install -e ".[dev]"
```

## CLI

Validate a WorkPacket:

```bash
agent-hub-core validate \
  --kind work_packet \
  examples/v0.1/work-packet.json
```

Check every bundled schema:

```bash
agent-hub-core check-schemas
```

Run the deterministic v0.1 conformance scenario:

```bash
agent-hub-core conformance
```

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

See `docs/protocol-v0.1.md` and `examples/v0.1/`.

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

## Zero-custom-secret bootstrap

A new instance does not need a PAT, API key, SSH key, or other custom secret:

```bash
agent-hub-core init --owner example-org \
  --project example-org/public-repo-one \
  --project example-org/public-repo-two

agent-hub-core validate-instance
agent-hub-core doctor
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
agent-hub-core bootstrap-acceptance
```

This creates a fresh five-repository instance in a temporary directory, verifies that
zero custom credentials are required, runs the offline doctor, and completes protocol
conformance.

## Instance configuration

The core is user-agnostic. An installation supplies its own project inventory,
aliases, capability pointers, credential metadata, and durable context. A sanitized
example lives in `examples/instance/`.

Secret **values** are outside the protocol. Only names, scopes, stores, and safe
consumer routes belong in an Agent Hub instance.

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
