---
name: rebuild-context
description: Rebuild a project's authoritative current context from an Agent Hub instance without relying on conversation memory.
---

# Rebuild project context

Start from the instance configuration, resolve the project alias, then read live
authoritative state for freshness-sensitive facts.

Use this precedence:

1. live target-system evidence;
2. reviewed control-plane configuration;
3. current instance routing/capability metadata;
4. lifecycle inventory;
5. reconciliation cache;
6. conversation memory.

Durable context may hold goals, decisions, constraints, rejected options, and pointers.
Do not store current branches, workflow status, deployments, or runtime state as durable truth.

For a broad account view, inspect unresolved reconciliation events before ordinary
activity. Events are observations, not authorization to mutate anything.
