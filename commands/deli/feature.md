---
description: Сформировать бизнес-требования Delion по задаче или файлу.
---

Сформируй бизнес-требования Delion по задаче пользователя.

Если пользователь передал путь к файлу, выполни:

```powershell
python main.py \deli:feature FEATURE_KEY @path/to/file.md
```

Если пользователь передал текст задачи, выполни:

```powershell
python main.py \deli:feature FEATURE_KEY "Текст задачи"
```

После выполнения покажи путь к файлу в `docs/delion/business-requirements/` и явно попроси человека проверить и дополнить бизнес-цель, пользователей, сценарии и acceptance criteria.
