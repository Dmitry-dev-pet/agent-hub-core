# Truthrail onboarding protocol v0.1

Truthrail onboarding is chat-first. The user should not have to enumerate repositories,
write YAML, or install a local runtime when the connected GitHub surface already
contains the required evidence.

The canonical machine-readable entry point is `onboarding/contract.yaml`. AI clients
may use `skills/bootstrap-instance/SKILL.md` as the portable execution guidance.

## Permission ladder

Onboarding should request the **least access necessary**.

1. **Explore** — read only. Inspect public repositories or only the repositories the
   user approved. Do not create, edit, or delete anything.
2. **Connect** — write only to one private Truthrail instance so durable routing and
   context can be stored. Prefer a user-created private repository from the public
   Truthrail Core template when available; otherwise use an empty private repository.
   A public fork is for core development, not private instance state. Project repositories
   may remain read-only and may be added gradually.
3. **Name** — optionally choose a chat-facing assistant name and store a small assistant
   profile in the private instance. The profile is identity/continuity metadata only;
   renaming never grants or removes capabilities.
4. **Operate** — optional. Add write-capable project/infrastructure capabilities later,
   one target and one reviewed capability at a time.

Full-account GitHub write access is not required.

Repository selection and permission controls vary by GitHub connection/provider. When
fine-grained private-repository selection is unavailable, a user may start with public
repository URLs and connect private repositories later.

A `verified` or `partial` receipt is complete **within the GitHub scope the user
approved**. It must not imply visibility into repositories outside that scope.

## Choose the onboarding mode

There are two user-facing cases.

### Brownfield — repositories already exist

Use brownfield mode when the GitHub account already contains project repositories.

The AI client should:

1. discover the complete visible repository set;
2. classify only relationships supported by evidence;
3. create or update one private Truthrail instance;
4. preserve ambiguous relationships as unresolved instead of guessing;
5. validate the instance and secret-value boundary;
6. configure a reviewed watcher when one already exists and is useful, otherwise skip it;
7. prove fresh-session recovery.

### Greenfield — the GitHub account is empty

Use greenfield mode when the account has no project repositories and no existing
Truthrail instance.

The AI client should:

1. confirm that the visible project repository set is empty;
2. **not invent projects, aliases, context, or relationships**;
3. create one private Truthrail instance for the account;
4. write an empty project inventory plus baseline GitHub capabilities;
5. keep credential routes empty unless a real reviewed capability requires metadata;
6. validate the instance;
7. prove from a completely fresh chat that the owner, empty inventory, capabilities,
   and unresolved state can be recovered.

A greenfield onboarding may be `verified` with zero projects. Zero projects is a valid
authoritative state, not an onboarding failure.

When the first real repository appears later, rerun discovery and update the **existing**
Truthrail instance. Do not create a second instance.

## Shared phases

Both modes use the same lifecycle:

```text
DISCOVER -> CLASSIFY -> BUILD -> VALIDATE -> WATCH -> RECEIPT
```

For greenfield onboarding, CLASSIFY is intentionally a no-op when there are no projects.

### DISCOVER

Enumerate the complete repository set visible in the selected GitHub account scope.
Follow pagination and connector continuation until complete.

Use live GitHub evidence. Do not infer absence from one partial listing.

If discovery completeness cannot be established, onboarding cannot be `verified`.

### CLASSIFY

For brownfield accounts, build project IDs, aliases, families, and lifecycle
observations from repository evidence such as README/AGENTS content, explicit links,
package/deployment metadata, and reviewed configuration.

Never archive, delete, rename, or change visibility during classification.

For greenfield accounts with no project repositories, record an empty inventory and do
not synthesize placeholder projects.

### BUILD

If a compatible Truthrail instance already exists, update it rather than creating a
competing source of truth.

Otherwise create one dedicated private Truthrail repository or user-approved equivalent.

A portable instance contains at least:

```text
agent-hub.yaml
projects.yaml
capabilities.yaml
credentials.yaml
context/
```

It may also contain an assistant profile such as `assistant.yaml` with a user-selected
name and chat role. This profile must not contain secret values or redefine capability
authority. It is safe to rename independently of permissions.

The default baseline can be zero-custom-secret:

- GitHub public reads at L0;
- ambient connected GitHub access at L0/L1 when available;
- provider-managed GitHub Actions at L3.

Credential metadata may be recorded, but credential **values must never be copied**
into Truthrail, chat, issues, logs, or receipts.

### VALIDATE

Validate the instance structure, project coverage, and credential boundary.

Low-level CLI validation is an implementation option, not a user onboarding step.
Live GitHub reads remain authoritative for freshness-sensitive facts.

For brownfield onboarding, every discovered repository must be represented before a
receipt can be `verified` or `partial`.

For greenfield onboarding, an explicitly empty project inventory satisfies coverage
when discovery proved that no project repositories exist.

### WATCH

A watcher/reconciliation loop is optional for onboarding verification.

If a reviewed watcher already exists, configure it to detect repository additions,
removals, lifecycle changes, or other drift. Otherwise mark WATCH as `skipped`.

A watcher is an acceleration mechanism, not the source of truth.

### RECEIPT

Produce an `onboarding_receipt` recording:

- onboarding mode;
- phase status;
- repositories seen and recorded;
- project-family/capability counts;
- unresolved questions;
- confirmation that no credential values were copied;
- fresh-session recovery result;
- authoritative GitHub references.

## Receipt statuses

### verified

Use when:

- discovery is complete;
- the inventory exactly represents the discovered state, including a valid empty
  inventory in greenfield mode;
- validation passed;
- WATCH completed or was intentionally skipped;
- unresolved queue is empty;
- fresh-session recovery passed;
- no credential values were copied.

### partial

Use when the instance is complete and recoverable but explicit semantic ambiguities
remain. This normally applies to brownfield onboarding.

### blocked

Use when discovery completeness, instance creation/update, validation, or fresh recovery
cannot be established.

## Fresh-session recovery

Fresh recovery is the decisive portability test.

Start a new AI session without the previous transcript. Give it only the GitHub account
and Truthrail entry point needed to locate the instance.

The fresh client must recover:

1. owner;
2. repository inventory — including an intentionally empty inventory;
3. project routing;
4. capabilities;
5. credential metadata without secret values;
6. optional assistant profile/name when configured;
7. unresolved items.

It must re-read freshness-sensitive live state rather than trusting persisted narrative.

## Acceptance principle

```text
discovered != classified
classified != built
built != validated
validated != recoverable
recoverable + complete + unambiguous = verified onboarding
```

For a greenfield account, `complete` may legitimately mean **zero projects**.
