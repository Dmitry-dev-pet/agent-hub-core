# AGENTS.md

## Purpose

This repository is the portable, user-agnostic Agent Hub Core reference implementation.

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
- Keep handoff packets bounded; do not forward complete chat histories.
- Do not introduce a generic privileged shell or universal executor.

## Compatibility

v0.1 schema changes must remain backward compatible unless the package version and
protocol version are intentionally advanced together.
