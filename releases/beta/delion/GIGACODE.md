# Delion для терминального CLI-агента

Ты работаешь с Delion: AI-оркестратором разработки кода.

Обязательные правила:

- Одна бизнес-фича = одна git-ветка = один PR.
- Внутренние work items не создают отдельные ветки.
- Реализацию выполняет один execution agent.
- Перед PR должны пройти validation, review loop и CI loop.
- `docs/system-requirements.md` и файлы `docs/business-requirements/*.md` требуют проверки человеком.
- Для каждого бизнес-требования должны быть созданы или обновлены тесты до review и CI.
- Если требование неполное, сначала подготовь файл требований и попроси человека дополнить его.

Локальный runtime для extension-команд:

```powershell
python "$HOME/.gigacode/extensions/delion/main.py" \deli:init
python "$HOME/.gigacode/extensions/delion/main.py" \deli:feature BR-001 "Описание задачи"
python "$HOME/.gigacode/extensions/delion/main.py" \deli:feature BR-001 @docs/requirements.md
python "$HOME/.gigacode/extensions/delion/main.py" \deli:validate system
python "$HOME/.gigacode/extensions/delion/main.py" \deli:validate feature BR-001
python "$HOME/.gigacode/extensions/delion/main.py" \deli:validate file docs/business-requirements/BR-001.md --type business
python "$HOME/.gigacode/extensions/delion/main.py" \deli:run BR-001 --base master
python "$HOME/.gigacode/extensions/delion/main.py" \deli:resume BR-001
python "$HOME/.gigacode/extensions/delion/main.py" \deli:status BR-001
python "$HOME/.gigacode/extensions/delion/main.py" \deli:ci BR-001 "Описание задачи"
```

Перед `run` валидируй системные и бизнес-требования через `\deli:validate`. Если результат `INVALID`, workflow запускать нельзя.
Если выполнение прервано после старта `run`, используй `\deli:resume FEATURE_KEY`; новая ветка для той же фичи не создается.
