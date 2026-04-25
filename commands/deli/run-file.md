---
description: Запустить workflow Delion по проверенному файлу бизнес-требований.
---

Запусти workflow Delion по готовому файлу бизнес-требований.

Выполни:

```powershell
python main.py \deli:run-file FEATURE_KEY path/to/requirements.md --base master
```

Если в файле остались TODO или unchecked пункты готовности, остановись и попроси человека дополнить требования.
