# Delion для терминального CLI-агента

Ты работаешь с Delion: AI-оркестратором разработки кода.

Обязательные правила:

- Одна бизнес-фича = одна git-ветка = один PR.
- Внутренние work items не создают отдельные ветки.
- Реализацию выполняет один execution agent.
- Перед PR должны пройти validation, review loop и CI loop.
- `docs/delion/system-requirements.md` и файлы `docs/delion/business-requirements/*.md` требуют проверки человеком.
- Если требование неполное, сначала подготовь файл требований и попроси человека дополнить его.

Локальный runtime для extension-команд:

```powershell
python main.py \deli:init
python main.py \deli:feature BR-001 "Описание задачи"
python main.py \deli:feature BR-001 @docs/requirements.md
python main.py \deli:validate system
python main.py \deli:validate feature BR-001
python main.py \deli:validate file docs/delion/business-requirements/BR-001.md --type business
python main.py \deli:run-file BR-001 docs/delion/business-requirements/BR-001.md --base master
python main.py \deli:resume BR-001
python main.py \deli:status BR-001
python main.py \deli:ci BR-001 "Описание задачи"
```

Перед `run-file` валидируй системные и бизнес-требования через `\deli:validate`. Если результат `INVALID`, workflow запускать нельзя.
Если выполнение прервано после старта `run-file`, используй `\deli:resume FEATURE_KEY`; новая ветка для той же фичи не создается.
