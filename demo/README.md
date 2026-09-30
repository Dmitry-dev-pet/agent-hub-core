# Cross-vendor Agent Hub demo

This is a deliberately tiny public proof of the Agent Hub model:

> one GitHub-native policy, multiple AI chats, the same real operation.

No Agent Hub-specific connector, server, daemon, workflow, coding agent, MCP gateway,
or custom secret is required.

## The operation

The only routable operation is `demo-record`.

A compliant AI chat reads the policy and live contract, creates one public proof
issue, then re-reads that issue before claiming success.

Issue **#5** is the public index explaining the demo. Each run creates a separate
public receipt issue.

## Run it from ChatGPT

Give ChatGPT access to the repository through its normal GitHub connection, then send:

```text
Use the Agent Hub demo policy in demo/AGENTS.md.
Record one public demo entry.
Client: chatgpt.
Follow demo/control-plane.json exactly.
Do not use a coding agent, workflow, or repository file edit.
Do not claim success until you re-read and verify the created GitHub issue.
```

## Run the same operation from Grok

Give Grok access to the same repository through its normal GitHub connection, then
send:

```text
Use the Agent Hub demo policy in demo/AGENTS.md.
Record one public demo entry.
Client: grok.
Follow demo/control-plane.json exactly.
Do not use a coding agent, workflow, or repository file edit.
Do not claim success until you re-read and verify the created GitHub issue.
```

The operation and policy are identical. Only the client label differs.

## What observers should see

Both chats should produce the same public route:

```text
AI chat
  -> normal GitHub connection
  -> reads demo/AGENTS.md
  -> reads demo/control-plane.json
  -> creates [agent-hub-demo] <client> issue
  -> re-reads that issue
  -> verifies title + body
```

The required issue body is:

```text
agent-hub-demo
client: <client>
policy: demo/control-plane.json
```

After one ChatGPT run and one Grok run, the public issue list should visibly contain
both receipts.

## What this proves

GitHub proves that both interactions used the same durable policy surface and the same
operation shape. A screenshot or shared transcript from each AI host can be paired
with its public receipt issue when demonstrating which host produced each entry.

The important architectural point is that the policy and evidence are not stored in
ChatGPT or Grok.

## Security and simplicity

- no custom secrets;
- no background service;
- no workflow runner;
- no autonomous coding agent;
- no repository-file mutation;
- L1 direct GitHub mutation is the lowest sufficient level;
- execution is not accepted until the issue is read back.

This demo is intentionally smaller than a full Agent Hub instance. It isolates the
cross-vendor property so it can be understood in under a minute.
