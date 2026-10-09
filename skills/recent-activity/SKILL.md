---
name: recent-activity
description: Reconstruct fresh activity across an Truthrail instance using reconciliation hints plus authoritative live verification.
---

# Reconstruct recent activity

Use scheduled watcher/snapshot output only as an acceleration layer. Surface unresolved
inventory events first, then live-verify repositories that materially affect the answer.

For each relevant repository, read only what is necessary: default-branch state, recent
commits, open pull requests, Actions/workflow state, and materially active feature branches.

Do not infer inactivity from a partial snapshot. Do not equate a push with a deployment.
For all-project questions, enumerate the canonical lifecycle inventory rather than only
repositories remembered from chat.
