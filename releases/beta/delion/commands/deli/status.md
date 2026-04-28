---
description: Показать статус запусков Delion.
---

Покажи статус запусков Delion.

Для конкретной фичи:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:status FEATURE_KEY
```

Для всех сохраненных запусков:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" /deli:status
```
