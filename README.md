# Delion

Delion - extension для GigaCode/Qwen-подобных CLI-агентов, который оркестрирует разработку кода по требованиям.

Статус: beta-версия.

Основной режим работы - команды агента:

```text
/deli:init
/deli:feature
/deli:validate
/deli:run
/deli:resume
/deli:status
/deli:ci
```

Базовая политика:

- одна фича = одна git-ветка = один PR;
- один execution agent выполняет реализацию;
- тесты создаются или обновляются для всех бизнес-требований до review и CI;
- внутренние work items не создают отдельные ветки;
- PR создается только после review loop и CI loop;
- системные и бизнес-требования валидирует человек.

## Установка GigaCode/Qwen Extension

Файлы extension:

```text
gigacode-extnsion.json
GIGACODE.md
commands/deli/*.md
main.py
orchestrator/*.py
```

Подключение зависит от конкретного CLI-агента. Для Qwen Code-подобного механизма расширений Delion должен подключаться как локальная extension-директория или через marketplace-запись, указывающую на этот репозиторий.

После подключения агент должен читать `GIGACODE.md`, видеть команды из `commands/deli/` и вызывать Delion через `/deli:*`.

### GigaCode CLI

Корпоративный fork Qwen:

```bash
# 1. Скачайте beta-релиз Delion extension
curl -L -o /tmp/delion-gigacode-beta.zip \
  https://github.com/AverbakhMV/delion-orchestrator/raw/main/releases/beta/delion-gigacode.zip

# 2. Распакуйте beta-релиз в директорию расширений GigaCode
mkdir -p ~/.gigacode/extensions
unzip -o /tmp/delion-gigacode-beta.zip -d ~/.gigacode/extensions

# 3. Запустите GigaCode и инициализируйте структуру Delion внутри проекта
gigacode
/deli:init
```

Если репозиторий уже скачан и вы находитесь в его корне, можно установить локальный beta-архив:

```bash
mkdir -p ~/.gigacode/extensions
unzip -o releases/beta/delion-gigacode.zip -d ~/.gigacode/extensions
gigacode
/deli:init
```

## Команды

```text
/deli:init
```

Анализирует проект и создает:

```text
docs/system-requirements.md
```

```text
/deli:feature BR-001 "Добавить экспорт отчета в CSV"
/deli:feature BR-001 @docs/input/business-requirements.md
```

Создает черновик бизнес-требований:

```text
docs/business-requirements/BR-001.md
```

```text
/deli:validate system
/deli:validate feature BR-001
/deli:validate file docs/business-requirements/BR-001.md --type business
```

Валидирует системные или бизнес-требования. Delion считает файл неготовым, если в нем остались `TODO`, unchecked-пункты, статус ручной валидации или отсутствуют обязательные секции.

```text
/deli:run BR-001 --base master
```

Запускает workflow по `docs/business-requirements/BR-001.md` только после валидации системных и бизнес-требований.

```text
/deli:resume BR-001
```

Продолжает workflow с последнего checkpoint. Новая ветка для той же фичи не создается.

```text
/deli:status BR-001
```

Показывает run status и checkpoint.

```text
/deli:ci BR-001 "Описание задачи"
```

Запускает CI loop для фичи.

## Workflow

```text
system requirements
  -> business requirements
  -> validation
  -> plan
  -> one feature branch
  -> one execution agent
  -> tests for all business requirements
  -> review loop
  -> CI loop
  -> PR to master/main
```

Ключевые компоненты:

- `PlannerAgent` составляет план реализации.
- `DeveloperAgent` представляет один execution agent.
- `TestAgent` добавляет или обновляет тесты под все бизнес-требования и acceptance criteria.
- `ReviewerAgent` проверяет изменения до PR.
- `WorkflowEngine` управляет feature workflow.
- CI loop выполняет bounded retry-проверку.

## Resume

Delion сохраняет checkpoint в:

```text
.deli/state.json
```

Checkpoint фиксирует завершенные шаги:

- `branch_created`
- `implemented`
- `tests_created`
- `reviewed`
- `ci_passed`
- `branch_pushed`
- `pr_created`

Если выполнение прервано, агент должен выполнить:

```text
/deli:status BR-001
/deli:resume BR-001
```

## Claude Code Plugin

Claude Code - дополнительный режим, не основной.

Файлы:

```text
.claude-plugin/plugin.json
.claude-plugin/marketplace.json
commands/deli/*.md
```

Локальная установка:

```text
/plugin marketplace add ./delion
/plugin install delion@delion-marketplace
```

После установки ожидаются те же команды:

```text
/deli:init
/deli:feature
/deli:validate
/deli:run
/deli:resume
/deli:status
/deli:ci
```

## Внутренний Runtime

Внутри команд Delion сейчас используется Python runtime и in-memory адаптеры:

- `InMemoryScmClient`
- `InMemoryCIRunner`

Для production-поведения их нужно заменить на реальные адаптеры GitHub/GitLab и Jenkins. Runtime-команды предназначены для реализации extension-команд и отладки, а не как основной пользовательский интерфейс.
