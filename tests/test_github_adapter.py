"""ARK95X GitHub Adapter tests. report_repo_state() runs against a real,
throwaway git repo built in tmp_path with real `git` subprocess calls
(never this working tree). request_push()/approve_pending_push() use an
injected git runner so no test ever touches a real remote."""
import subprocess

import pytest

from control_plane import build_default_control_plane
from github_adapter import GitHubAdapter


@pytest.fixture
def scratch_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("one\n")
    subprocess.run(["git", "add", "a.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial commit"], cwd=tmp_path, check=True)
    return tmp_path


def test_report_repo_state_clean_tree(scratch_repo):
    plane = build_default_control_plane()
    adapter = GitHubAdapter(control_plane=plane, repo_path=str(scratch_repo))

    payload = adapter.report_repo_state()

    assert payload["dirty_file_count"] == 0
    assert "initial commit" in payload["last_commit"]
    assert plane.agents["github"].state == "clean"


def test_report_repo_state_dirty_tree(scratch_repo):
    (scratch_repo / "a.txt").write_text("one\ntwo\n")
    plane = build_default_control_plane()
    adapter = GitHubAdapter(control_plane=plane, repo_path=str(scratch_repo))

    payload = adapter.report_repo_state()

    assert payload["dirty_file_count"] == 1
    assert plane.agents["github"].state == "dirty"


def test_request_push_requires_control_plane():
    adapter = GitHubAdapter(control_plane=None)
    with pytest.raises(ValueError):
        adapter.request_push()


class FakeCompleted:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_request_push_queues_for_human_approval_and_does_not_run(scratch_repo):
    plane = build_default_control_plane()
    calls = []

    def fake_runner(args):
        calls.append(args)
        return FakeCompleted(stdout="main")

    adapter = GitHubAdapter(control_plane=plane, repo_path=str(scratch_repo), git_runner=fake_runner)

    request = adapter.request_push(remote="origin", branch="main")

    assert request["disposition"] == "queued_for_human_approval"
    assert request["executed"] is False
    assert not any(c[0] == "push" for c in calls)


def test_approve_pending_push_executes_and_reports_real_outcome(scratch_repo):
    plane = build_default_control_plane()
    calls = []

    def fake_runner(args):
        calls.append(args)
        if args[0] == "push":
            return FakeCompleted(returncode=0, stdout="pushed ok")
        return FakeCompleted(stdout="main")

    adapter = GitHubAdapter(control_plane=plane, repo_path=str(scratch_repo), git_runner=fake_runner)

    request = adapter.request_push(remote="origin", branch="main")
    result = adapter.approve_pending_push(request["request_id"])

    assert result["succeeded"] is True
    assert ["push", "origin", "main"] in calls
    agent = plane.agents["github"]
    assert agent.state == "completed"
    assert agent.last_report["request_id"] == request["request_id"]


def test_approve_pending_push_reports_failure(scratch_repo):
    plane = build_default_control_plane()

    def failing_runner(args):
        if args[0] == "push":
            return FakeCompleted(returncode=1, stderr="rejected")
        return FakeCompleted(stdout="main")

    adapter = GitHubAdapter(control_plane=plane, repo_path=str(scratch_repo), git_runner=failing_runner)

    request = adapter.request_push(remote="origin", branch="main")
    result = adapter.approve_pending_push(request["request_id"])

    assert result["succeeded"] is False
    assert plane.agents["github"].state == "failed"


def test_approve_unknown_request_id_raises(scratch_repo):
    plane = build_default_control_plane()
    adapter = GitHubAdapter(control_plane=plane, repo_path=str(scratch_repo))
    with pytest.raises(KeyError):
        adapter.approve_pending_push("not-a-real-id")
