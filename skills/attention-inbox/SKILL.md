---
name: attention-inbox
description: Build a quiet prioritized inbox of items that require the user's decision or action from authoritative live evidence.
---

# Build an actionable attention inbox

Use this skill when the user asks what needs their attention, or when an approved
attention policy calls for triage.

Collect only items that have a concrete reason for the user to act now or soon. Typical
eligible signals are:

- an explicit approval that blocks a durable run;
- a sourced deadline or commitment that falls inside the relevant review window;
- a failure or blocker that prevents an active outcome;
- a direct human request awaiting the user's response when an available capability
  exposes that state;
- a quota or budget risk established by the `quota-guard` skill.

For every item, state the subject, why it needs attention, the authoritative source or
evidence timestamp, the requested next action, and any explicit deadline. Mark
uncertainty instead of turning an inference into a task.

Do not convert routine repository activity, successful workflows, unchanged state, or
low-value informational updates into attention items. Refresh freshness-sensitive
evidence before reporting it.

This skill is triage behavior only. It grants no authority to approve, send, merge,
deploy, spend, or mutate anything. A follow-up action must route through the owning
capability and its approval contract.

If nothing currently requires action, say so briefly instead of padding the inbox.
