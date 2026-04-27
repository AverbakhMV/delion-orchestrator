# Delion для терминального CLI-агента

Ты работаешь с Delion: AI-оркестратором разработки кода.

## Обязательные правила

- Одна бизнес-фича = одна git-ветка = один PR.
- Внутренние work items не создают отдельные ветки.
- Реализацию выполняет один основной execution agent.
- Перед PR должны пройти validation, тесты, review loop и CI loop.
- `docs/system-requirements.md` и файлы `docs/business-requirements/*.md` требуют проверки человеком.
- Для каждого бизнес-требования должны быть созданы или обновлены тесты до review и CI.
- Если code review выдал замечания, основной агент исправляет их в той же feature branch и запускает повторный review.
- `/deli:run` выполняет полный цикл автоматически: реализация, тесты, review loop, CI, push и PR. Отдельные `/deli:test`, `/deli:review`, `/deli:ci` нужны для ручного запуска или повторения конкретной стадии.
- Если требование неполное, сначала подготовь файл требований и попроси человека дополнить его.

## Runtime-команды

Python runtime Delion выполняет локальные операции с требованиями и состоянием:

```powershell
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:init
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:feature BR-001 "Описание задачи"
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:feature BR-001 @docs/requirements.md
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:validate system
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:validate feature BR-001
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:validate file docs/business-requirements/BR-001.md --type business
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:status BR-001
python "%USERPROFILE%\.gigacode\extensions\delion\main.py" --project-root "%CD%" \deli:resume BR-001
```

## Agent-команды

Эти команды выполняются самим GigaCode через prompt, локальные инструменты и доступные MCP/tools:

```text
/deli:test BR-001
/deli:review BR-001
/deli:run BR-001
/deli:ci BR-001
```

Для `/deli:run` и `/deli:ci` реальные git/Jenkins/PR действия должны выполняться через MCP/tools GigaCode. Python runtime не выполняет git, Jenkins или PR.

Перед `run` валидируй системные и бизнес-требования через `\deli:validate`. Если результат `INVALID`, workflow запускать нельзя.
Если выполнение прервано после старта `run`, используй `\deli:resume FEATURE_KEY`; новая ветка для той же фичи не создается.
