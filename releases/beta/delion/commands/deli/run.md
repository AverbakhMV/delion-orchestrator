---
description: Запустить workflow Delion по валидированным требованиям фичи.
---

Запусти workflow Delion по валидированному файлу бизнес-требований фичи.

Перед запуском проверь:

- системные требования лежат в `docs/system-requirements.md`;
- бизнес-требования лежат в `docs/business-requirements/FEATURE_KEY.md`;
- `/deli:validate system` возвращает `VALID`;
- `/deli:validate feature FEATURE_KEY` возвращает `VALID`.

Выполни внутренний runtime:

```powershell
python main.py \deli:run FEATURE_KEY --base master
```

Соблюдай политику: одна фича = одна ветка = один PR. Не создавай отдельные ветки для тестов или внутренних work items.
