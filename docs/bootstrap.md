# Zero-custom-secret bootstrap

Truthrail Core separates **authentication for a capability** from the core protocol.

A fresh instance can start without any user-managed secret. The legacy `agent-hub-core` CLI remains an alias for v0.1 compatibility. Public GitHub reads use
unauthenticated API access, direct connected operations may use ambient host
authentication when available, and GitHub Actions can use GitHub's provider-managed
`GITHUB_TOKEN`.

## Create an instance

```bash
truthrail init --owner example-org \
  --project example-org/public-repo-one \
  --project example-org/public-repo-two
```

No credential values or placeholder tokens are generated.

## Validate

```bash
truthrail validate-instance
```

The validator checks file boundaries, project/alias consistency, execution levels,
reviewed control-plane pointers, and the credential metadata boundary. Fields such as
`token`, `password`, `secret`, `private_key`, `api_key`, and raw `value`
are forbidden inside credential routes.

## Doctor

```bash
truthrail doctor
```

Doctor first runs local validation, then checks GitHub's public API without an
Authorization header. Every configured project is probed as a public repository.

For deterministic or air-gapped validation:

```bash
truthrail doctor --offline
```

A default instance reports:

```json
{
  "credential_mode": "zero-custom-secret",
  "custom_credentials_required": 0
}
```

## Add privileged capabilities later

L2 reviewed control planes are intentionally absent from the default bootstrap.
Add them capability-by-capability when needed. Their operation surface comes from a
live reviewed `control-plane.json`; credential metadata may name a provider secret
store, but secret values remain outside Truthrail Core.

## Acceptance test

```bash
truthrail bootstrap-acceptance
```

The acceptance test creates a second five-project instance in a temporary directory,
requires zero custom credentials, validates it with offline doctor, and then runs the
core protocol conformance scenario.
