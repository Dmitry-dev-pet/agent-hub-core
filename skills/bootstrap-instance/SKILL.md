---
name: bootstrap-instance
description: Discover an existing GitHub account and build or refresh a portable Agent Hub instance with explicit unresolved items and a verifiable onboarding receipt.
---

# Bootstrap an Agent Hub instance

Use this skill when the user asks to set up, bootstrap, rebuild, or onboard an Agent
Hub for an existing GitHub account.

Brownfield discovery is the default. Do not assume the account is empty.

## Goal

Turn the GitHub state the user already has into a portable Agent Hub instance that a
fresh AI session can recover without relying on the current conversation.

Follow these phases in order:

```text
DISCOVER -> CLASSIFY -> BUILD -> VALIDATE -> WATCH -> RECEIPT
```

## DISCOVER

Enumerate the complete repository set available in the selected account scope. Follow
pagination and connector-specific continuation until complete.

Use live GitHub evidence for repository metadata. Do not infer absence from one partial
listing or a stale Hub inventory.

If discovery completeness cannot be established, do not issue a verified or partial
receipt.

## CLASSIFY

Build project IDs, aliases, families, and lifecycle observations from repository
evidence.

Prefer conservative normalization:

- preserve every discovered repository;
- group repositories only when evidence is strong;
- never archive/delete/change visibility based on classification;
- put ambiguous relationships in the unresolved queue.

Do not ask the user questions that can be answered from GitHub itself.

## BUILD

If a compatible Agent Hub already exists, update it rather than creating a competing
source of truth.

Otherwise create a dedicated private Hub repository or user-approved equivalent and
write the portable instance files.

Baseline onboarding should require zero custom secrets whenever possible. Record
credential names/routes only when needed; never retrieve or copy credential values.

Add reviewed privileged capabilities only from live reviewed contracts. Do not invent
commands from examples or chat history.

## VALIDATE

Validate the instance structure and credential boundary.

Use `agent-hub-core validate-instance` when available. Use live GitHub reads for
freshness-sensitive facts. Treat public API checks as supplemental when private
repositories are in scope.

Every discovered repository must be represented before an onboarding receipt can be
`verified` or `partial`.

## WATCH

Configure an existing reviewed watcher/reconciliation loop when one is available and
useful. Otherwise mark WATCH as `skipped`.

Do not make onboarding depend on a new background service merely to satisfy this phase.

## RECEIPT

Produce an `onboarding_receipt` document and validate it.

Status rules:

- `verified`: complete inventory, no unresolved items, validation passed, fresh
  recovery passed;
- `partial`: complete inventory and recovery passed, but explicit unresolved items
  remain;
- `blocked`: completeness, build, validation, or recovery cannot be established.

No receipt may claim that credential values were copied.

## Fresh recovery

Use a fresh chat/session after the Hub is built.

The recovery client should receive only the GitHub/Hub entry point, not the previous
conversation. It must reload the Hub and reconstruct owner, repository inventory,
project routing, capabilities, credential metadata, and unresolved items from GitHub.

Prefer a second AI vendor when convenient, because that additionally demonstrates
vendor portability, but same-vendor fresh-session recovery is sufficient for protocol
verification.

## Completion report

Report:

- repositories discovered / recorded;
- project families;
- capabilities;
- unresolved count and questions;
- watcher completed or skipped;
- fresh-recovery client and result;
- receipt status and authoritative references.

Do not report onboarding as verified when only the Hub repository was created.
