# Truthrail Watch semantics v0.2

Truthrail Watch is an optional observation layer. It helps a durable Truthrail instance
notice when recorded lifecycle/classification metadata may no longer match live activity.

Watch is advisory. It is not an autonomous writer.

## Lifecycle activity advisories

A reference policy may raise a lifecycle advisory when a project is recorded as dormant
but multiple independent recent activity signals are visible.

Useful signal kinds include:

- a recent commit on the default branch;
- a recently updated open pull request;
- a recent workflow run.

The private reference deployment currently uses a 14-day activity window and requires at
least two different signal kinds before surfacing an advisory. Those thresholds are policy
choices, not extra execution authority.

## What an advisory means

An advisory means:

> live evidence suggests that a human or controlling agent should review the recorded
> lifecycle/classification state.

It does **not** mean:

- automatically change `dormant` to `active`;
- infer that silence means dormancy;
- authorize a write;
- prove that a requested run succeeded;
- replace normal verification.

If source data was reused after a failed/stale read, implementations should avoid promoting
that stale snapshot into a high-confidence lifecycle advisory.

## Relationship to run verification

Watch and run verification solve different problems.

- **Watch** asks whether durable metadata may be stale relative to live activity.
- **Verification** checks whether one concrete run achieved its requested outcome.

A Watch advisory can cause review or context refresh, but only verification evidence can
move a run from lifecycle `verifying` to lifecycle `verified`.

## Safe default

The safe default is review-only:

1. observe live signals;
2. surface the mismatch;
3. refresh authoritative evidence;
4. ask for or apply the normal policy-governed reconciliation path;
5. never mutate state merely because the watcher noticed activity.
