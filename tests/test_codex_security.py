"""ARK95X Codex Security Adapter tests. Scans real files on disk for real
secret patterns (no mocked findings), and proves a finding vetoes while a
clean scan still cannot self-release (security_sensitive always requires
human approval)."""
import pytest

from control_plane import build_default_control_plane
from codex_security import CodexSecurityAdapter


def test_scan_text_detects_aws_key():
    findings = CodexSecurityAdapter.scan_text("AWS_KEY = 'AKIAABCDEFGHIJKLMNOP'")
    assert any(f["rule"] == "aws_access_key" for f in findings)


def test_scan_text_detects_generic_api_key_assignment():
    findings = CodexSecurityAdapter.scan_text('api_key = "sk_live_1234567890abcdef"')
    assert any(f["rule"] == "generic_api_key" for f in findings)


def test_scan_text_detects_private_key_block():
    findings = CodexSecurityAdapter.scan_text("-----BEGIN RSA PRIVATE KEY-----\nMIIB...")
    assert any(f["rule"] == "private_key_block" for f in findings)


def test_scan_text_clean_source_has_no_findings():
    findings = CodexSecurityAdapter.scan_text("def add(a, b):\n    return a + b\n")
    assert findings == []


def test_review_with_a_real_secret_vetoes_and_reports(tmp_path):
    bad_file = tmp_path / "config.py"
    bad_file.write_text("SECRET_TOKEN = 'abcdef0123456789abcd'\n")

    plane = build_default_control_plane()
    adapter = CodexSecurityAdapter(control_plane=plane, repo_path=str(tmp_path))

    result = adapter.review(paths=["config.py"])

    assert result["verdict"] == "vetoed"
    assert "config.py" in result["findings"]

    agent = plane.agents["codex_security"]
    assert agent.state == "vetoed"
    assert "config.py" in agent.last_report["findings"]


def test_review_clean_files_still_requires_human_release(tmp_path):
    good_file = tmp_path / "clean.py"
    good_file.write_text("def hello():\n    return 'hi'\n")

    plane = build_default_control_plane()
    adapter = CodexSecurityAdapter(control_plane=plane, repo_path=str(tmp_path))

    result = adapter.review(paths=["clean.py"])

    assert result["verdict"] == "clean_pending_human_release"
    assert result["findings"] == {}
    assert result["request"]["disposition"] == "queued_for_human_approval"
    assert result["request"]["executed"] is False


def test_review_missing_file_is_skipped_not_raised(tmp_path):
    plane = build_default_control_plane()
    adapter = CodexSecurityAdapter(control_plane=plane, repo_path=str(tmp_path))

    result = adapter.review(paths=["does_not_exist.py"])

    assert result["verdict"] == "clean_pending_human_release"


def test_changed_files_uses_real_git_diff_in_a_scratch_repo(tmp_path):
    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("one\n")
    subprocess.run(["git", "add", "a.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    (tmp_path / "a.txt").write_text("one\ntwo\n")

    adapter = CodexSecurityAdapter(control_plane=None, repo_path=str(tmp_path))
    changed = adapter.changed_files(base_ref="HEAD")

    assert "a.txt" in changed
