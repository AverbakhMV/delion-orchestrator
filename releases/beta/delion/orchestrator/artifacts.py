from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


DOCS_DIR = Path("docs")
SYSTEM_REQUIREMENTS_FILE = DOCS_DIR / "system-requirements.md"
BUSINESS_REQUIREMENTS_DIR = DOCS_DIR / "business-requirements"


@dataclass(frozen=True)
class ProjectSnapshot:
    root: Path
    files_count: int
    languages: list[str]
    markers: list[str]
    entrypoints: list[str]
    test_paths: list[str]


class ProjectAnalyzer:
    IGNORED_DIRS = {
        ".git",
        ".idea",
        ".venv",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        "target",
        ".bloop",
        ".metals",
        ".scala-build",
        ".gradle",
        ".mvn",
        "out",
        ".deli",
    }

    LANGUAGE_BY_SUFFIX = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript/React",
        ".jsx": "JavaScript/React",
        ".java": "Java",
        ".kt": "Kotlin",
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",
        ".scala": "Scala",
        ".sbt": "SBT",
    }

    PROJECT_MARKERS = {
        "pyproject.toml": "Python packaging",
        "requirements.txt": "Python requirements",
        "package.json": "Node.js package",
        "pom.xml": "Maven",
        "build.sbt": "SBT",
        "build.gradle": "Gradle",
        "Jenkinsfile": "Jenkins pipeline",
        "Dockerfile": "Docker image",
        "docker-compose.yml": "Docker Compose",
    }

    def analyze(self, root: Path) -> ProjectSnapshot:
        files = self._iter_project_files(root)
        languages = sorted(
            {
                self.LANGUAGE_BY_SUFFIX[path.suffix]
                for path in files
                if path.suffix in self.LANGUAGE_BY_SUFFIX
            }
        )
        markers = [
            f"{name}: {description}"
            for name, description in self.PROJECT_MARKERS.items()
            if (root / name).exists()
        ]
        entrypoints = [str(path.relative_to(root)) for path in files if path.name in {"main.py", "app.py", "manage.py"}]
        test_paths = [
            str(path.relative_to(root))
            for path in files
            if "test" in path.name.lower() or "tests" in path.parts
        ]
        return ProjectSnapshot(
            root=root,
            files_count=len(files),
            languages=languages,
            markers=markers,
            entrypoints=entrypoints,
            test_paths=test_paths,
        )

    def _is_relevant(self, path: Path) -> bool:
        return not any(part in self.IGNORED_DIRS for part in path.parts)

    def _iter_project_files(self, root: Path) -> list[Path]:
        files: list[Path] = []
        for current_root, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda _error: None):
            current_path = Path(current_root)
            dirnames[:] = [dirname for dirname in dirnames if dirname not in self.IGNORED_DIRS]
            for filename in filenames:
                path = current_path / filename
                if not self._is_relevant(path):
                    continue
                try:
                    if path.is_file():
                        files.append(path)
                except OSError:
                    continue
        return files


def write_system_requirements(snapshot: ProjectSnapshot) -> Path:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    content = "\n".join(
        [
            "# Delion: системные требования проекта",
            "",
            f"Статус: требуется валидация человеком",
            f"Сформировано: {datetime.now().isoformat(timespec='seconds')}",
            "",
            "## Обнаруженный контекст",
            "",
            f"- Корень проекта: `{snapshot.root}`",
            f"- Количество файлов в анализе: {snapshot.files_count}",
            f"- Языки: {', '.join(snapshot.languages) if snapshot.languages else 'нужно уточнить'}",
            f"- Маркеры проекта: {', '.join(snapshot.markers) if snapshot.markers else 'не обнаружены'}",
            f"- Точки входа: {', '.join(snapshot.entrypoints) if snapshot.entrypoints else 'нужно уточнить'}",
            f"- Тесты: {', '.join(snapshot.test_paths) if snapshot.test_paths else 'нужно уточнить'}",
            "",
            "## Обязательные требования к изменениям",
            "",
            "- Одна бизнес-фича должна выполняться в одной ветке и одном PR.",
            "- Микрозадачи не должны создавать отдельные git-ветки.",
            "- Перед push и PR должен пройти review loop.",
            "- Изменения должны сопровождаться созданными или обновленными тестами либо явным обоснованием, почему тесты не нужны.",
            "- Локальные тесты в Delion workflow не запускаются; тестовая стадия только создает или обновляет тестовые файлы.",
            "- Code review должен быть принят до push feature branch и до PR.",
            "- Jenkins build запускается после merge PR в основную ветку.",
            "",
            "## Требует ручного дополнения",
            "",
            "- Основная бизнес-цель системы: TODO",
            "- Критичные пользовательские сценарии: TODO",
            "- Ограничения безопасности и доступа: TODO",
            "- Правила именования веток и PR: TODO",
            "- Правила оформления тестов: TODO",
            "- Jenkins job и параметры пост-merge запуска: TODO",
            "- Правила auto-merge или human approval: TODO",
            "",
        ]
    )
    SYSTEM_REQUIREMENTS_FILE.write_text(content, encoding="utf-8")
    return SYSTEM_REQUIREMENTS_FILE


