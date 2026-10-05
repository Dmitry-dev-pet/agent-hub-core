# Truthrail Core

**English** | [Русский](README.ru.md)

**One source of truth. Any AI.**

Truthrail lets you keep using ChatGPT as the interface while the durable state of your
work lives outside the chat.

A chat can end. A new chat can continue.

```text
ChatGPT / another AI chat
          │
          ▼
      Truthrail
          │
   ┌──────┼─────────┐
   ▼      ▼         ▼
 GitHub   control   optional
 live     planes    executors
 state
```

You do **not** need to install Truthrail locally for normal use, and you do not need an
always-on Mac or PC. Truthrail is currently a developer preview.

## Start here

Connect GitHub to your AI chat, then choose the case that matches your account.

### 1. You already have GitHub repositories

Send this:

```text
Onboard my GitHub account with Truthrail.
Read the bootstrap skill in skills/bootstrap-instance/SKILL.md from the Truthrail Core repository I shared.
Discover my repositories yourself. Do not ask me to list them or write YAML if GitHub already has the information.
Do not copy secret values.
After setup, verify that a completely fresh chat can recover the same Truthrail state.
```

Truthrail should then:

1. discover the repositories visible in your GitHub account;
2. read enough live evidence to understand the projects and obvious relationships;
3. create or update one private Truthrail instance for your account;
4. record project routing, durable context, capabilities, and credential metadata
   **without secret values**;
5. validate the result;
6. record unresolved ambiguities instead of guessing;
7. verify recovery from a completely new chat.

You should not have to maintain repository lists or configuration files by hand.

### 2. Your GitHub account is new and empty

Send this instead:

```text
My GitHub account is new and has no project repositories.
Set up a greenfield Truthrail instance for me.
Do not invent projects.
Create one private Truthrail repository with an empty project inventory, baseline GitHub capabilities, and no secret values.
Validate it and verify from a completely fresh chat that the empty Truthrail state can be recovered.
```

In the greenfield case Truthrail starts with:

- one private Truthrail repository;
- an empty project inventory;
- baseline GitHub capabilities;
- no copied credential values;
- no invented project context.

When you create your first real repository later, ask:

```text
Refresh Truthrail and onboard anything new in my GitHub account.
```

Truthrail should update the existing instance rather than create a second one.

## What happens after onboarding?

You keep working in normal chat.

For example:

```text
Alfred, continue.
```

A fresh session can use Truthrail to find the current durable run, refresh the live
GitHub/control-plane state, continue the work, verify the result, and close the run only
after verification.

Truthrail does not treat old conversation text as authoritative current state.

## What Truthrail stores

Truthrail may keep:

- project routing and aliases;
- durable goals, decisions, and constraints;
- capability metadata;
- credential **names/scopes/routes**, never secret values;
- durable work/run state;
- references to authoritative live systems.

Truthrail should re-read freshness-sensitive facts such as branches, PRs, Actions,
deployments, and runtime status from the live system.

## What Truthrail is not

Truthrail is not:

- a replacement chat application;
- a permanent central agent daemon;
- a secret manager;
- a universal remote shell;
- a requirement to keep your computer online.

Machine-bound execution can still be attached when a task genuinely needs a specific
computer, GPU, GUI application, or local-only asset.

## Public demos

- [Fresh-session continuity demo](docs/fresh-session-demo.md) — start work in one
  chat and complete it from another without passing the old transcript.
- [Cross-vendor GitHub demo](demo/) — different AI chats follow the same durable
  GitHub-native policy and verify the same operation shape.

## Technical reference

The main user path is chat-first. The CLI and Python API are reference/CI tooling, not
the onboarding interface.

- [Onboarding protocol](docs/onboarding-v0.1.md)
- [Work continuity v0.2](docs/protocol-v0.2.md)
- [Protocol v0.1](docs/protocol-v0.1.md)
- [Capability activation](docs/capability-activation-v0.1.md)
- [Security](SECURITY.md)
- [Portable bootstrap skill](skills/bootstrap-instance/SKILL.md)

> Formerly **Agent Hub Core**. Legacy v0.1 identifiers such as
> `agent-hub-core`, `agent_hub_core`, and `.agent-hub/` remain supported for
> compatibility.

## License

MIT.
