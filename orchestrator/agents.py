from __future__ import annotations

import re

from orchestrator.models import (
    CodeChangeSet,
    FeaturePlan,
    FeatureRequest,
    ReviewDecision,
    ReviewFinding,
    ReviewResult,
    WorkItem,
)


class PlannerAgent:
    def build_plan(self, feature: FeatureRequest) -> FeaturePlan:
        branch_name = self._branch_name(feature.key, feature.requirement_text)
        return FeaturePlan(
            feature=feature,
            branch_name=branch_name,
            summary=feature.requirement_text.strip(),
            work_items=[
                WorkItem(
                    title="Реализовать объем фичи",
                    description="Внести все изменения production-кода за один проход execution agent.",
                ),
                WorkItem(
                    title="Добавить или обновить тесты",
                    description="Покрыть все бизнес-требования, acceptance criteria и ожидаемые регрессии в той же feature-ветке.",
                ),
                WorkItem(
                    title="Проверить сборку дистрибутива",
                    description="Запустить CI для тестов, статических проверок и сборки артефакта.",
                ),
            ],
        )

    def _branch_name(self, feature_key: str, requirement_text: str) -> str:
        slug_source = requirement_text.lower().strip()
        slug = re.sub(r"[^a-z0-9]+", "-", slug_source).strip("-")
        slug = slug[:48].strip("-") or "feature"
        return f"ai/{feature_key.lower()}-{slug}"


class DeveloperAgent:
    def implement(self, plan: FeaturePlan) -> CodeChangeSet:
        return CodeChangeSet(
            branch_name=plan.branch_name,
            changed_files=["<execution-agent-output>"],
            notes=[
                "Заглушка execution agent: здесь подключается LLM и инструменты изменения кода.",
                "Одна фича использует одну ветку; внутренние work items не создают ветки.",
            ],
        )

    def fix_after_review(self, plan: FeaturePlan, findings: list[ReviewFinding]) -> CodeChangeSet:
        return CodeChangeSet(
            branch_name=plan.branch_name,
            changed_files=["<execution-agent-output>"],
            notes=[f"Применены исправления по review: {len(findings)} замечаний."],
        )


class TestAgent:
    def create_or_update_tests(self, plan: FeaturePlan, change_set: CodeChangeSet) -> CodeChangeSet:
        return CodeChangeSet(
            branch_name=plan.branch_name,
            changed_files=["<test-agent-output>"],
            notes=[
                "Заглушка TestAgent: здесь агент добавляет или обновляет тесты под все бизнес-требования и acceptance criteria.",
                f"Тесты создаются в той же ветке: {change_set.branch_name}.",
            ],
        )


class ReviewerAgent:
    def review(self, plan: FeaturePlan, change_set: CodeChangeSet) -> ReviewResult:
        blocking_findings = [
            ReviewFinding(
                severity="blocking",
                message="Execution agent не вернул список измененных файлов.",
            )
        ]
        if not change_set.changed_files:
            return ReviewResult(
                decision=ReviewDecision.CHANGES_REQUESTED,
                findings=blocking_findings,
            )
        return ReviewResult(decision=ReviewDecision.APPROVED)