def write_business_requirements(feature_key: str, task_text: str, source_file: Path | None = None) -> Path:
    BUSINESS_REQUIREMENTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = BUSINESS_REQUIREMENTS_DIR / f"{feature_key}.md"
    source_note = f"Файл-источник: `{source_file}`" if source_file else "Источник: задача из терминала"
    title = task_text.strip().splitlines()[0].strip().strip('"') or feature_key
    content = "\n".join(
        [
            "---",
            f"id: {feature_key}",
            f'title: "{title}"',
            "status: draft",
            f"created: {date.today().isoformat()}",
            "priority: P2",
            "size: M",
            "---",
            "",
            f"# Delion: бизнес-требования {feature_key}",
            "",
            "Статус: draft",
            source_note,
            "Проектный контекст: перед заполнением требований нужно прочитать корневой `AGENTS.md` целевого проекта и учесть его инструкции.",
            "",
            "## Исходная задача",
            "",
            task_text.strip(),
            "",
            "## Что и зачем",
            "",
            "**Что делаем:**",
            task_text.strip(),
            "",
            "**Зачем:**",
            "TODO: описать бизнес-ценность изменения.",
            "",
            "**Для кого:**",
            "TODO: указать пользователей, роли или системы-потребители.",
            "",
            "## Требования",
            "",
            "### Должно быть (Must have)",
            "",
            "- [ ] TODO: основное требование из описания.",
            "",
            "### Хорошо бы (Nice to have)",
            "",
            "- [ ] TODO: дополнительные пожелания, если они есть.",
            "",
            "## Критерии готовности",
            "",
            "- [ ] Функционал работает для основного сценария.",
            "- [ ] Ошибки и edge cases обработаны.",
            "- [ ] Поведение покрыто созданными или обновленными тестами либо явно описано, почему тесты не нужны.",
            "",
            "## Требования к тестам",
            "",
            "- [ ] TODO: указать критерии готовности, которые должны быть покрыты автоматическими тестами.",
            "- [ ] TODO: указать обязательные негативные сценарии и edge cases.",
            "- [ ] TODO: указать, какие тестовые файлы и сценарии должны быть созданы или обновлены для этой фичи.",
            "- [ ] Для S2T/data mapping: создать CSV с SQL-тестами по листу `Target_columns` из Excel-файла в `s2t` в формате `Id:Entity:Test_name:Test_script:Expected_result`.",
            "",
            "## Ограничения",
            "",
            "- Одна фича выполняется в одной feature-ветке и одном PR.",
            "- Внутренние work items не создают отдельные ветки.",
            "- Если фича большая, она разбивается на work items; состояние каждого work item фиксируется в `.deli/state.json` через `/deli:subtask`.",
            "- PR не создается до прохождения review loop.",
            "- Jenkins CI запускается после merge PR в основную ветку.",
            "- TODO: добавить проектные ограничения.",
            "",
            "## Готовность к разработке",
            "",
            "- [ ] Требования проверены человеком.",
            "- [ ] Must have требования полные и проверяемые.",
            "- [ ] Критерии готовности полные и проверяемые.",
            "- [ ] Требования к тестам заполнены.",
            "- [ ] Системные требования проекта учтены.",
            "- [ ] Инструкции из корневого `AGENTS.md` учтены.",
            "",
            "## Следующий шаг",
            "",
            "После ручной проверки:",
            "",
            "```text",
            f"/deli:validate feature {feature_key}",
            f"/deli:run {feature_key}",
            "```",
            "",
        ]
    )
    output_path.write_text(content, encoding="utf-8")
    return output_path
