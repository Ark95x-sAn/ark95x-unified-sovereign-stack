"""ARK95X Codex Security Adapter
Runs a real secret-pattern scan (AWS keys, generic api_key/secret/token
assignments, PEM private key headers, Slack tokens, GitHub PATs) over a
set of files -- by default the files `git diff` reports as changed against
a base ref -- and reports the result through the control plane.

A finding is a veto: codex_security reports `status="vetoed"` with the
evidence and does not request release. A clean scan still cannot release
itself -- `security_sensitive` is one of
control_plane.APPROVAL_REQUIRED_ACTION_CLASSES, so `request_action` always
queues the release for human approval, matching docs/control-plane-pass-1.md
invariant 4. This adapter never bypasses that.
"""
from __future__ import annotations

import logging
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ark95x.codex_security.scanner")

SECRET_PATTERNS = (
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("generic_api_key", re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9/_\-\.]{12,}['\"]")),
    ("private_key_block", re.compile(r"-----BEGIN (RSA|EC|OPENSSH|DSA)? ?PRIVATE KEY-----")),
    ("slack_token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
)


class CodexSecurityAdapter:
    """Real threat-modeling/review lane: inspects actual file contents,
    reports/vetoes through a ControlPlane."""

    def __init__(self, control_plane: Any = None, repo_path: str = "."):
        self.control_plane = control_plane
        self.repo_path = Path(repo_path)

    def changed_files(self, base_ref: str = "HEAD") -> List[str]:
        """Real `git diff --name-only` against base_ref. Returns [] (not a
        raise) if the repo/ref is unavailable -- callers pass explicit
        paths when they want to scan without relying on git."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", base_ref],
                cwd=self.repo_path, capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                return []
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("git diff failed: %s", exc)
            return []

    @staticmethod
    def scan_text(text: str) -> List[Dict[str, str]]:
        findings = []
        for rule_name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                findings.append({"rule": rule_name, "match_preview": match.group(0)[:12] + "..."})
        return findings

    def scan_files(self, paths: List[str]) -> Dict[str, List[Dict[str, str]]]:
        findings_by_file: Dict[str, List[Dict[str, str]]] = {}
        for rel_path in paths:
            file_path = self.repo_path / rel_path
            try:
                text = file_path.read_text(errors="ignore")
            except (FileNotFoundError, IsADirectoryError, OSError):
                continue
            findings = self.scan_text(text)
            if findings:
                findings_by_file[rel_path] = findings
        return findings_by_file

    def review(self, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Scans `paths` (or the real changed-files set) and either vetoes
        (a finding exists) or requests human release (clean)."""
        paths = self.changed_files() if paths is None else paths
        findings_by_file = self.scan_files(paths)
        observed_at = datetime.now(timezone.utc).isoformat()
        evidence = {
            "files_scanned": len(paths),
            "findings": findings_by_file,
            "observed_at": observed_at,
        }

        if findings_by_file:
            if self.control_plane is not None:
                self.control_plane.report(agent_id="codex_security", status="vetoed", payload=evidence)
            return {"verdict": "vetoed", **evidence}

        request = None
        if self.control_plane is not None:
            request = self.control_plane.request_action(
                agent_id="codex_security",
                action="release_security_review",
                action_class="security_sensitive",
                payload=evidence,
            )
        return {"verdict": "clean_pending_human_release", "request": request, **evidence}
