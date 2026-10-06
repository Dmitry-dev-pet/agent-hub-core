# Truthrail Core

**English** | [Русский](README.ru.md)

**One source of truth. Any AI.**

Truthrail lets you keep using ChatGPT as the interface while the durable state of your
work lives outside the chat.

A chat can end. A new chat can continue.

You do **not** need to install Truthrail locally, keep a Mac/PC online, or give an AI
write access to your whole GitHub account just to try it.

## Start with minimal access

Truthrail onboarding uses a trust ladder:

### 1. Explore — read only

Start with no write access.

You can either:

- share a public repository URL; or
- when your GitHub connection supports repository selection/read-only access, expose
  only the repositories you want Truthrail to inspect.

Ask:

```text
Explore these GitHub repositories with Truthrail.
Read only. Do not create, edit, or delete anything.
Show me what projects and relationships you can infer, and clearly mark anything uncertain.
```

At this stage Truthrail should only read and explain what it sees.

### 2. Connect — one private Truthrail repository

If the result looks right, Truthrail needs one private repository for durable
routing/context.

The preferred least-privilege path is to create your own private `truthrail`
repository from a small Truthrail starter template when that option is available.
If template creation is unavailable, create an empty private repository manually.
Then grant the AI write access **only to that repository**.

A fork of public `truthrail-core` is for developing the core, not for storing your
private Truthrail instance. Project repositories can remain read-only and can be added
gradually.

Ask:

```text
Create or update my private Truthrail instance from the repositories I have approved.
Do not request write access to my project repositories.
Do not copy secret values.
Verify that a completely fresh chat can recover the same Truthrail state.
```

### 3. Meet your assistant

Truthrail is the durable state/protocol layer. Your assistant is the chat-facing identity
that uses it.

Choose any name you like. `Alfred` is only the name used by this project's reference
instance; your assistant can be `Nova`, `Friday`, `Ada`, or something else entirely.

Ask:

```text
My assistant's name is Nova.
Use my private Truthrail repository as durable state.
Keep project repositories read-only unless I explicitly approve a narrower write capability.
Record the assistant profile, then verify that a fresh chat can recover both the Truthrail state and the assistant name.
```

The name is not a permission boundary. Renaming the assistant never grants or removes
capabilities.

A new assistant also receives the portable default skill bundle:

- resume/rebuild context;
- reconstruct recent activity;
- route to the narrowest safe capability;
- execute an authorized action and verify it separately.

Onboarding and capability activation remain separate setup/optional skills. See
[assistant profile example](examples/assistant-profile.yaml) and
[named assistant skills](docs/assistant-skills-v0.2.md).

### 4. Operate — optional, later

Only when you want your assistant/Truthrail to perform actions, add write-capable permissions
or control planes **for the specific repositories/services that need them**.

Examples:

- allow issues/PRs in one project;
- enable one deployment control plane;
- attach a machine-bound executor for Blender/GPU work.

Full-account write access is not a Truthrail requirement.

> Exact repository-selection and permission controls depend on the GitHub connection
> or AI host you use. If fine-grained selection is unavailable, you can still start
> with public repositories before connecting private ones.

## Two onboarding cases

### Existing GitHub repositories

After the Explore step, Truthrail discovers and records only the repositories in the
scope you approved. It should not claim visibility into repositories outside that scope.

It then:

1. reads enough live evidence to understand projects and obvious relationships;
2. records ambiguity instead of guessing;
3. creates or updates one private Truthrail instance;
4. stores routing, durable context, capabilities, and credential metadata without
   secret values;
5. validates the result;
6. verifies recovery from a completely new chat.

### New and empty GitHub account

There are no project repositories to inspect. After you allow creation of one private
Truthrail repository, ask:

```text
My GitHub account is new and has no project repositories.
Set up a greenfield Truthrail instance.
Do not invent projects.
Create one private Truthrail repository with an empty project inventory, baseline GitHub capabilities, and no secret values.
Verify from a completely fresh chat that the empty Truthrail state can be recovered.
```

Zero projects is a valid state.

When the first real repository appears later:

```text
Refresh Truthrail and onboard anything new in the GitHub scope I have approved.
```

Truthrail should update the existing instance rather than create a second one.

## After onboarding

You keep working in normal chat.

For example:

```text
Nova, continue.
```

A fresh session can find the current durable run, refresh live GitHub/control-plane
state, continue the work, verify the result, and close the run only after verification.

Truthrail deliberately separates execution from verification:

```text
executing -> executed -> verifying -> verified
```

`executed` means the executor finished the operation. It is not success by itself.
`verified` is the terminal lifecycle state reached only after authoritative evidence
passes verification. A durable run may also keep a compact resume checkpoint, while
optional Truthrail Watch advisories can flag stale lifecycle metadata without changing it
automatically.

## What Truthrail stores

Truthrail may keep:

- project routing and aliases;
- durable goals, decisions, and constraints;
- capability metadata;
- credential names/scopes/routes, never secret values;
- durable work/run state;
- references to authoritative live systems.

Freshness-sensitive facts such as branches, PRs, Actions, deployments, and runtime
status are re-read from the live system.

## What Truthrail is not

Truthrail is not:

- a replacement chat application;
- a permanent central agent daemon;
- a secret manager;
- a universal remote shell;
- a requirement to keep your computer online;
- a requirement to grant account-wide GitHub write access.

## Public demos

- [Fresh-session continuity demo](docs/fresh-session-demo.md)
- [Cross-vendor GitHub demo](demo/)

## Technical reference

- [Onboarding protocol](docs/onboarding-v0.1.md)
- [Work continuity v0.2](docs/protocol-v0.2.md)
- [Run ledger v0.2](docs/run-ledger-v0.2.md)
- [Truthrail Watch semantics v0.2](docs/watch-v0.2.md)
- [Named assistant skills v0.2](docs/assistant-skills-v0.2.md)
- [Security](SECURITY.md)
- [Bootstrap skill](skills/bootstrap-instance/SKILL.md)

> Formerly **Agent Hub Core**. Legacy v0.1 identifiers such as
> `agent-hub-core`, `agent_hub_core`, and `.agent-hub/` remain supported for compatibility.

## License

MIT.
