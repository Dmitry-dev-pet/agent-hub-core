# Truthrail boundaries v0.3

Truthrail has four separate concerns. Keeping them separate is a compatibility and
security property, not only a code-organization preference.

```text
assistant profile
      |
      v
private Truthrail instance
      |
      v
Truthrail Core
      |
      v
capabilities / reviewed control planes
```

## 1. Assistant profile

The assistant profile describes identity and behavior:

- display name and role;
- goals and attention policy;
- enabled skill **IDs**;
- behavioral rules.

It does not own protocol implementation, credential values, runtime topology, workflow
paths, issue triggers, runner labels, or operation contracts. A skill ID is resolved by
Truthrail Core or the host integration.

Renaming an assistant never changes authority.

## 2. Private Truthrail instance

A private instance owns user-specific durable state and routing overlays:

- project inventory and aliases;
- durable context, decisions, goals and constraints;
- assistant profile;
- capability references and credential metadata;
- run-ledger state and references to authoritative systems.

An instance may keep thin compatibility shims needed by an older consumer, but it must
not maintain an independent copy of the Truthrail protocol implementation or portable
schemas. Freshness-sensitive state remains authoritative in the live target system.

## 3. Truthrail Core

Core owns portable mechanism:

- protocol schemas and semantic validation;
- execution-level and lifecycle semantics;
- portable assistant skills;
- instance validation/bootstrap rules;
- capability routing/admission/policy helpers;
- compatibility adapters.

The canonical Python namespace is `truthrail_core`. The legacy
`agent_hub_core` namespace remains supported during the compatibility window.

The canonical CLI is `truthrail`. The legacy `agent-hub-core` command remains an
alias.

## 4. Capabilities and control planes

Capabilities own the concrete operation surface. A reviewed control plane publishes its
live operation contract, including admission, execution venue, required permissions and
verification evidence.

Core routes to capabilities; it does not copy their operation lists. Assistant profiles
do not hard-code their workflow paths or triggers.

## Compatibility quarantine

Legacy Agent Hub identifiers are allowed only where removing them would break an
existing consumer. New code and documentation use Truthrail names.

| Concern | Canonical | Compatibility |
| --- | --- | --- |
| product | Truthrail | Agent Hub |
| CLI | `truthrail` | `agent-hub-core` |
| Python import | `truthrail_core` | `agent_hub_core` |
| private instance | `truthrail` | `agent-hub` aliases where required |
| portable skills | skill IDs | physical legacy plugin paths only in adapters |

Compatibility code should point inward to the canonical implementation. Do not create a
second implementation under a legacy name.

## Lifecycle invariant

Boundary cleanup does not change the execution lifecycle:

```text
executing -> executed -> verifying -> verified
```

`executed` records that an executor completed its operation. Only independent
acceptance evidence may move the run to `verified`.
