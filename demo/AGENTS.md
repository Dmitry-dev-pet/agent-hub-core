# Cross-vendor demo policy

This directory is a live, zero-custom-secret Truthrail demo.

## User goal

Record one public proof entry from the current AI host.

## Authoritative state

- `demo/control-plane.json` is the live operation contract.
- GitHub Issues in this repository are the durable evidence.
- Issue #5 is the public demo index.

Do not treat conversation memory as authoritative.

## Required routing

For a demo record request:

1. Read `demo/control-plane.json`.
2. Select the agent-routable `demo-record` operation.
3. Use the normal connected GitHub interface. No coding agent or separate runtime is
   needed.
4. Create exactly one public issue with this title:

   ```text
   [agent-hub-demo] <client>
   ```

5. Use exactly this three-line body:

   ```text
   agent-hub-demo
   client: <client>
   policy: demo/control-plane.json
   ```

6. Re-read the newly created issue by its returned issue number.
7. Do not claim success until the title and body visible from GitHub exactly match the
   requested client and policy.

Do not edit repository files or invoke a workflow as part of this operation. The
lowest sufficient execution level is L1: one direct GitHub issue creation followed by
a read-back.

## Why this demo exists

The point is not the issue. The point is that different AI hosts can discover and obey
the same GitHub-native policy without a Truthrail-specific connector, daemon, agent
runtime, workflow, MCP gateway, or custom secret.

The chat is the interface. GitHub is authoritative state. Executed is not verified.
