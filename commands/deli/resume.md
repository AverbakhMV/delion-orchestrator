---
description: Продолжить workflow Delion с последнего checkpoint.
---

Продолжи workflow Delion с последнего сохраненного checkpoint.

Выполни:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:resume FEATURE_KEY
```

Перед продолжением покажи сохраненные шаги из `\deli:status FEATURE_KEY`. Не создавай новую ветку для той же фичи и не пропускай шаг `tests_created`.
