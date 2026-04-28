# Delion для GigaCode

Ты работаешь с Delion: оркестратором разработки кода по системным и бизнес-требованиям.

Всегда используй команды Delion только со слэшем `/`: `/deli:*`. Не предлагай и не используй вариант с обратным слэшем.

## Команды Delion

GigaCode должен предлагать и выполнять эти команды:

```text
/deli:init
/deli:feature FEATURE_KEY "Описание задачи"
/deli:feature FEATURE_KEY @path/to/requirements.md
/deli:validate system
/deli:validate feature FEATURE_KEY
/deli:validate file path/to/requirements.md --type auto
/deli:test FEATURE_KEY
/deli:review FEATURE_KEY
/deli:run FEATURE_KEY
/deli:resume FEATURE_KEY
/deli:status
/deli:status FEATURE_KEY
/deli:ci FEATURE_KEY
```

### /deli:init

Инициализирует Delion в текущем проекте.

Создает минимальную структуру:

```text
.deli/state.json
docs/system-requirements.md
docs/business-requirements/
docs/specs/
```

После выполнения человек должен проверить и дополнить `docs/system-requirements.md`.

### /deli:feature

Создает черновик бизнес-требования для одной фичи.

Примеры:

```text
/deli:feature BR-001 "Добавить экспорт отчета в CSV"
/deli:feature BR-001 @docs/input/feature-request.md
```

Результат:

```text
docs/business-requirements/BR-001.md
```

Файл должен быть проверен человеком до запуска реализации.

### /deli:validate

Проверяет системные или бизнес-требования.

Примеры:

```text
/deli:validate system
/deli:validate feature BR-001
/deli:validate file docs/business-requirements/BR-001.md --type business
```

Если результат `INVALID`, workflow запускать нельзя. Покажи ошибки и попроси исправить требования.

### /deli:test

Создает или обновляет тесты по бизнес-требованию.

Пример:

```text
/deli:test BR-001
```

Тесты должны покрывать must-have требования, критерии готовности, edge cases и требования к тестам из `docs/business-requirements/BR-001.md`. На этой стадии тесты только создаются или обновляются, запускать их не нужно.

### /deli:review

Проводит code review изменений по бизнес-требованию.

Пример:

```text
/deli:review BR-001
```

Если review нашел замечания, основной агент исправляет их в той же feature branch, обновляет тесты при изменении поведения и повторяет review.

### /deli:run

Запускает полный workflow фичи.

Пример:

```text
/deli:run BR-001
```

`/deli:run` выполняет полный цикл: validation, feature branch, реализация, создание или обновление тестов, review loop, push, PR, merge и post-merge CI loop. Пользователь не должен отдельно запускать `/deli:test`, `/deli:review` и `/deli:ci`, если уже запущен `/deli:run`.

Локальные тесты не запускаются. Code review должен быть принят до push и PR. Jenkins запускается только после merge PR в основную ветку.

Git branch, push, Jenkins и PR выполняются GigaCode через доступные MCP/tools. Python runtime Delion не выполняет git, Jenkins или PR.

### /deli:resume

Продолжает workflow с последнего checkpoint.

Пример:

```text
/deli:resume BR-001
```

Если выполнение было прервано после старта `/deli:run`, используй `/deli:resume FEATURE_KEY`. Новая ветка для той же фичи не создается.

### /deli:status

Показывает сохраненный статус запусков Delion.

Примеры:

```text
/deli:status
/deli:status BR-001
```

### /deli:ci

Запускает post-merge Jenkins CI loop для фичи через MCP/tools GigaCode.

Пример:

```text
/deli:ci BR-001
```

После падения post-merge CI основной агент исправляет проблему по процессу проекта, затем повторяет полный цикл: тестовые файлы, review, push, PR, merge и только потом CI.

## Обязательные правила

- Одна бизнес-фича = одна git-ветка = один PR.
- Внутренние work items не создают отдельные ветки.
- Реализацию выполняет один основной execution agent.
- Перед push и PR должны пройти validation, создание или обновление тестов и review loop.
- `docs/system-requirements.md` и `docs/business-requirements/*.md` требуют проверки человеком.
- Для каждого бизнес-требования должны быть созданы или обновлены тесты до review; запускать локальные тесты не нужно.
- Если требование неполное, сначала подготовь файл требований и попроси человека дополнить его.
- Если code review или CI нашли замечания, исправляй их в той же feature branch.
- Code review должен быть принят до push и PR.
- Jenkins CI запускается после merge PR в основную ветку.
- Не создавай PR до успешного review loop.

## Runtime-команды

Когда prompt-команде нужно вызвать Python runtime Delion, используй `/deli:*`:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:init
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:feature BR-001 "Описание задачи"
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:feature BR-001 @docs/requirements.md
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:validate system
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:validate feature BR-001
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:validate file docs/business-requirements/BR-001.md --type business
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:status BR-001
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:resume BR-001
```

Python runtime ограничен локальными операциями с документами и состоянием: `init`, `feature`, `validate`, `mark`, `resume`, `status`.

## Workflow

```text
system requirements
  -> business requirements
  -> validation
  -> one feature branch
  -> implementation
  -> create or update tests
  -> review loop
  -> push
  -> PR
  -> merge
  -> post-merge CI loop
```

Ключевые компоненты:

- prompt-команды из `commands/deli/` управляют стадиями workflow;
- Python runtime создает и валидирует документы, а также ведет checkpoint-и;
- GigaCode MCP/tools выполняют реальные git, Jenkins и PR действия;
- checkpoint-и хранятся в `.deli/state.json`.
