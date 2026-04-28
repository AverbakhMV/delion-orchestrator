---
description: Запустить agent-orchestrated workflow Delion по валидированным требованиям фичи.
---

# /deli:run — workflow фичи через GigaCode MCP/tools

Запусти workflow Delion по валидированному файлу бизнес-требований `docs/business-requirements/FEATURE_KEY.md`.

`/deli:run` выполняет полный цикл автоматически. Пользователь не должен отдельно запускать `/deli:test`, `/deli:review` и `/deli:ci`, если он уже запустил `/deli:run`.

Важно: стадия тестов только создает или обновляет тестовые файлы. Локальные тесты не запускаются. Code review обязательно выполняется до push и PR. Jenkins запускается только после merge PR в основную ветку.

Отдельные команды стадий нужны только для ручного контроля, повторного запуска конкретного этапа или отладки.

## Важно

Python runtime Delion используется только для локальных операций: `init`, `feature`, `validate`, `mark`, `status` и read-only `resume`. Реальные git/Jenkins/PR действия выполняй через доступные MCP/tools GigaCode.

Не используй in-memory runtime как доказательство реального push, Jenkins build или PR.

## Перед запуском

Проверь:

- `docs/system-requirements.md` существует;
- `docs/business-requirements/FEATURE_KEY.md` существует;
- `/deli:validate system` возвращает `VALID`;
- `/deli:validate feature FEATURE_KEY` возвращает `VALID`;
- текущий git workspace не содержит unrelated изменений, которые нельзя включать в эту фичу.

Команды валидации:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:validate system
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:validate feature FEATURE_KEY
```

## Алгоритм

1. Определи base branch.

   Если пользователь передал `--base BRANCH`, используй его.

   Если `--base` не передан, определи base branch автоматически через GigaCode git/SCM MCP/tools:
   - сначала default branch remote;
   - затем `main`, если ветка существует;
   - затем `master`, если ветка существует.

   Если определить base branch нельзя, задай пользователю один вопрос:

```text
Не удалось определить базовую ветку. От какой ветки создавать feature branch?
```

2. Через GigaCode git MCP/tools создай или переключись на одну feature branch для `FEATURE_KEY`.

   Правило ветки:

```text
ai/feature_key-short-slug
```

   После создания или переключения ветки зафиксируй checkpoint:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:mark FEATURE_KEY branch_created --branch "BRANCH_NAME" --base "BASE_BRANCH"
```

3. Реализуй production-код одним основным execution agent.

   После реализации production-кода зафиксируй checkpoint:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:mark FEATURE_KEY implemented --branch "BRANCH_NAME"
```

4. Создай или обнови тесты как встроенную стадию workflow:

```text
/deli:test FEATURE_KEY
```

Не спрашивай пользователя, запускать ли тесты: это обязательная стадия `/deli:run`, но тесты не нужно выполнять. Нужно только создать или обновить тестовые файлы.

Выполни инструкции из `commands/deli/test.md` как встроенную стадию. Не ограничивайся выводом строки `/deli:test FEATURE_KEY`.

5. Проведи code review как встроенную стадию workflow:

```text
/deli:review FEATURE_KEY
```

Если review вернул замечания, основной агент исправляет их в той же feature branch, обновляет тесты при изменении поведения и повторяет `/deli:review FEATURE_KEY`. Не делай push и не создавай PR, пока review loop не принят.

Выполни инструкции из `commands/deli/review.md` как встроенную стадию. Не ограничивайся выводом строки `/deli:review FEATURE_KEY`.

6. Только после принятого review через GigaCode git/SCM MCP/tools:
   - push feature branch в удаленный репозиторий;
   - создай один PR в определенную base branch;
   - приложи summary, созданные или обновленные тесты и review result.

   После push и PR зафиксируй checkpoints:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:mark FEATURE_KEY branch_pushed --branch "BRANCH_NAME"
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:mark FEATURE_KEY pr_created --branch "BRANCH_NAME" --pr-url "PR_URL"
```

7. Дождись merge PR в основную ветку или выполни merge через доступные GigaCode SCM/MCP tools, если это разрешено процессом проекта.

   После merge зафиксируй checkpoint:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:mark FEATURE_KEY pr_merged --branch "BRANCH_NAME" --pr-url "PR_URL"
```

8. Только после merge PR запусти Jenkins CI как встроенную стадию workflow:

```text
/deli:ci FEATURE_KEY
```

CI должен запускаться через Jenkins MCP/tools GigaCode из удаленного репозитория после merge в основную ветку, а не из локальной feature branch. Не спрашивай пользователя, запускать ли CI, если validation, создание тестов, review, push, PR и merge уже прошли.

Выполни инструкции из `commands/deli/ci.md` как встроенную стадию. Не ограничивайся выводом строки `/deli:ci FEATURE_KEY`.

## Запрещено

- Не создавай отдельные ветки для тестов, review fixes или внутренних work items.
- Не запускай локальные тесты: Delion на этой стадии только создает или обновляет тестовые файлы.
- Не делай push и не создавай PR до принятого code review.
- Не запускай Jenkins CI до push, PR и merge в основную ветку.
- Не создавай PR до успешных validation, создания тестов и review.
- Не используй fake URL из runtime как ссылку на реальный PR или Jenkins build.
- Не включай unrelated изменения без явного подтверждения пользователя.
