---
description: Валидировать системные или бизнес-требования Delion.
---

Провалидируй требования Delion.

Для системных требований выполни:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:validate system
```

Для бизнес-требований фичи выполни:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:validate feature FEATURE_KEY
```

Для произвольного файла выполни:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:validate file path/to/requirements.md --type auto
```

Если результат `INVALID`, покажи ошибки и не запускай workflow. Если результат `VALID`, можно продолжать к `\deli:run FEATURE_KEY`.
