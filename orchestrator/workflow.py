from __future__ import annotations

from dataclasses import dataclass

from orchestrator.agents import DeveloperAgent, PlannerAgent, ReviewerAgent
from orchestrator.models import (
    CiResult,
    CiStatus,
    CodeChangeSet,
    FeatureRequest,
    ReviewDecision,
    ReviewResult,
    WorkflowCheckpoint,
    WorkflowResult,
    WorkflowStep,
    WorkflowStatus,
)
from orchestrator.ports import CiRunner, ScmClient


@dataclass
class WorkflowEngine:
    planner: PlannerAgent
    developer: DeveloperAgent
    reviewer: ReviewerAgent
    scm: ScmClient
    ci: CiRunner
    max_review_fix_attempts: int = 2
    max_ci_attempts: int = 3

    def run_feature(
        self,
        feature_key: str,
        requirement_text: str,
        base_branch: str = "master",
        completed_steps: set[str] | None = None,
        requirements_file: str | None = None,
        checkpoint_callback=None,
    ) -> WorkflowResult:
        feature = FeatureRequest(
            key=feature_key,
            requirement_text=requirement_text,
            base_branch=base_branch,
        )
        plan = self.planner.build_plan(feature)
        completed_steps = completed_steps or set()
        errors: list[str] = []

        try:
            if WorkflowStep.PR_CREATED.value in completed_steps:
                return WorkflowResult(
                    feature_key=feature.key,
                    branch_name=plan.branch_name,
                    status=WorkflowStatus.PR_CREATED,
                    ci_result=CiResult(
                        status=CiStatus.SUCCESS,
                        build_url="checkpoint://ci-passed",
                    ),
                    review_result=ReviewResult(decision=ReviewDecision.APPROVED),
                )

            if WorkflowStep.BRANCH_CREATED.value not in completed_steps:
                self.scm.create_feature_branch(plan.branch_name, feature.base_branch)
                self._checkpoint(
                    plan,
                    WorkflowStep.BRANCH_CREATED,
                    completed_steps,
                    requirements_file,
                    checkpoint_callback,
                )

            if WorkflowStep.IMPLEMENTED.value not in completed_steps:
                change_set = self.developer.implement(plan)
                self._checkpoint(
                    plan,
                    WorkflowStep.IMPLEMENTED,
                    completed_steps,
                    requirements_file,
                    checkpoint_callback,
                )
            else:
                change_set = CodeChangeSet(
                    branch_name=plan.branch_name,
                    changed_files=["<checkpoint-restored-output>"],
                    notes=["Результат implementation восстановлен из checkpoint."],
                )

            if WorkflowStep.REVIEWED.value not in completed_steps:
                review_result = self.reviewer.review(plan, change_set)
                for _ in range(self.max_review_fix_attempts):
                    if review_result.decision == ReviewDecision.APPROVED:
                        break
                    change_set = self.developer.fix_after_review(plan, review_result.findings)
                    review_result = self.reviewer.review(plan, change_set)

                if review_result.decision != ReviewDecision.APPROVED:
                    errors.append("Review не одобрил feature-ветку.")
                    return WorkflowResult(
                        feature_key=feature.key,
                        branch_name=plan.branch_name,
                        status=WorkflowStatus.FAILED,
                        review_result=review_result,
                        errors=errors,
                    )
                self._checkpoint(
                    plan,
                    WorkflowStep.REVIEWED,
                    completed_steps,
                    requirements_file,
                    checkpoint_callback,
                )
            else:
                review_result = ReviewResult(decision=ReviewDecision.APPROVED)

            if WorkflowStep.CI_PASSED.value not in completed_steps:
                ci_result = self.ci.run_validation_loop(
                    plan=plan,
                    branch_name=plan.branch_name,
                    max_attempts=self.max_ci_attempts,
                )
                if ci_result.status != CiStatus.SUCCESS:
                    errors.append("CI завершился ошибкой после retry loop.")
                    return WorkflowResult(
                        feature_key=feature.key,
                        branch_name=plan.branch_name,
                        status=WorkflowStatus.FAILED,
                        ci_result=ci_result,
                        review_result=review_result,
                        errors=errors,
                    )
                self._checkpoint(
                    plan,
                    WorkflowStep.CI_PASSED,
                    completed_steps,
                    requirements_file,
                    checkpoint_callback,
                )
            else:
                ci_result = CiResult(
                    status=CiStatus.SUCCESS,
                    build_url="checkpoint://ci-passed",
                )

            if WorkflowStep.BRANCH_PUSHED.value not in completed_steps:
                self.scm.push_branch(plan.branch_name)
                self._checkpoint(
                    plan,
                    WorkflowStep.BRANCH_PUSHED,
                    completed_steps,
                    requirements_file,
                    checkpoint_callback,
                )

            if WorkflowStep.PR_CREATED.value not in completed_steps:
                pull_request = self.scm.open_pull_request(
                    title=f"{feature.key}: {plan.summary}",
                    body=self._pr_body(plan.summary),
                    source_branch=plan.branch_name,
                    target_branch=feature.base_branch,
                )
                self._checkpoint(
                    plan,
                    WorkflowStep.PR_CREATED,
                    completed_steps,
                    requirements_file,
                    checkpoint_callback,
                )
            else:
                pull_request = None
            return WorkflowResult(
                feature_key=feature.key,
                branch_name=plan.branch_name,
                status=WorkflowStatus.PR_CREATED,
                pull_request=pull_request,
                ci_result=ci_result,
                review_result=review_result,
            )
        except Exception as exc:
            errors.append(str(exc))
            return WorkflowResult(
                feature_key=feature.key,
                branch_name=plan.branch_name,
                status=WorkflowStatus.FAILED,
                errors=errors,
            )

    def _pr_body(self, summary: str) -> str:
        return "\n".join(
            [
                "Feature-ветка, подготовленная Delion.",
                "",
                f"Краткое описание: {summary}",
                "",
                "Политика: одна фича = одна ветка = один PR.",
            ]
        )

    def _checkpoint(
        self,
        plan,
        step: WorkflowStep,
        completed_steps: set[str],
        requirements_file: str | None,
        checkpoint_callback,
    ) -> None:
        completed_steps.add(step.value)
        if checkpoint_callback is None:
            return
        checkpoint_callback(
            WorkflowCheckpoint(
                feature_key=plan.feature.key,
                requirement_text=plan.feature.requirement_text,
                base_branch=plan.feature.base_branch,
                branch_name=plan.branch_name,
                completed_steps=sorted(completed_steps),
                requirements_file=requirements_file,
                status=WorkflowStatus(step.value) if step.value in WorkflowStatus._value2member_map_ else WorkflowStatus.PLANNED,
            )
        )
