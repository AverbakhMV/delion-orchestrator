---
description: Запустить CI loop Delion для фичи.
---

Запусти CI loop Delion для фичи.

Выполни:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:ci FEATURE_KEY "Текст задачи"
```

Если CI упал, покажи краткий статус и предложи вернуть ошибку execution agent для исправления в той же feature-ветке.
