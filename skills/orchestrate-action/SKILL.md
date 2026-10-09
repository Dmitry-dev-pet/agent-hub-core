---
name: orchestrate-action
description: Execute an authorized Truthrail action through the owning capability and verify the outcome separately from execution.
---

# Orchestrate an action

1. Resolve the exact project from instance routing.
2. Hydrate required current evidence.
3. Define the observable outcome and smallest acceptance proof.
4. Select the lowest sufficient execution level.
5. For privileged work, read the live reviewed operation contract and require
   `agent_routable: true`.
6. Execute inside the declared execution envelope.
7. Record an ExecutionReceipt with status `executed`.
8. Re-read authoritative evidence and produce a separate VerificationResult.

A successful tool call, commit, deployment, or workflow run is not automatically
verification. Preserve `executed != verified`.

Use a bounded HandoffPacket when changing execution venues; do not forward the full
conversation or secret values.
