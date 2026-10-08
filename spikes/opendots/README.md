# OpenDots / Truthrail spike

This spike tests a narrow integration boundary between an OpenDots-style conversational
agent and Truthrail Core.

The goal is **not** to make OpenDots a privileged executor. The goal is to let a Dot ask
Truthrail for authoritative state, request a reviewed route, and surface a human approval
gate while execution remains owned by the reviewed control plane.

## Boundary

```text
OpenDots / AG-UI conversation
        |
        | server tools
        v
truthrail_status
truthrail_dispatch
truthrail_approve
        |
        v
Truthrail reference routing + admission policy
        |
        +-- L0 live state
        +-- reviewed control-plane contract
        +-- manual approval gate
        |
        v
approved handoff only
(no privileged execution in this spike)
```

The provider intentionally has no generic shell, no credential API, and no direct
provider mutation. Every result carries `executed: false`.

## Files

- `agent_hub_core/tool_provider.py` — portable execution-free tool provider.
- `provider_server.py` — tiny local HTTP boundary using only the Python standard
  library.
- `truthrail-tools.ts` — OpenDots-compatible `defineTool(...)` wrappers.
- `demo-config.example.json` — sanitized deterministic fixture.
- `tests/test_tool_provider.py` — provider policy tests.
- `tests/test_opendots_http_spike.py` — STATUS -> DISPATCH -> APPROVE over real HTTP.

## Run the provider

From the repository root:

```bash
python spikes/opendots/provider_server.py \
  --config spikes/opendots/demo-config.example.json
```

It binds to `127.0.0.1:8766` by default.

Inspect tools:

```bash
curl http://127.0.0.1:8766/v1/tools
```

Read status:

```bash
curl -s http://127.0.0.1:8766/v1/call \
  -H 'content-type: application/json' \
  -d '{
    "name":"truthrail_status",
    "arguments":{"project":"demo"}
  }'
```

Request a privileged route:

```bash
curl -s http://127.0.0.1:8766/v1/call \
  -H 'content-type: application/json' \
  -d '{
    "name":"truthrail_dispatch",
    "arguments":{
      "project":"demo",
      "requirement":"privileged_mutation",
      "capability":"repo-admin",
      "operation":"deploy",
      "acceptance_proof":["provider state is visible"]
    }
  }'
```

The sanitized fixture returns `approval_required`. Pass its `approval_id` to
`truthrail_approve` with `approve: true` or `false`.

Approval changes the request to `approved_for_handoff`; it still does not execute it.

## OpenDots hook

OpenDots already builds server-side tools with `defineTool` and injects them into the
Dot agent's `serverTools` list. The included `truthrail-tools.ts` follows the same
shape.

For a throwaway OpenDots checkout, copy the adapter next to
`src/server/tanstack-tools.ts`, then in `src/server/dot-agent.ts`:

```ts
import { truthrailTools } from './truthrail-tools.js';

// ...

const serverTools = [
  ...tools,
  ...pageTools(pages),
  ...(computer.configured
    ? computerTools(computer, dot.id, check, controller.signal)
    : []),
  ...truthrailTools(),
];
```

Optional environment variables:

```text
TRUTHRAIL_PROVIDER_URL=http://127.0.0.1:8766
TRUTHRAIL_PROVIDER_TOKEN=<owner-generated local token>
```

A token is optional on loopback. `provider_server.py` refuses a non-loopback bind
unless `TRUTHRAIL_PROVIDER_TOKEN` is set.

## What this proves

This spike is successful when CI proves the following sequence:

1. OpenDots-compatible tool definitions are bounded to STATUS, DISPATCH, APPROVE.
2. STATUS returns authoritative live-state input supplied to Truthrail.
3. DISPATCH selects the lowest sufficient level and evaluates the reviewed operation
   admission contract.
4. A `manual_approval` operation stops at `REQUIRE_HUMAN`.
5. APPROVE releases only a handoff and never performs the privileged action.
6. Operator-only operations fail closed.

## Deliberately out of scope

- executing GitHub, Vercel, VPS, or other privileged operations;
- copying private Truthrail instance data into this public repository;
- secret transport;
- replacing Truthrail's reviewed control planes;
- changing the v0.1 protocol schemas;
- forking or vendoring OpenDots.

If this boundary holds, the next spike can wire `approved_for_handoff` to one existing
reviewed control plane and verify the real external outcome separately.
