"""
ARK95X Emerald Tablet - Code Audit Master Agent
Python AI orchestrator that runs all audit layers, 
analyzes results with local LLM (Ollama), and produces
intelligent summaries with fix recommendations.
"""
import shlex
import subprocess
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")

# Allowlist of audit tool binaries permitted for subprocess execution.
# These are hardcoded commands — no user input reaches this surface.
ALLOWED_TOOLS = frozenset({
    "pylint", "flake8", "shellcheck", "yamllint",
    "bandit", "semgrep", "gitleaks",
    "trivy", "mypy", "find",
})


class EmeraldTabletAgent:
    def __init__(self, target_dir="."):
        self.target = Path(target_dir).resolve()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_dir = Path(__file__).parent / "reports" / self.timestamp
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.findings = {}
        self.total_issues = 0

    def run_tool(self, name, cmd):
        """Run an audit tool via subprocess.

        Security note: *cmd* is always a hardcoded string defined in this
        file (see layer methods below). The first token is validated
        against ALLOWED_TOOLS so no arbitrary binary can be executed.
        We use shell=False with shlex.split for safe argument handling.
        """
        print(f"  [{name}] Running...")
        try:
            args = shlex.split(cmd)
            if args[0] not in ALLOWED_TOOLS:
                raise ValueError(f"Tool '{args[0]}' not in allowlist")
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.target),
            )
            output = result.stdout + result.stderr
            outfile = self.report_dir / f"{name.lower().replace(' ', '_')}.txt"
            outfile.write_text(output)
            lines = len([l for l in output.strip().split("\n") if l.strip()])
            self.findings[name] = {"lines": lines, "file": str(outfile)}
            self.total_issues += lines
            print(f"  [{name}] Done - {lines} lines")
            return output
        except subprocess.TimeoutExpired:
            print(f"  [{name}] Timeout")
            self.findings[name] = {"lines": 0, "file": "", "error": "timeout"}
            return ""
        except Exception as e:
            print(f"  [{name}] Error: {e}")
            self.findings[name] = {"lines": 0, "file": "", "error": str(e)}
            return ""

    def layer1_static(self):
        print("\n=== LAYER 1: STATIC ANALYSIS ===")
        self.run_tool("pylint", "pylint --recursive=y --output-format=text --score=no .")
        self.run_tool("flake8", "flake8 .")
        self.run_tool("shellcheck", "find . -name *.sh -exec shellcheck -f gcc {} +")
        self.run_tool("yamllint", "yamllint .")

    def layer2_security(self):
        print("\n=== LAYER 2: SECURITY ANALYSIS ===")
        self.run_tool("bandit", "bandit -r . -f txt -ll")
        self.run_tool("semgrep", "semgrep scan --config auto . --text")
        self.run_tool("gitleaks", "gitleaks detect --source . --verbose")

    def layer3_vulns(self):
        print("\n=== LAYER 3: VULNERABILITY SCAN ===")
        self.run_tool("trivy_fs", "trivy fs . --severity HIGH,CRITICAL")
        self.run_tool("trivy_config", "trivy config .")

    def layer4_types(self):
        print("\n=== LAYER 4: TYPE CHECKING ===")
        self.run_tool("mypy", "mypy . --ignore-missing-imports")

    def layer5_ai_analysis(self):
        print("\n=== LAYER 5: AI ANALYSIS (Ollama) ===")
        if not HAS_REQUESTS:
            print("  [AI] requests not installed, skipping")
            return ""
        try:
            summary_parts = []
            for name, data in self.findings.items():
                if data.get("file") and Path(data["file"]).exists():
                    content = Path(data["file"]).read_text()[:2000]
                    summary_parts.append(f"### {name}\n{content[:500]}")

            prompt = f"""You are an expert code auditor. Analyze these findings and provide:
1. Top 5 critical issues to fix immediately
2. Security vulnerabilities summary 
3. Code quality score (A-F)
4. Specific fix recommendations

Findings:
{''.join(summary_parts[:5])}
"""
            resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
                "model": OLLAMA_MODEL, "prompt": prompt, "stream": False
            }, timeout=120)
            if resp.status_code == 200:
                ai_output = resp.json().get("response", "")
                (self.report_dir / "ai_analysis.md").write_text(ai_output)
                print(f"  [AI] Analysis complete - {len(ai_output)} chars")
                return ai_output
        except Exception as e:
            print(f"  [AI] Ollama unavailable: {e}")
        return ""

    def generate_report(self, ai_analysis=""):
        report = f"""# Emerald Tablet Audit Report
**Target:** {self.target}
**Date:** {datetime.now().isoformat()}
**Agent:** ARK95X Code Audit Master v1.0
**Total Findings:** {self.total_issues}

---

## Tool Results
"""
        for name, data in self.findings.items():
            report += f"### {name}\n- Lines: {data['lines']}\n"
            if data.get("error"):
                report += f"- Error: {data['error']}\n"
            report += "\n"

        if ai_analysis:
            report += f"\n## AI Analysis\n{ai_analysis}\n"

        report += f"\n---\n*Generated by ARK95X Emerald Tablet Audit Agent*\n"

        report_file = self.report_dir / "REPORT.md"
        report_file.write_text(report)
        print(f"\nReport: {report_file}")
        return report

    def run(self):
        print("=" * 50)
        print("  EMERALD TABLET - CODE AUDIT MASTER v1.0")
        print("=" * 50)
        print(f"Target: {self.target}")
        print(f"Report: {self.report_dir}")

        self.layer1_static()
        self.layer2_security()
        self.layer3_vulns()
        self.layer4_types()
        ai = self.layer5_ai_analysis()
        report = self.generate_report(ai)

        print("\n" + "=" * 50)
        print("  AUDIT COMPLETE")
        print("=" * 50)
        print(f"Total findings: {self.total_issues}")
        return report


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    agent = EmeraldTabletAgent(target)
    agent.run()
