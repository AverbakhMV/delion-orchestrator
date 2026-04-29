# Delion

Delion - extension для GigaCode/Qwen-подобных CLI-агентов, который оркестрирует разработку кода по требованиям.

Статус: beta-версия.

Основной режим работы - команды агента:

```text
/deli:init
/deli:feature
/deli:validate
/deli:test
/deli:review
/deli:run
/deli:resume
/deli:status
/deli:subtask
/deli:ci
```

Базовая политика:

- одна фича = одна git-ветка = один PR;
- один execution agent выполняет реализацию;
- тесты создаются или обновляются для всех бизнес-требований до review, но локально не запускаются;
- внутренние work items не создают отдельные ветки;
- большие фичи разбиваются на work items, состояние каждого work item сохраняется в `.deli/state.json` через `/deli:subtask`;
- code review выполняется до push и PR;
- PR создается только после review loop;
- Jenkins CI запускается после merge PR в основную ветку;
- системные и бизнес-требования валидирует человек;
- в корне целевого проекта ожидается файл `AGENTS.md`; при создании бизнес-требований агент должен прочитать его и учитывать описанные там правила проекта.

## Установка GigaCode/Qwen Extension

Файлы extension:

```text
gigacode-extension.json
GIGACODE.md
commands/deli/*.md
main.py
orchestrator/*.py
```

Подключение зависит от конкретного CLI-агента. Для Qwen Code-подобного механизма расширений Delion должен подключаться как локальная extension-директория или через marketplace-запись, указывающую на этот репозиторий.

После подключения агент должен читать `GIGACODE.md`, видеть команды из `commands/deli/` и вызывать Delion через `/deli:*`.

В целевом проекте, где запускается Delion, ожидается корневой файл `AGENTS.md` с проектным prompt-контекстом. `/deli:feature` должен читать этот файл перед созданием `docs/business-requirements/BR-XXX.md`.

### GigaCode CLI

Корпоративный fork Qwen:

```bash
# 1. Скачайте beta-релиз Delion extension
curl -L -o /tmp/delion-gigacode-beta.zip \
  https://github.com/AverbakhMV/delion-orchestrator/raw/main/releases/beta/delion-gigacode.zip

# 2. Распакуйте beta-релиз в директорию расширений GigaCode
mkdir -p ~/.gigacode/extensions
rm -rf ~/.gigacode/extensions/delion
unzip -o /tmp/delion-gigacode-beta.zip -d ~/.gigacode/extensions

# 3. Зарегистрируйте extension в настройках GigaCode
mkdir -p ~/.gigacode
python -c "import json, pathlib; p=pathlib.Path.home()/'.gigacode/settings.json'; data=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}; exts=data.setdefault('extensions', []); exts.append('extensions/delion') if 'extensions/delion' not in exts else None; p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')"

# 4. Запустите GigaCode и инициализируйте структуру Delion внутри проекта
gigacode
/deli:init
```

После регистрации в `~/.gigacode/settings.json` должен быть путь к extension:

```json
{
  "extensions": [
    "extensions/delion"
  ]
}
```

PowerShell-вариант установки для Windows:

```powershell
$zip = Join-Path $env:TEMP "delion-gigacode-beta.zip"
$url = "https://github.com/AverbakhMV/delion-orchestrator/raw/main/releases/beta/delion-gigacode.zip"
$extensionRoot = Join-Path $env:USERPROFILE ".gigacode\extensions"
$delionDir = Join-Path $extensionRoot "delion"
$settingsDir = Join-Path $env:USERPROFILE ".gigacode"
$settingsFile = Join-Path $settingsDir "settings.json"

Invoke-WebRequest -Uri $url -OutFile $zip
New-Item -ItemType Directory -Force -Path $extensionRoot | Out-Null
if (Test-Path -LiteralPath $delionDir) {
    Remove-Item -LiteralPath $delionDir -Recurse -Force
}
Expand-Archive -LiteralPath $zip -DestinationPath $extensionRoot -Force

New-Item -ItemType Directory -Force -Path $settingsDir | Out-Null
$settings = if (Test-Path -LiteralPath $settingsFile) {
    Get-Content -LiteralPath $settingsFile -Raw | ConvertFrom-Json
} else {
    [pscustomobject]@{}
}
if (-not ($settings.PSObject.Properties.Name -contains "extensions")) {
    $settings | Add-Member -MemberType NoteProperty -Name "extensions" -Value @()
}
if ($settings.extensions -notcontains "extensions/delion") {
    $settings.extensions = @($settings.extensions) + "extensions/delion"
}
$settings | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $settingsFile -Encoding UTF8
```

Если репозиторий уже скачан и вы находитесь в его корне, можно установить локальный beta-архив:

```bash
mkdir -p ~/.gigacode/extensions
rm -rf ~/.gigacode/extensions/delion
unzip -o releases/beta/delion-gigacode.zip -d ~/.gigacode/extensions
mkdir -p ~/.gigacode
python -c "import json, pathlib; p=pathlib.Path.home()/'.gigacode/settings.json'; data=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}; exts=data.setdefault('extensions', []); exts.append('extensions/delion') if 'extensions/delion' not in exts else None; p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')"
gigacode
/deli:init
```

