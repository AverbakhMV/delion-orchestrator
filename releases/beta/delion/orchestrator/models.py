from __future__ import annotations

from enum import Enum


class WorkflowStep(str, Enum):
    BRANCH_CREATED = "branch_created"
    IMPLEMENTED = "implemented"
    TESTS_CREATED = "tests_created"
    REVIEWED = "reviewed"
    BRANCH_PUSHED = "branch_pushed"
    PR_CREATED = "pr_created"
    PR_MERGED = "pr_merged"
    CI_PASSED = "ci_passed"
