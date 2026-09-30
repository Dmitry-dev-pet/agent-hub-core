# Cross-vendor demo policy

This directory is a live, zero-custom-secret Agent Hub demo.

## User goal

Record one public proof entry from the current AI host.

## Authoritative state

- `demo/control-plane.json` is the live operation contract.
- Public issue **#5** is the durable demo ledger.
- The issue comment list is authoritative evidence.

Do not treat conversation memory as authoritative.

## Required routing

For a demo record request:

1. Read `demo/control-plane.json`.
2. Select the agent-routable `demo-record` operation.
3. Use the normal connected GitHub interface. No coding agent or separate runtime is
   needed.
4. Add exactly one comment to issue #5 with this four-line format:

   ```text
   agent-hub-demo
   operation: demo.record
   client: <client>
   policy: demo/control-plane.json
   ```

5. Re-read the comments on issue #5.
6. Do not claim success until the newly written comment is visible with the exact
   operation, client, and policy values.

Do not edit repository files as part of this operation. The lowest sufficient
execution level is L1: a direct GitHub comment mutation followed by a read-back.

## Why this demo exists

The point is not the comment. The point is that different AI hosts can discover and
obey the same GitHub-native policy without an Agent Hub-specific connector, daemon,
agent runtime, workflow, MCP gateway, or custom secret.

The chat is the interface. GitHub is authoritative state. Executed is not verified.
