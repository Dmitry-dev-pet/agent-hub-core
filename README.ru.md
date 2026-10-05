# Truthrail Core

[English](README.md) | **Русский**

**Один источник истины. Любой ИИ.**

> **Developer preview.** Сейчас Truthrail — это открытый протокол и эталонная
> реализация. Обычный onboarding идёт прямо через чат: локальная установка, CLI
> и постоянно включённый компьютер не требуются.

**Продолжайте пользоваться привычным AI-чатом. Сами сессии могут быть одноразовыми.**

Truthrail позволяет новой AI-сессии восстановить незавершённую работу из устойчивого
внешнего состояния, выбрать для следующего шага минимально необходимую capability и
проверить результат по живой системе, а не доверять памяти разговора.

```text
ChatGPT / другой AI-чат
          │
          ▼
      Truthrail
   ┌──────┼────────┐
   ▼      ▼        ▼
 GitHub  проверенные  эфемерные /
 live    control      machine-bound
 state   planes       executors
```

Сам Truthrail **не требует** постоянного центрального agent daemon или всегда
включённого локального компьютера. Machine-bound capabilities можно подключать только
там, где задаче действительно нужен конкретный компьютер, GPU, GUI-приложение или
локальный asset.

Базовые правила намеренно короткие:

- чат — это пользовательский интерфейс, а не источник истины;
- живое состояние целевых систем важнее cache и состояния разговора;
- устойчивая идентичность задачи переживает полностью новую сессию чата;
- привилегированные действия остаются внутри проверенных и ограниченных capability contracts;
- успешное выполнение ещё не означает завершение: требуемый результат должен быть проверен.

> Ранее проект назывался **Agent Hub Core**. Технические идентификаторы v0.1
> (`agent-hub-core`, `agent_hub_core`, `.agent-hub/` и существующие schema IDs)
> продолжают поддерживаться на время переименования.

Версия: **0.1.1**

## Базовая модель

```text
GitHub/live systems are authoritative state.
Chat is the interface.
Use the lowest sufficient execution level.
Privileged operations come from live reviewed contracts.
Executed does not mean verified.
```

Truthrail Core намеренно не является универсальным привилегированным agent runtime.
Он определяет, как найти проект, получить актуальные evidence, выбрать маршрут
выполнения, передавать работу между разными execution venues, фиксировать выполнение
и проверять требуемый результат.

## Уровни выполнения

| Уровень | Назначение |
| --- | --- |
| L0 | Чтение/анализ по авторитетному live state |
| L1 | Прямое изменение через connector/API |
| L2 | Операция через проверенный control plane |
| L3 | Эфемерный workflow/runtime |
| L4 | Coding-agent/runtime |
| L5 | Выполнение, привязанное к конкретной машине: GPU/GUI/local-only assets |

В рамках одной попытки эскалация должна быть монотонной: переходить на следующий
уровень только тогда, когда более низкий уровень не может обеспечить нужный результат
или его acceptance proof.

## Публичные демо

Два небольших демо изолированно показывают два главных свойства.

### Cross-vendor выполнение

Публичная папка [`demo/`](demo/) показывает vendor-neutral модель взаимодействия
без специального Truthrail connector:

```text
ChatGPT или Grok
  -> обычное подключение GitHub
  -> одна и та же demo policy
  -> одинаковая форма публичного issue
  -> одинаковая операция issue-create
  -> read-back verification
```

Демо не использует пользовательские секреты, workflow runner или coding-agent
runtime. Опубликованный контракт выбирает минимально достаточный уровень: одно прямое
создание GitHub issue с последующим чтением обратно и проверкой.

### Продолжение в новой сессии

[`docs/fresh-session-demo.md`](docs/fresh-session-demo.md) содержит воспроизводимый
сценарий из двух чатов: первый чат оставляет устойчивую незавершённую задачу, второй
начинается без старого transcript, обновляет авторитетное состояние GitHub, выполняет
оставшееся действие, перечитывает результат и только после этого завершает run.

Встроенный deterministic conformance harness также проверяет fresh-session recovery
без conversation memory.

## Как начать

Для обычного использования **ничего локально устанавливать не нужно**.

1. Подключите GitHub к AI-чату.
2. Дайте чату доступ к своему GitHub-аккаунту и к публичному репозиторию Truthrail Core.
3. Попросите его прочитать `skills/bootstrap-instance/SKILL.md` и выполнить onboarding GitHub-аккаунта.
4. AI сам проходит `DISCOVER -> CLASSIFY -> BUILD -> VALIDATE -> WATCH -> RECEIPT`.
5. После этого откройте полностью новый чат и проверьте восстановление из устойчивого состояния Truthrail.

