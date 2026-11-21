# security-agent

Wraps audit-agent/ Emerald Tablet (allowlisted bandit/semgrep/gitleaks/trivy). Job: secrets scan, permission review, dependency/license check before any build. Risk: Green read-only scans; Red never auto-fixes/deletes. Model route: local first. Health: `python3 scripts/check_agent_fleet.py`. Live creation: none needed (repo file); dashboard: none.

Boundaries: no keys in chat/files, no post/send/publish/pay/delete, Job 001 NO-GO.
