from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class WorkflowStatus(str, Enum):
    PLANNED = "planned"
    IMPLEMENTED = "implemented"
    REVIEWED = "reviewed"
    CI_RUNNING = "ci_running"
    READY_FOR_PR = "ready_for_pr"
    PR_CREATED = "pr_created"
    FAILED = "failed"


class WorkflowStep(str, Enum):
    BRANCH_CREATED = "branch_created"
    IMPLEMENTED = "implemented"
    REVIEWED = "reviewed"
    CI_PASSED = "ci_passed"
    BRANCH_PUSHED = "branch_pushed"
    PR_CREATED = "pr_created"


class ReviewDecision(str, Enum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class CiStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True)
class FeatureRequest:
    key: str
    requirement_text: str
    base_branch: str = "master"


@dataclass(frozen=True)
class WorkItem:
    title: str
    description: str


@dataclass(frozen=True)
class FeaturePlan:
    feature: FeatureRequest
    branch_name: str
    summary: str
    work_items: list[WorkItem]


@dataclass(frozen=True)
class CodeChangeSet:
    branch_name: str
    changed_files: list[str]
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReviewFinding:
    severity: str
    message: str
    file_path: str | None = None


@dataclass(frozen=True)
class ReviewResult:
    decision: ReviewDecision
    findings: list[ReviewFinding] = field(default_factory=list)


@dataclass(frozen=True)
class CiResult:
    status: CiStatus
    build_url: str
    log_excerpt: str = ""


@dataclass(frozen=True)
class PullRequest:
    number: int
    url: str
    source_branch: str
    target_branch: str


@dataclass(frozen=True)
class WorkflowResult:
    feature_key: str
    branch_name: str
    status: WorkflowStatus
    pull_request: PullRequest | None = None
    ci_result: CiResult | None = None
    review_result: ReviewResult | None = None
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        parts = [
            f"feature={self.feature_key}",
            f"branch={self.branch_name}",
            f"status={self.status.value}",
        ]
        if self.pull_request:
            parts.append(f"pr={self.pull_request.url}")
        if self.ci_result:
            parts.append(f"ci={self.ci_result.status.value}")
        if self.errors:
            parts.append(f"errors={len(self.errors)}")
        return " | ".join(parts)


@dataclass(frozen=True)
class WorkflowCheckpoint:
    feature_key: str
    requirement_text: str
    base_branch: str
    branch_name: str
    completed_steps: list[str] = field(default_factory=list)
    requirements_file: str | None = None
    status: WorkflowStatus = WorkflowStatus.PLANNED
    last_error: str | None = None
