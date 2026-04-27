---
description: Инициализировать минимальную структуру Delion в текущем проекте.
---

# /deli:init — инициализация Delion

Инициализируй Delion в текущем проекте и создай стартовый файл системных требований.

## Использование

```text
/deli:init
```

## Что должно быть создано

```text
.deli/
└── state.json

docs/
├── system-requirements.md
├── business-requirements/
└── specs/
```

Минимальный смысл структуры:

- `.deli/state.json` — состояние запусков, checkpoint-ы и служебные данные Delion.
- `docs/system-requirements.md` — общий контекст проекта, правила, ограничения и команды проверки.
- `docs/business-requirements/` — бизнес-требования по фичам, например `BR-001.md`.
- `docs/specs/` — технические спецификации, если бизнес-требование нужно детализировать перед реализацией.

Не создавай сейчас `backlog/`, `tasks/`, `docs/plans/`, `docs/adr/`, `docs/architecture/`, `docs/contracts/` и `docs/templates/`. Эти разделы не используются текущим Delion workflow и могут быть добавлены позже отдельными командами.

## Алгоритм

1. Проверь, был ли Delion уже инициализирован:
   - если существует `.deli/state.json`, предупреди пользователя;
   - не перезаписывай существующие документы без явного подтверждения.

2. Выполни runtime-команду:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:init
```

3. Убедись, что в проекте появился файл:

```text
docs/system-requirements.md
```

4. Если runtime еще не создал `.deli/state.json`, создай минимальное состояние:

```json
{
  "runs": {},
  "checkpoints": {}
}
```

5. Убедись, что существуют директории:

```text
docs/business-requirements/
docs/specs/
```

6. Обнови `.gitignore` идемпотентно, если в нем еще нет Delion state:

```gitignore
.deli/
```

7. Выведи краткое подтверждение:

```text
Delion initialized

Created:
  - .deli/state.json
  - docs/system-requirements.md
  - docs/business-requirements/
  - docs/specs/

Next:
  - Проверь и дополни docs/system-requirements.md
  - Запусти /deli:validate system после ручной правки
  - Создай бизнес-требование через /deli:feature BR-001 "Описание задачи"
```

После выполнения явно скажи, что `docs/system-requirements.md` должен быть проверен и дополнен человеком перед использованием Delion workflow.
