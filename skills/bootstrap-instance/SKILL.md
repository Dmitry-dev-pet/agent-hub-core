---
name: bootstrap-instance
description: Onboard an existing or empty GitHub account into one portable Truthrail instance and verify fresh-session recovery.
---

# Bootstrap a Truthrail instance

Use this skill when the user asks to set up, bootstrap, rebuild, refresh, or onboard
Truthrail for a GitHub account.

The user should not need to manually list repositories or write YAML when GitHub already
contains the required evidence.

## Access policy: start read-only

Use the least privilege available in the current GitHub connection.

- Start with **Explore**: public repositories or user-approved repository scope,
  read-only, no mutations.
- Move to **Connect** only after the user wants persistence: create/update one private
  Truthrail instance; do not require write access to project repositories.
- Move to **Operate** only when the user asks for actions: enable write-capable
  permissions/control planes for the specific project or service that needs them.

Never request full-account write access merely to perform onboarding.

If the connector/provider cannot offer fine-grained private-repository selection,
support a public-repository Explore path rather than treating broad private access as
mandatory.

Completeness means complete within the user-approved GitHub scope. Never claim that
unseen repositories do not exist.

## First: choose the mode from live GitHub

Enumerate the complete visible repository set before deciding the mode.

- **Brownfield:** one or more project repositories already exist, or a compatible
  Truthrail instance already exists.
- **Greenfield:** no project repositories exist and there is no existing Truthrail
  instance.

Do not ask the user which mode applies if live GitHub can answer it.

## Brownfield goal

Turn the existing GitHub state into one portable Truthrail instance that a fresh AI
session can recover without relying on conversation history.

Follow:

```text
DISCOVER -> CLASSIFY -> BUILD -> VALIDATE -> WATCH -> RECEIPT
```

### DISCOVER

Enumerate the complete repository set. Follow pagination/continuation until complete.

Use live GitHub evidence. Do not infer absence from one partial listing or stale state.

### CLASSIFY

Build project IDs, aliases, families, and durable context only from evidence.

- preserve every discovered repository;
- group repositories only when evidence is strong;
- never mutate repository lifecycle during classification;
- put ambiguity in the unresolved queue instead of guessing.

### BUILD

If a compatible Truthrail instance exists, update it.

Otherwise create one dedicated private Truthrail repository or user-approved equivalent.

Record project routing, capability metadata, credential names/routes when needed, and
durable context. Never retrieve or copy credential values.

### VALIDATE

Validate structure, repository coverage, and credential boundaries. Use live GitHub for
freshness-sensitive facts.

### WATCH

Configure a reviewed watcher if one already exists and is useful. Otherwise mark WATCH
as skipped. Do not invent a new always-on service just to satisfy this phase.

### RECEIPT

Produce a validated onboarding receipt:

- `verified`: complete inventory, no unresolved items, fresh recovery passed;
- `partial`: complete inventory and recovery passed, explicit ambiguities remain;
- `blocked`: completeness/build/validation/recovery cannot be established.

## Greenfield goal

Create a recoverable Truthrail instance for an account that currently has no project
repositories.

Do **not** invent placeholder projects.

1. DISCOVER and prove that the visible project repository set is empty.
2. CLASSIFY as an intentional no-op.
3. BUILD one private Truthrail instance with:
   - empty project inventory;
   - baseline GitHub capabilities;
   - empty credential routes unless real capability metadata is required;
   - empty/minimal durable context.
4. VALIDATE the empty inventory and credential boundary.
5. WATCH may be configured or skipped.
6. Run fresh-session recovery.
7. Emit `verified` when the new chat can recover the owner, empty inventory,
   capabilities, unresolved state, and no secret values.

Zero projects is a valid state.

When the account later gains its first project repository, refresh the existing
Truthrail instance. Never create a second instance merely because the account changed
from greenfield to brownfield.

## Fresh recovery

Use a completely new chat/session after BUILD and VALIDATE.

Do not pass the previous transcript or a hand-written summary.

The recovery client should locate the Truthrail instance from GitHub and reconstruct:

- owner;
- repository inventory, including an intentional empty inventory;
- project routing;
- capabilities;
- credential metadata without secret values;
- unresolved items.

Refresh live GitHub before making freshness-sensitive claims.

## Completion report

Report only what matters to the user:

- onboarding mode: brownfield or greenfield;
- repositories discovered / recorded;
- unresolved count;
- watcher configured or skipped;
- fresh recovery result;
- receipt status.

Do not report onboarding as verified when only the Truthrail repository was created and
fresh recovery was not proven.
