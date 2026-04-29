---
description: Показать статус запусков Delion.
---

Покажи статус запусков Delion.

Для конкретной фичи:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:status FEATURE_KEY
```

Если фича разбита на work items, статус показывает прогресс подзадач в виде `subtasks=DONE/TOTAL` и первую незавершенную подзадачу как `next_subtask=WT-XXX`.

Для всех сохраненных запусков:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:status
```