Минимальный запрос пользователю достаточно сформулировать так:

```text
Подключи мой GitHub-аккаунт к Truthrail.
Используй bootstrap skill из OWNER/truthrail-core.
Не проси меня вручную перечислять репозитории или писать YAML, если эти данные можно получить из GitHub.
Не копируй значения секретов.
После onboarding проверь восстановление в новой сессии.
```

Onboarding-агент должен сам обнаружить полный набор доступных репозиториев, прочитать
живые repository evidence, не угадывать неоднозначные связи, создать или обновить
приватный Truthrail instance пользователя и сформировать onboarding receipt со статусом
`verified`, `partial` или `blocked`.

**Терминал не является частью обычного onboarding.**

Низкоуровневые CLI-команды остаются только для проверки протокола, CI, conformance
tests и обслуживания reference implementation. Это не пользовательский интерфейс
Truthrail.

## Python API

```python
from agent_hub_core import validate_document

plan = {
    "version": 1,
    "project": "demo-app",
    "selected_level": "L1",
    "reason": "A direct API mutation is sufficient.",
    "capability": "github",
    "acceptance_proof": ["updated state is visible from the authoritative API"],
}

validate_document("execution_plan", plan)
```

## Документы протокола

v0.1 включает executable JSON Schemas для:

- WorkPacket
- HandoffPacket
- ExecutionPlan
- ExecutionReceipt
- VerificationResult
- lifecycle transitions
- reviewed control-plane contracts
- onboarding receipts
- capability readiness snapshots
- capability activation receipts
- capability policy decisions

См. `docs/protocol-v0.1.md` и `examples/v0.1/`.

### Непрерывность работы v0.2

v0.2 — дополнительный continuity layer для chat-first операторов. WorkPacket становится
устойчивым корневым work order для одного результата, явно разрешённого пользователем.
Шесть continuity documents несут один стабильный `run_id`, WorkPacket фиксирует
source channel и approval policy, а lifecycle может остановиться в
`waiting_approval` до начала выполнения.

v0.1 остаётся неизменным и по-прежнему используется по умолчанию для совместимости.
Включить v0.2:

```bash
truthrail validate --schema-version 0.2 --kind work_packet work-packet.json
```

Python-клиенты могут использовать `validate_run_bundle()`, чтобы отвергать наборы
документов с разными run IDs до начала выполнения или handoff. См.
`docs/protocol-v0.2.md`.

## Проверенные control planes

Привилегированная capability указывает на живой operation contract репозитория-владельца,
а не копирует список команд в центральный registry.

```yaml
id: repo-admin
kind: reviewed_control_plane
operations_contract:
  provider: github
  repo: example-org/repo-admin
  path: control-plane.json
execution_levels: [L2]
```

Операция доступна AI router только если owning contract явно содержит
`agent_routable: true`. Operator-only или legacy operations могут оставаться в
контракте, не становясь доступными AI.

Control-plane operation также может явно описывать свою authority surface:
`credential_refs`, `execution_level`, `runtime_auth`, `execution_venue`,
`github_permissions`, `network_destinations`, `external_side_effects`,
`cost_ceiling` и `human_gate`. Truthrail capability diff сравнивает только эти
объявленные поля; он не выводит привилегии из описаний и не просит LLM судить diff.
Такие расширения, как `read -> write`, новая credential reference, новый внешний
side effect, более высокий cost ceiling в тех же единицах или удаление human gate,
фиксируются детерминированно.

Runtime admission объявляется отдельно объектом `admission` с полями `mode`
(`automatic`, `manual_approval`, `provider_interaction` или `operator_only`)
и requester policy. Это намеренно отделено от `human_gate`, который может описывать
более позднюю границу review.

Machine-readable default policy находится в `capabilities/policy-v1.yaml`. Policy
evaluation детерминирована и использует только capability diff; LLM judgment и secret
values в ней не участвуют.

## Подключение существующей инфраструктуры

Основной продуктовый сценарий — не пустой аккаунт, а уже существующий GitHub account
с репозиториями, workflows, старыми экспериментами, project families и неоднозначными
связями.

Переносимый onboarding protocol:

```text
DISCOVER -> CLASSIFY -> BUILD -> VALIDATE -> WATCH -> RECEIPT
```

Клиент должен обнаружить полный набор видимых репозиториев, сохранить каждый
репозиторий, нормализовать только связи с высокой уверенностью, фиксировать
неоднозначности вместо догадок, собрать и проверить Truthrail instance, а затем доказать
fresh-session recovery.

