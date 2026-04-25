from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


SYSTEM_REQUIRED_SECTIONS = [
    "# Delion: системные требования проекта",
    "## Обнаруженный контекст",
    "## Обязательные требования к изменениям",
    "## Требует ручного дополнения",
]

BUSINESS_REQUIRED_SECTIONS = [
    "# Delion: бизнес-требования",
    "## Исходная задача",
    "## Бизнес-цель",
    "## Пользователи и сценарии",
    "## Acceptance criteria",
    "## Требования к тестам",
    "## Ограничения",
    "## Готовность к разработке",
]


@dataclass(frozen=True)
class ValidationResult:
    path: Path
    document_type: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


class RequirementsValidator:
    def validate_file(self, path: Path, document_type: str = "auto") -> ValidationResult:
        if not path.exists():
            return ValidationResult(
                path=path,
                document_type=document_type,
                errors=[f"Файл не найден: {path}"],
            )

        text = path.read_text(encoding="utf-8")
        resolved_type = self._resolve_type(text, document_type)
        errors = self.validate_text(text, resolved_type)
        warnings = self._warnings(text)
        return ValidationResult(
            path=path,
            document_type=resolved_type,
            errors=errors,
            warnings=warnings,
        )

    def validate_text(self, text: str, document_type: str) -> list[str]:
        errors: list[str] = []
        required_sections = self._required_sections(document_type)

        for section in required_sections:
            if section not in text:
                errors.append(f"Отсутствует обязательная секция: {section}")

        if "TODO" in text:
            errors.append("В файле остались TODO.")
        if "- [ ]" in text:
            errors.append("В файле остались unchecked-пункты готовности.")
        if "Статус: требуется валидация человеком" in text:
            errors.append("Статус файла указывает, что требуется валидация человеком.")
        if "требуется валидация и дополнение человеком" in text.lower():
            errors.append("Статус файла указывает, что требуется валидация и дополнение человеком.")

        return errors

    def _resolve_type(self, text: str, document_type: str) -> str:
        if document_type != "auto":
            return document_type
        if "# Delion: системные требования проекта" in text:
            return "system"
        if "# Delion: бизнес-требования" in text:
            return "business"
        return "unknown"

    def _required_sections(self, document_type: str) -> list[str]:
        if document_type == "system":
            return SYSTEM_REQUIRED_SECTIONS
        if document_type == "business":
            return BUSINESS_REQUIRED_SECTIONS
        return []

    def _warnings(self, text: str) -> list[str]:
        warnings: list[str] = []
        if "Jenkins" not in text:
            warnings.append("Не найдено упоминание Jenkins; проверьте, описана ли CI-сборка.")
        if "review" not in text.lower():
            warnings.append("Не найдено упоминание review; проверьте, описан ли review gate.")
        return warnings
