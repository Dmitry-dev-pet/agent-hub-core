# Cross-vendor demo policy

This directory is a live, zero-custom-secret Agent Hub demo.

## User goal

A user may ask an AI chat to increment the public demo counter and identify the
client that is making the request.

## Authoritative state

- `demo/control-plane.json` is the live operation contract.
- `demo/state.json` is the public durable state.
- GitHub Issues and Actions are the execution and receipt surfaces.

Do not treat conversation memory as authoritative.

## Required routing

For an increment request:

1. Read `demo/control-plane.json`.
2. Select the agent-routable `demo-increment` operation.
3. Do **not** edit `demo/state.json` directly, even when the chat has a direct
   GitHub file-write tool.
4. Open an issue with the exact title:
   `[demo-increment] <client>`
5. Use this exact JSON body:
   `{"confirm":"DEMO_INCREMENT"}`
6. Do not claim success when the issue is merely created.
7. Verify completion only after the issue is closed by the workflow and
   `demo/state.json` on the default branch contains the issue number and client.

The repository workflow accepts mutation requests only from the repository owner.
Forks therefore remain independently reproducible by their own owners.

## Why this demo exists

The point is not the counter. The point is that different AI hosts can discover and
obey the same GitHub-native policy without an Agent Hub-specific connector, daemon,
agent runtime, or custom secret.

The chat is the interface. GitHub is authoritative state. Executed is not verified.
