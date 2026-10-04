# AGENTS.md

## Purpose

This repository is the portable, user-agnostic Truthrail Core reference implementation.

## Change rules

1. Create a feature branch from current `main`.
2. Keep changes portable: do not add personal repository names, private URLs, real
   credential names, email addresses, account identifiers, or environment-specific
   infrastructure details.
3. Update executable schemas, examples, tests, and protocol documentation together
   when a protocol contract changes.
4. Run the full CI suite.
5. Merge only after CI is green.

## Protocol invariants

- Live target systems outrank cached or conversational state.
- Use the lowest sufficient execution level.
- Privileged operations come from live reviewed control-plane contracts.
- Only operations with `agent_routable: true` are AI-routable.
- Secret values are outside the protocol.
- `executed != verified`.
- In v0.2 the WorkPacket is the single root work order; execution bindings must not create a parallel task/lifecycle owner.
- Agent route proposals do not grant authority; policy owns the authorized direct/branch_pr route.
- A bound receipt is stale if its execution-plan digest or state fingerprint no longer matches authoritative state.
- Keep handoff packets bounded; do not forward complete chat histories.
- Do not introduce a generic privileged shell or universal executor.

## Compatibility

v0.1 schema changes must remain backward compatible unless the package version and
protocol version are intentionally advanced together. During the Truthrail rename, keep
legacy technical identifiers such as `agent-hub-core`, `agent_hub_core`, `.agent-hub/`,
and existing schema IDs working unless a separately versioned migration removes them.