Machine-readable `onboarding_receipt` имеет три результата:

- `verified` — inventory полный, нерешённых элементов нет, fresh recovery прошёл;
- `partial` — состояние полное и восстанавливаемое, но остаются явно отмеченные
  semantic ambiguities;
- `blocked` — не удалось надёжно подтвердить полноту/build/validation/recovery.

Единая machine-readable точка входа — `onboarding/contract.yaml`. См. также
`docs/onboarding-v0.1.md` и `skills/bootstrap-instance/SKILL.md`.

## Постепенная активация capabilities

Базовый onboarding и включение дополнительных capabilities — разные lifecycles.

Truthrail instance может быть полностью verified, пока дополнительные capabilities
находятся в состояниях:

```text
ready     — полностью доступна
degraded  — доступна с явно описанными ограничениями
dormant   — известна и может быть активирована, но сейчас выключена
blocked   — запрошенную активацию сейчас нельзя выполнить или проверить
```

Machine-readable точка входа — `capabilities/contract.yaml`.

Если запрошенный результат требует capability не в состоянии `ready`, клиент должен
определить минимальные prerequisites, выполнить все безопасные неинтерактивные шаги,
остановиться ровно на требуемом провайдером human action, а затем проверить реальную
capability до формирования `capability_activation_receipt`.

Отсутствие необязательных capabilities не делает проверенный Truthrail onboarding
невалидным.

См. `docs/capability-activation-v0.1.md` и
`skills/activate-capability/SKILL.md`.

## Bootstrap без пользовательских секретов

Новый instance не требует PAT, API key, SSH key или другого пользовательского секрета:

```bash
truthrail init --owner example-org \
  --project example-org/public-repo-one \
  --project example-org/public-repo-two

truthrail validate-instance
truthrail doctor
```

Созданная директория `.agent-hub/` содержит:

```text
.agent-hub/
├── agent-hub.yaml
├── projects.yaml
├── capabilities.yaml
├── credentials.yaml
└── context/
```

Начальный `credentials.yaml` содержит пустой `credential_routes`. Capabilities по
умолчанию: публичное чтение GitHub (L0), необязательный ambient connected GitHub access
(L0/L1) и GitHub Actions с provider-managed `GITHUB_TOKEN` (L3).
Пользовательские секреты не создаются и не запрашиваются.

`doctor` использует публичный GitHub API без заголовка Authorization для проверки
публичных репозиториев. Для deterministic или air-gapped проверки используйте
`doctor --offline`.

Привилегированные L2 capabilities подключаются отдельно. Добавляйте такую capability
только когда существует её reviewed control plane; metadata может назвать provider
secret store, но само значение секрета остаётся вне Truthrail.

CI также запускает:

```bash
truthrail bootstrap-acceptance
```

Этот тест создаёт новый instance с пятью репозиториями во временной директории,
проверяет, что пользовательские credentials не требуются, запускает offline doctor и
завершает protocol conformance.

## Конфигурация instance

Core не зависит от конкретного пользователя. Установка задаёт собственный project
inventory, aliases, capability pointers, credential metadata и durable context.
Обезличенный пример находится в `examples/instance/`.

Значения **секретов** находятся вне протокола. В Truthrail instance могут храниться
только их names, scopes, stores и безопасные consumer routes.

## Conformance

Эталонный сценарий проверяет:

1. разрешение проекта из fresh natural-language запроса;
2. hydration из authoritative live-state fixtures;
3. L0 read routing;
4. L1 direct mutation routing;
5. L2 reviewed control-plane routing;
6. отклонение operator-only операции;
7. переход к L3 runtime только когда это действительно требуется;
8. выбор L4/L5;
9. проверку WorkPacket и HandoffPacket;
10. правило `executed != verified`;
11. проверку acceptance proof;
12. fresh-session recovery без conversation memory.

Reference adapter использует deterministic in-memory fixtures. Это conformance harness,
а не production privileged executor.

## Переносимые skills

Generic agent-facing instructions находятся в `skills/`. Они сохраняют те же правила
source precedence, live contracts, lowest-sufficient-level, credential boundaries и
verification, не завися от конкретного AI vendor.

## Что Truthrail не пытается делать

- собственная закрытая task database;
- постоянный центральный agent daemon;
- secret manager;
- универсальный remote shell;
- обязательное использование coding agent;
- замена GitHub Issues, pull requests, Actions или provider APIs.

## Лицензия

MIT.
