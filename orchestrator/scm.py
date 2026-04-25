from __future__ import annotations

from dataclasses import dataclass, field

from orchestrator.models import PullRequest


@dataclass
class InMemoryScmClient:
    default_base_branch: str = "master"
    branches: set[str] = field(default_factory=set)
    pull_requests: list[PullRequest] = field(default_factory=list)

    def create_feature_branch(self, branch_name: str, base_branch: str) -> None:
        if branch_name in self.branches:
            return
        self.branches.add(branch_name)

    def push_branch(self, branch_name: str) -> None:
        if branch_name not in self.branches:
            self.branches.add(branch_name)

    def open_pull_request(
        self,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str,
    ) -> PullRequest:
        if source_branch not in self.branches:
            self.branches.add(source_branch)
        pull_request = PullRequest(
            number=len(self.pull_requests) + 1,
            url=f"https://example.invalid/pr/{len(self.pull_requests) + 1}",
            source_branch=source_branch,
            target_branch=target_branch,
        )
        self.pull_requests.append(pull_request)
        return pull_request
