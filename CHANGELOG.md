# Changelog

## Unreleased

- add additive work continuity v0.2 schemas with stable `run_id` across WorkPacket, plan, receipt, verification, handoff, and lifecycle documents;
- add source-channel and approval-policy metadata plus waiting/rejected/failed/cancelled lifecycle outcomes;
- add mixed-run bundle validation and explicit CLI schema-version selection while preserving v0.1 defaults;

- add runtime operation admission v1 with ADMIT / REQUIRE_HUMAN / DENY decisions;
- add explicit per-operation admission mode/requester metadata and fail-closed semantics;
- add machine-readable `capabilities/admission-v1.yaml`, decision schema, CLI and tests;

- add deterministic capability policy v1 with PASS / REVIEW / BLOCK decisions;
- publish machine-readable `capabilities/policy-v1.yaml`;
- add `truthrail capability-policy` with optional CI enforcement thresholds;

- add deterministic reviewed-control-plane capability diffs with Markdown/JSON output;
- add explicit operation metadata for GitHub permissions, network destinations, external side effects, cost ceilings, human gates, runtime auth and execution venues;
- add optional `--fail-on-expansion` CI policy without making blocking the protocol default;

- adopt **Truthrail** as the product name with the tagline `One source of truth. Any AI.`;
- add the preferred `truthrail` CLI while retaining `agent-hub-core` for v0.1 compatibility;
- keep legacy Python package, on-disk paths, and schema identifiers stable during the rename;

- add progressive capability readiness states: ready / degraded / dormant / blocked;
- add machine-readable `capabilities/contract.yaml`;
- add executable `capability_readiness` and `capability_activation_receipt` schemas;
- separate optional capability activation from core Hub onboarding;
- add portable activation skill, examples, semantic validation and tests;
- add brownfield-first onboarding protocol with DISCOVER → CLASSIFY → BUILD → VALIDATE → WATCH → RECEIPT phases;
- add machine-readable `onboarding/contract.yaml` and portable bootstrap skill;
- add executable `onboarding_receipt` schema with verified / partial / blocked semantics;
- require complete discovered-repository coverage and successful fresh-session recovery for verified/partial receipts;
- add onboarding examples and acceptance tests.

## 0.1.1 — 2026-09-30

- add zero-custom-secret instance bootstrap;
- add `validate-instance` and `doctor`;
- default to public GitHub reads, optional ambient GitHub auth, and provider-managed
  GitHub Actions credentials;
- reject secret-value fields from instance credential metadata;
- add deterministic second-instance bootstrap acceptance to CI.

## 0.1.0 — 2026-09-30

Initial public core:

- executable v0.1 JSON Schemas;
- semantic protocol validator;
- L0-L5 reference routing adapter;
- reviewed control-plane contract schema;
- deterministic end-to-end conformance scenario;
- CLI;
- generic installation examples and agent skills;
- public-tree hygiene audit.
