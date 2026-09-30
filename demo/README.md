# Cross-vendor Agent Hub demo

This is a deliberately tiny public proof of the Agent Hub model:

> one GitHub-native policy, multiple AI chats, the same real operation.

No Agent Hub-specific connector, server, daemon, coding agent, MCP gateway, or custom
secret is required.

## The operation

The only routable operation is `demo-increment`.

A compliant AI chat must **not** edit `state.json` directly. It reads
`control-plane.json`, opens the reviewed issue command, waits for execution, and
verifies the resulting default-branch state.

## Run it from ChatGPT

Give ChatGPT access to the repository through its normal GitHub connection, then send:

```text
Use the Agent Hub demo policy in demo/AGENTS.md.
Increment the public demo counter.
Client: chatgpt.
Follow the live control-plane contract exactly.
Do not edit demo/state.json directly.
Do not claim success until the outcome is verified.
```

## Run the same operation from Grok

Give Grok access to the same repository through its normal GitHub connection, then send:

```text
Use the Agent Hub demo policy in demo/AGENTS.md.
Increment the public demo counter.
Client: grok.
Follow the live control-plane contract exactly.
Do not edit demo/state.json directly.
Do not claim success until the outcome is verified.
```

The operation is identical. Only the client label differs.

## What observers should see

For each run there should be a public chain of evidence:

```text
AI chat
  -> reads demo/AGENTS.md
  -> reads demo/control-plane.json
  -> opens [demo-increment] <client> issue
  -> GitHub Actions serializes the mutation
  -> demo/state.json changes on main
  -> workflow re-reads origin/main
  -> issue receives a receipt and closes
```

After one ChatGPT run and one Grok run, the counter should have advanced twice and
the public history should contain both client labels.

## Security properties

- mutation is owner-only on the canonical repository;
- forks are independently runnable by their owners;
- no custom secrets are required;
- execution uses only GitHub's run-scoped `GITHUB_TOKEN`;
- direct state edits are forbidden by the published policy;
- issue creation is not treated as success;
- verification reads the pushed default-branch state.

This demo is intentionally smaller than a full Agent Hub instance. It isolates the
cross-vendor property so it can be understood in under a minute.
