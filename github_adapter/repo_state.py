"""ARK95X GitHub Adapter
Reports on real local git state -- HEAD commit, current branch, working-tree
dirtiness, the latest commit's message -- via `git status`/`git log`/`git
diff` subprocess calls, and gates a real `git push` behind the control
plane. Deliberately local-git-based: this repo's CI and this adapter do
not assume GitHub API credentials are configured.

`report_repo_state()` is a plain observation (github's "record_proof"
capability) and reports directly, no gate needed. `request_push()` asks to
publish commits to a remote -- a `deployment`-class action, always queued
for human approval -- and only `approve_pending_push()` actually runs
`git push`, reporting the real result back.
"""
from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("ark95x.github_adapter.repo_state")

GitRunner = Callable[[list], "subprocess.CompletedProcess"]


class GitHubAdapter:
    """Source-control observation and gated-push lane, backed by real git
    subprocess calls against a local working tree."""

    def __init__(
        self,
        control_plane: Any = None,
        repo_path: str = ".",
        git_runner: Optional[GitRunner] = None,
    ):
        self.control_plane = control_plane
        self.repo_path = Path(repo_path)
        self._run: GitRunner = git_runner or self._default_git_runner
        self._pending: Dict[str, Dict[str, Any]] = {}

    def _default_git_runner(self, args: list) -> "subprocess.CompletedProcess":
        return subprocess.run(["git", *args], cwd=self.repo_path, capture_output=True, text=True, timeout=15)

    def report_repo_state(self) -> Dict[str, Any]:
        """Real `git status`/`git log` observation, reported directly --
        no approval needed to look at the repo."""
        head = self._run(["rev-parse", "HEAD"]).stdout.strip()
        branch = self._run(["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
        status_lines = [
            line for line in self._run(["status", "--porcelain"]).stdout.splitlines() if line.strip()
        ]
        last_commit = self._run(["log", "-1", "--format=%H|%an|%ct|%s"]).stdout.strip()
        observed_at = datetime.now(timezone.utc).isoformat()

        payload = {
            "head_commit": head,
            "branch": branch,
            "dirty_file_count": len(status_lines),
            "dirty_files": status_lines[:20],
            "last_commit": last_commit,
            "observed_at": observed_at,
        }
        status_label = "dirty" if status_lines else "clean"
        if self.control_plane is not None:
            self.control_plane.report(agent_id="github", status=status_label, payload=payload)
        return payload

    def request_push(self, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """Requests to publish real commits to a remote -- always queued
        for human approval (`deployment` is in
        control_plane.APPROVAL_REQUIRED_ACTION_CLASSES)."""
        if self.control_plane is None:
            raise ValueError("GitHubAdapter.request_push requires a control_plane")

        branch = branch or self._run(["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
        request = self.control_plane.request_action(
            agent_id="github",
            action=f"push:{remote}/{branch}",
            action_class="deployment",
            payload={"remote": remote, "branch": branch},
        )
        if request["disposition"] == "queued_for_human_approval":
            self._pending[request["request_id"]] = {"remote": remote, "branch": branch}
        return request

    def approve_pending_push(self, request_id: str) -> Dict[str, Any]:
        """Executes the previously queued `git push` and reports the real
        result back to the control plane."""
        pending = self._pending.pop(request_id, None)
        if pending is None:
            raise KeyError(f"No pending github push for request_id {request_id}")

        result = self._run(["push", pending["remote"], pending["branch"]])
        succeeded = result.returncode == 0
        payload = {
            "request_id": request_id,
            "remote": pending["remote"],
            "branch": pending["branch"],
            "succeeded": succeeded,
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-2000:],
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.control_plane is not None:
            self.control_plane.report(
                agent_id="github",
                status="completed" if succeeded else "failed",
                payload=payload,
            )
        return payload
