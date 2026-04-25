from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
    }

    PROJECT_MARKERS = {
        "pyproject.toml": "Python packaging",
        "requirements.txt": "Python requirements",
        "package.json": "Node.js package",
        "pom.xml": "Maven",
        "build.gradle": "Gradle",
        "Jenkinsfile": "Jenkins pipeline",
        "Dockerfile": "Docker image",
        "docker-compose.yml": "Docker Compose",
    }

    def analyze(self, root: Path) -> ProjectSnapshot:
        files = [path for path in root.rglob("*") if path.is_file() and self._is_relevant(path)]
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
            "- Перед PR должны пройти review loop и CI loop.",
            "- Изменения должны сопровождаться тестами или явным обоснованием, почему тесты не нужны.",
            "- Jenkins build должен запускаться для ветки фичи до финального статуса.",
            "",
            "## Требует ручного дополнения",
            "",
            "- Основная бизнес-цель системы: TODO",
            "- Критичные пользовательские сценарии: TODO",
            "- Ограничения безопасности и доступа: TODO",
            "- Правила именования веток и PR: TODO",
            "- Команды локальной проверки: TODO",
            "- Jenkins job и параметры запуска: TODO",
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
    content = "\n".join(
        [
            f"# Delion: бизнес-требования {feature_key}",
            "",
            "Статус: требуется валидация человеком",
            source_note,
            "",
            "## Исходная задача",
            "",
            task_text.strip(),
            "",
            "## Бизнес-цель",
            "",
            "TODO: описать, какую бизнес-ценность дает изменение.",
            "",
            "## Пользователи и сценарии",
            "",
            "- TODO: указать роли пользователей.",
            "- TODO: описать основной happy path.",
            "- TODO: описать ошибки и edge cases.",
            "",
            "## Acceptance criteria",
            "",
            "- TODO: критерий 1.",
            "- TODO: критерий 2.",
            "- TODO: критерий 3.",
            "",
            "## Требования к тестам",
            "",
            "- TODO: указать, какие acceptance criteria должны быть покрыты автоматическими тестами.",
            "- TODO: указать обязательные негативные сценарии и edge cases.",
            "- TODO: указать команду запуска локальных тестов для этой фичи.",
            "",
            "## Ограничения",
            "",
            "- Не создавать отдельные ветки для внутренних микрозадач.",
            "- Не открывать PR до прохождения review loop и CI loop.",
            "- TODO: добавить проектные ограничения.",
            "",
            "## Готовность к разработке",
            "",
            "- [ ] Требования проверены человеком.",
            "- [ ] Acceptance criteria полные и проверяемые.",
            "- [ ] Для каждого бизнес-требования указан способ тестовой проверки.",
            "- [ ] Системные требования проекта учтены.",
            "",
        ]
    )
    output_path.write_text(content, encoding="utf-8")
    return output_path
