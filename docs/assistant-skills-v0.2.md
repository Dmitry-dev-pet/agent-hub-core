# Named assistant skills in Truthrail v0.2

Truthrail separates **identity**, **skills**, and **authority**.

- An assistant profile gives the chat-facing assistant a user-selected name and role.
- A skill describes how the assistant should handle a class of task.
- A capability or reviewed control plane defines what the assistant is actually allowed to do.

A skill therefore never grants permission by itself.

## Default assistant bundle

The portable default bundle is [`skills/default-assistant.yaml`](../skills/default-assistant.yaml).

A newly named assistant gets four everyday skills:

| Skill | What it enables |
| --- | --- |
| `rebuild-context` | Resume a project or a durable run from authoritative state instead of relying on chat memory. |
| `recent-activity` | Answer “what changed?” from live repository/workflow evidence. |
| `capability-route` | Select the narrowest safe tool/control plane without exposing credential values. |
| `orchestrate-action` | Carry out a user-authorized action and verify the outcome separately from execution. |

Two additional skills are not ordinary background powers:

- `bootstrap-instance` is a setup/onboarding skill;
- `activate-capability` is optional and is used only when the user asks to enable a capability that is not ready.

## Example

A private Truthrail instance may keep:

```yaml
name: Nova
role: personal_ai_assistant

skills:
  bundle: truthrail-default-assistant
  enabled:
    - rebuild-context
    - recent-activity
    - capability-route
    - orchestrate-action
```

The same bundle works for Alfred, Nova, Ada, or any other name.

## Fresh-session behavior

When a new chat locates the private Truthrail instance, it should:

1. recover the assistant profile;
2. resolve the configured skill bundle against the declared Truthrail Core source;
3. use the appropriate skill only when the user's request matches it;
4. refresh authoritative references before freshness-sensitive claims or resumed actions;
5. apply the instance's capability/approval contracts before any mutation.

If a skill cannot be resolved, the assistant should report that the behavior contract is unavailable rather than inventing it.

## Safety boundary

Skill selection must not:

- add GitHub write permissions;
- bypass a reviewed control plane;
- reveal or request credential values when a safe credential route exists;
- turn an advisory watcher signal into automatic mutation;
- treat `executed` as `verified`.

Identity and skills are portable configuration. Authority remains explicit and separately governed.
