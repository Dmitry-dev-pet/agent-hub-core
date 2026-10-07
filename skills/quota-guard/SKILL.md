---
name: quota-guard
description: Inspect authoritative usage, quota, budget, and rate-limit evidence and surface only decision-relevant capacity risk without changing spend or routing.
---

# Guard quotas and capacity

Use this skill to inspect provider or capability usage that can affect whether planned
work will complete safely or economically.

Read current usage from authoritative provider or control-plane evidence when available.
Examples include CI minutes, model budgets, API rate limits, deployment allowances,
storage, or compute allocations.

Never guess a user's limit, balance, reset time, or billing state from generic
documentation. A warning or critical threshold must come from one of:

- an explicit user preference;
- instance configuration;
- a provider-defined warning/state;
- a capability contract that defines the threshold.

If no threshold exists, report measured usage without inventing one.

For a decision-relevant risk, report the resource, measurement period or reset time when
known, used/remaining capacity, the source of the threshold, likely impact on current
work, and the narrowest reasonable alternative.

Alternatives are advisory only. This skill may not purchase capacity, change a billing
plan, move work to a different paid provider, alter credentials, or reroute execution by
itself. Any such action must use the owning capability and the required approval.
