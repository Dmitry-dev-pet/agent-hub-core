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

## Architectural boundaries

- Assistant profiles own identity, goals, attention policy and skill IDs; they do not own implementation paths, runtime topology or operation contracts.
- Private Truthrail instances own user-specific durable state and routing overlays; they must not grow a second implementation of the portable protocol.
- Truthrail Core owns protocol schemas, semantic validation, portable skills and routing mechanism.
- Capabilities/control planes own concrete operation contracts and verification evidence.
- New code uses the canonical `truthrail_core` namespace. `agent_hub_core` is a compatibility namespace backed by the same implementation.
- Compatibility aliases point to canonical behavior; do not fork logic between old and new names.

See [docs/boundaries-v0.3.md](docs/boundaries-v0.3.md).

## Protocol invariants

- Live target systems outrank cached or conversational state.
- Use the lowest sufficient execution level.
- Privileged operations come from live reviewed control-plane contracts.
- Only operations with `agent_routable: true` are AI-routable.
- Secret values are outside the protocol.
- `executed != verified`.
- Keep handoff packets bounded; do not forward complete chat histories.
- Do not introduce a generic privileged shell or universal executor.

## Compatibility

v0.1 schema changes must remain backward compatible unless the package version and
protocol version are intentionally advanced together. During the Truthrail rename, keep
legacy technical identifiers such as `agent-hub-core`, `agent_hub_core`, `.agent-hub/`,
and existing schema IDs working unless a separately versioned migration removes them.
