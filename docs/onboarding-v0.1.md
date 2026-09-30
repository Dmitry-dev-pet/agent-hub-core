# Agent Hub onboarding protocol v0.1

The onboarding protocol turns an existing GitHub account into a portable Agent Hub
instance without requiring the user to manually inventory repositories or write YAML.

The primary path is **brownfield onboarding**: discover what already exists, normalize
it into an Agent Hub instance, validate it, and prove that a fresh AI session can
recover the same operational model from GitHub.

A **greenfield** account uses the same phases with an empty or minimal discovery set.

## Phases

```text
DISCOVER
  -> CLASSIFY
  -> BUILD
  -> VALIDATE
  -> WATCH
  -> RECEIPT
```

### 1. DISCOVER

Enumerate every repository visible in the selected GitHub account scope.

Discovery should capture enough live metadata to support classification, such as:

- full repository name;
- visibility;
- archived state;
- default branch;
- recent activity timestamps;
- README / AGENTS.md presence;
- GitHub Actions workflows;
- deployment/configuration hints visible from repository state.

Pagination and connector scope matter. If the client cannot establish that discovery
is complete, onboarding cannot be `verified`.

Do not infer that a repository does not exist merely because one connector call did
not return it.

### 2. CLASSIFY

Build project routes and aliases from evidence, not from conversation memory.

Safe automatic classifications include high-confidence relationships supported by
repository names, README/AGENTS content, explicit links, package/deployment metadata,
or reviewed configuration.

Do not archive, delete, rename, change visibility, or otherwise mutate lifecycle state
because a repository merely looks old or experimental.

When two repositories may belong to one project family but evidence is ambiguous,
record an unresolved item instead of guessing.

### 3. BUILD

Create or update the Agent Hub instance.

A portable instance contains at least:

```text
agent-hub.yaml
projects.yaml
capabilities.yaml
credentials.yaml
context/
```

The default baseline can be zero-custom-secret:

- GitHub public reads at L0;
- ambient connected GitHub access at L0/L1 when available;
- provider-managed GitHub Actions at L3.

Only add a privileged reviewed control-plane capability when a live reviewed contract
actually exists.

Credential metadata may be recorded, but credential **values must never be copied**
into the Hub, chat, issues, logs, or receipts.

### 4. VALIDATE

Run structural instance validation.

For a local checkout:

```bash
agent-hub-core validate-instance .agent-hub
agent-hub-core doctor .agent-hub --offline
```

Use live GitHub reads to verify freshness-sensitive repository facts. Public API doctor
checks are useful for public repositories but are not a substitute for connected access
to private repositories.

### 5. WATCH

A watcher/reconciliation loop is optional for onboarding verification.

If a reviewed watcher already exists, configure it to detect repository additions,
removals, lifecycle changes, or other drift. Otherwise mark the phase `skipped`.

A watcher is an acceleration and reconciliation mechanism, not the source of truth.

### 6. RECEIPT

Produce an `onboarding_receipt` document.

The receipt records:

- onboarding mode;
- phase status;
- repositories seen and recorded;
- project-family/capability counts;
- unresolved questions;
- confirmation that no credential values were copied;
- fresh-session recovery result;
- authoritative GitHub references.

Validate it with:

```bash
agent-hub-core validate \
  --kind onboarding_receipt \
  onboarding-receipt.json
```

## Receipt statuses

### verified

Use only when:

- every discovered repository is represented in the Hub inventory;
- DISCOVER, CLASSIFY, BUILD, VALIDATE, and RECEIPT completed;
- WATCH completed or was intentionally skipped;
- unresolved queue is empty;
- fresh-session recovery was performed and passed;
- no credential values were copied.

### partial

Use when the Hub is operational and recoverable but semantic ambiguities remain.

A partial receipt still requires:

- every discovered repository recorded;
- structural validation passed;
- fresh-session recovery passed;
- at least one explicit unresolved item.

This is preferable to guessing.

### blocked

Use when onboarding cannot produce a trustworthy operational instance, for example
because repository discovery is incomplete, write access needed for the instance is
missing, validation fails, or fresh recovery cannot be performed.

## Fresh-session recovery

Fresh recovery is the decisive portability test.

Start a new AI session with no dependence on previous conversation memory. Give it only
the GitHub account / Agent Hub entry point needed to locate the instance.

The fresh client must rebuild the operational model from GitHub and demonstrate that it
can:

1. identify the Hub owner;
2. load the project inventory;
3. resolve the configured repository set;
4. load capabilities and credential metadata without secret values;
5. report unresolved items exactly as persisted;
6. distinguish durable Hub metadata from freshness-sensitive live GitHub state.

A second AI vendor is ideal but not required. The protocol tests recovery from durable
GitHub state, not brand identity.

## Acceptance principle

```text
discovered != classified
classified != built
built != validated
validated != recoverable
recoverable + complete + unambiguous = verified onboarding
```

The user should not need to manually transcribe repository lists or fill configuration
files when the connected GitHub surface already contains the required evidence.
