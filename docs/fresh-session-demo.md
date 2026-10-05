# Fresh-session continuity demo

This demo proves a different property from the cross-vendor demo:

> the next AI chat can continue work from durable external state without receiving the previous transcript.

It does not require an always-on laptop or a permanent Truthrail daemon. The only
authoritative system in this minimal example is GitHub.

## What you need

- a GitHub repository you control;
- an AI chat with normal GitHub read/write access to that repository;
- no Truthrail-specific server, MCP gateway, local runner, or custom secret.

Use a disposable test repository or test issue tracker. Do not run this recipe in a
repository where creating test issues would be disruptive.

## Chat 1 — leave unfinished work

Ask the first chat to create one issue with this exact title:

```text
[truthrail-run-demo] fresh-session continuity
```

Use this body, replacing `OWNER/REPO` with the test repository:

```text
truthrail-continuity-demo:v1
run_id: demo-fresh-session-001
state: planned
outcome: prove that a new chat can resume from GitHub without the previous transcript
next_action: create one issue titled [truthrail-marker] fresh-session continuity
acceptance_proof:
  - the marker issue exists in OWNER/REPO
  - its body is exactly: created by the Truthrail fresh-session continuity demo
  - the marker issue is re-read from GitHub before this run is completed
```

Then end the chat. Do not create the marker issue yet.

## Chat 2 — no previous transcript

Open a completely new chat. Do not paste the old conversation or a summary.

Give it only this bootstrap instruction:

```text
Use OWNER/REPO as authoritative state.
Find the newest open issue whose title starts with [truthrail-run-demo].
Continue that run from its recorded next_action.
Do not trust conversation memory for current state.
Verify the acceptance_proof by re-reading GitHub before marking the run complete.
```

A successful second chat should:

1. find the open run issue;
2. read its current body;
3. create exactly one marker issue titled
   `[truthrail-marker] fresh-session continuity`;
4. use exactly this marker body:

   ```text
   created by the Truthrail fresh-session continuity demo
   ```

5. re-read that marker issue from GitHub;
6. update the run issue to `state: verified` only after the read-back matches the
   acceptance proof;
7. close the run issue.

## What this proves

The second chat did not need the first transcript. The durable coordination state
lived outside the conversation, and completion depended on fresh evidence from the
authoritative system.

The issue format in this demo is intentionally tiny. Production Truthrail instances
can represent continuity with the v0.2 WorkPacket/lifecycle documents or a
GitHub-backed run ledger built on the same invariants.

## What this does not prove

This demo does not grant privileged infrastructure access, provide a secret manager,
or turn GitHub Issues into a universal task database. It demonstrates only the
continuity rule:

```text
conversation state is disposable
durable work state is external
live evidence decides whether the work is complete
```

For deterministic protocol-level coverage without any external writes, run:

```bash
truthrail conformance
```

The conformance harness includes fresh-session recovery without conversation memory.