Собрать локальный beta-архив из текущих исходников:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_release.ps1
```

## Команды

```text
/deli:init
```

Анализирует проект и создает:

```text
docs/system-requirements.md
```

```text
/deli:feature BR-001 "Добавить экспорт отчета в CSV"
/deli:feature BR-001 @docs/input/business-requirements.md
```

Создает черновик бизнес-требований:

```text
docs/business-requirements/BR-001.md
```

Перед созданием бизнес-требований агент читает корневой `AGENTS.md` целевого проекта, если он есть, и учитывает его при заполнении требований, ограничений, критериев готовности и требований к тестам.

```text
/deli:validate system
/deli:validate feature BR-001
/deli:validate file docs/business-requirements/BR-001.md --type business
```

Валидирует системные или бизнес-требования. Delion считает файл неготовым, если в нем остались `TODO`, unchecked-пункты, `status: draft`, статус ручной валидации или отсутствуют обязательные секции.

```text
/deli:test BR-001
```

Создает или обновляет реальные тесты проекта по `docs/business-requirements/BR-001.md`. Команда должна покрыть must-have требования, критерии готовности, edge cases и требования к тестам до review. Тесты на этой стадии не запускаются.

Для S2T/data mapping задач `/deli:test` читает Excel-файл из `s2t`, лист `Target_columns`, и создает CSV с SQL-тестами в формате `Id:Entity:Test_name:Test_script:Expected_result`. Обязательные проверки: кардинальность по всем таблицам, обязательные атрибуты с `col null = NO`, дубли по PK и битые ссылки FK -> PK. Временные CSV-файлы для чтения Excel должны удаляться, чувствительные данные не выводятся в чат.

```text
/deli:review BR-001
```

Проводит code review изменений по бизнес-требованию. Если review нашел замечания, основной агент должен исправить их в той же feature branch, обновить тесты при изменении поведения и повторить review до принятия.

```text
/deli:run BR-001
```

Запускает workflow по `docs/business-requirements/BR-001.md` только после валидации системных и бизнес-требований. Git branch, push, PR, merge и Jenkins выполняются GigaCode через доступные MCP/tools.

`/deli:run` выполняет полный цикл: реализация, создание или обновление тестов, review loop, push, PR, merge и post-merge CI. Отдельные `/deli:test`, `/deli:review` и `/deli:ci` нужны для ручного запуска или повторения конкретной стадии. Review выполняется до push и PR.

```text
/deli:resume BR-001
```

Продолжает workflow с последнего checkpoint. Новая ветка для той же фичи не создается.

```text
/deli:status BR-001
```

Показывает run status и checkpoint.

```text
/deli:subtask BR-001 WT-001 planned
/deli:subtask BR-001 WT-001 in_progress
/deli:subtask BR-001 WT-001 done
```

Фиксирует состояние внутренней подзадачи большой фичи в `.deli/state.json`. Подзадачи выполняются в той же feature branch и том же PR, что и основная фича.

```text
/deli:ci BR-001
```

Запускает post-merge Jenkins CI loop для фичи через MCP/tools GigaCode.

## Workflow

```text
system requirements
  -> business requirements
  -> validation
  -> plan
  -> one feature branch
  -> optional work items for large features
  -> one execution agent
  -> create or update tests for all business requirements
  -> review loop
  -> PR to master/main
  -> merge
  -> post-merge CI loop
```

Ключевые компоненты:

- prompt-команды из `commands/deli/` управляют стадиями workflow;
- Python runtime создает и валидирует документы, а также ведет checkpoint-и;
- GigaCode MCP/tools выполняют реальные git, Jenkins и PR действия;
- CI loop выполняется через Jenkins MCP/tools GigaCode после merge PR в основную ветку.

## Resume

Delion сохраняет checkpoint в:

```text
.deli/state.json
```

Checkpoint фиксирует завершенные шаги:

- `branch_created`
- `implemented`
- `tests_created`
- `reviewed`
- `branch_pushed`
- `pr_created`
- `pr_merged`
- `ci_passed`

Для больших фич Delion также хранит внутренние work items в том же checkpoint. `/deli:status BR-001` показывает `subtasks=DONE/TOTAL`, а `/deli:resume BR-001` возвращает первую незавершенную подзадачу.

Если выполнение прервано, агент должен выполнить:

```text
/deli:status BR-001
/deli:resume BR-001
```

## Claude Code Plugin

Claude Code - дополнительный режим, не основной.

Файлы:

```text
.claude-plugin/plugin.json
.claude-plugin/marketplace.json
commands/deli/*.md
```

Локальная установка:

```text
/plugin marketplace add ./delion
/plugin install delion@delion-marketplace
```

После установки ожидаются те же команды:

```text
/deli:init
/deli:feature
/deli:validate
/deli:test
/deli:review
/deli:run
/deli:resume
/deli:status
/deli:subtask
/deli:ci
```
