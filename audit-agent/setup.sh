#!/bin/bash
# ARK95X CODE AUDIT MASTER AGENT - SETUP & BOOTSTRAP
# Emerald Tablet Pattern: One Source of Truth for All Code Audits
set -euo pipefail

GREEN='\033[1;32m'; BLUE='\033[1;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
echo -e "${GREEN}=== ARK95X CODE AUDIT MASTER AGENT ===${NC}"
echo -e "${GREEN}=== Emerald Tablet Bootstrap v1.0  ===${NC}"

AUDIT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOOLS_DIR="$AUDIT_DIR/.tools"
mkdir -p "$TOOLS_DIR" "$AUDIT_DIR/reports" "$AUDIT_DIR/config"

echo -e "\n${BLUE}[1/6] Installing reviewdog...${NC}"
command -v reviewdog &>/dev/null || {
  curl -sfL https://raw.githubusercontent.com/reviewdog/reviewdog/master/install.sh | sh -s -- -b "$TOOLS_DIR" latest
  export PATH="$TOOLS_DIR:$PATH"
}

echo -e "${BLUE}[2/6] Installing semgrep...${NC}"
pip install semgrep 2>/dev/null || pip3 install semgrep 2>/dev/null || true

echo -e "${BLUE}[3/6] Installing Python linters...${NC}"
pip install pylint flake8 bandit mypy black yamllint 2>/dev/null || true

echo -e "${BLUE}[4/6] Installing JS/TS linters...${NC}"
command -v npm &>/dev/null && npm install -g eslint typescript 2>/dev/null || true

echo -e "${BLUE}[5/6] Installing trivy...${NC}"
command -v trivy &>/dev/null || {
  curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b "$TOOLS_DIR" latest 2>/dev/null || true
}

echo -e "${BLUE}[6/6] Installing gitleaks + shellcheck...${NC}"
command -v gitleaks &>/dev/null || curl -sfL https://raw.githubusercontent.com/gitleaks/gitleaks/master/scripts/install.sh | sh -s -- -b "$TOOLS_DIR" latest 2>/dev/null || true
command -v shellcheck &>/dev/null || sudo apt-get install -y shellcheck 2>/dev/null || true

echo -e "\n${GREEN}=== SETUP COMPLETE ===${NC}"
echo -e "Tools: reviewdog, semgrep, pylint, flake8, bandit, mypy, eslint, shellcheck, trivy, gitleaks"
echo -e "${YELLOW}Run: ./audit-agent/run-audit.sh <target-dir>${NC}"
