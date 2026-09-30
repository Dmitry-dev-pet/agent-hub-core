# Cross-vendor Agent Hub demo

This is a deliberately tiny public proof of the Agent Hub model:

> one GitHub-native policy, multiple AI chats, the same real operation.

No Agent Hub-specific connector, server, daemon, workflow, coding agent, MCP gateway,
or custom secret is required.

## The operation

The only routable operation is `demo-record`.

A compliant AI chat reads the policy and live contract, adds one comment to the
public ledger issue, then re-reads the ledger before claiming success.

The durable ledger is issue **#5** in this repository.

## Run it from ChatGPT

Give ChatGPT access to the repository through its normal GitHub connection, then send:

```text
Use the Agent Hub demo policy in demo/AGENTS.md.
Record one public demo entry.
Client: chatgpt.
Follow demo/control-plane.json exactly.
Do not use a coding agent or edit repository files.
Do not claim success until you re-read and verify the public ledger.
```

## Run the same operation from Grok

Give Grok access to the same repository through its normal GitHub connection, then
send:

```text
Use the Agent Hub demo policy in demo/AGENTS.md.
Record one public demo entry.
Client: grok.
Follow demo/control-plane.json exactly.
Do not use a coding agent or edit repository files.
Do not claim success until you re-read and verify the public ledger.
```

The operation and policy are identical. Only the client label differs.

## What observers should see

Both chats should produce the same public route:

```text
AI chat
  -> normal GitHub connection
  -> reads demo/AGENTS.md
  -> reads demo/control-plane.json
  -> writes one comment to issue #5
  -> re-reads issue #5
  -> verifies its own comment
```

The required comment format is:

```text
agent-hub-demo
operation: demo.record
client: <client>
policy: demo/control-plane.json
```

After one ChatGPT run and one Grok run, issue #5 should visibly contain both entries.

## What this proves

GitHub proves that both interactions used the same durable policy surface and the same
operation target. A screenshot or shared transcript from each AI host can be paired
with the public ledger when demonstrating which host produced each entry.

The important architectural point is that the policy and evidence are not stored in
ChatGPT or Grok.

## Security and simplicity

- no custom secrets;
- no background service;
- no workflow runner;
- no autonomous coding agent;
- no direct repository-file mutation;
- L1 direct GitHub mutation is the lowest sufficient level;
- execution is not accepted until the comment is read back.

This demo is intentionally smaller than a full Agent Hub instance. It isolates the
cross-vendor property so it can be understood in under a minute.
