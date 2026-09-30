# Changelog

## Unreleased

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
