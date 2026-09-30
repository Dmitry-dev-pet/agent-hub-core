---
name: capability-route
description: Select the narrowest safe capability and execution level, including live reviewed control-plane contracts, without exposing credential values.
---

# Route capabilities safely

Choose the lowest sufficient level:

- L0 live read/reason;
- L1 direct API/connector;
- L2 reviewed control plane;
- L3 ephemeral runtime;
- L4 coding agent;
- L5 machine-bound executor.

When a capability declares an `operations_contract`, read the owning repository's live
contract before routing. Never infer a privileged command from old examples or memory.
Invoke only operations whose contract explicitly says `agent_routable: true`.

Credential routes contain metadata only. Prefer the owning consumer capability; never
ask for or copy the underlying secret value when a safe route exists.

Do not replace a missing narrow capability with a generic shell, unrestricted SSH, or a
broader credential.
