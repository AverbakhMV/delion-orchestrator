from __future__ import annotations

from typing import Protocol

from orchestrator.models import CiResult, FeaturePlan, PullRequest


class ScmClient(Protocol):
    def create_feature_branch(self, branch_name: str, base_branch: str) -> None:
        """Create exactly one branch for the whole feature."""

    def push_branch(self, branch_name: str) -> None:
        """Push the feature branch after the execution agent finishes changes."""

    def open_pull_request(
        self,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str,
    ) -> PullRequest:
        """Open one PR from the feature branch into master/main."""


class CiRunner(Protocol):
    def run_validation_loop(
        self,
        plan: FeaturePlan,
        branch_name: str,
        max_attempts: int,
    ) -> CiResult:
        """Run CI and return the final result after bounded retries."""
