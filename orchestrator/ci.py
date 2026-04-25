from __future__ import annotations

from dataclasses import dataclass, field

from orchestrator.models import CiResult, CiStatus, FeaturePlan


@dataclass
class InMemoryCIRunner:
    fail_first_attempts: int = 0
    attempts: list[str] = field(default_factory=list)

    def run_validation_loop(
        self,
        plan: FeaturePlan,
        branch_name: str,
        max_attempts: int,
    ) -> CiResult:
        for attempt in range(1, max_attempts + 1):
            self.attempts.append(branch_name)
            if attempt > self.fail_first_attempts:
                return CiResult(
                    status=CiStatus.SUCCESS,
                    build_url=f"https://jenkins.example.invalid/job/{plan.feature.key}/{attempt}",
                )

        return CiResult(
            status=CiStatus.FAILED,
            build_url=f"https://jenkins.example.invalid/job/{plan.feature.key}/{max_attempts}",
            log_excerpt="CI-проверка завершилась ошибкой после всех retry attempts.",
        )
