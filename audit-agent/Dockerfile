# ARK95X Emerald Tablet - Code Audit Master Agent
# Containerized audit engine with all tools pre-installed
FROM python:3.12-slim

LABEL maintainer="Ark95x-sAn"
LABEL description="Emerald Tablet Code Audit Master Agent"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git shellcheck npm nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python audit tools
RUN pip install --no-cache-dir \
    pylint flake8 bandit mypy black yamllint semgrep requests

# Install JS/TS tools
RUN npm install -g eslint typescript

# Install reviewdog
RUN curl -sfL https://raw.githubusercontent.com/reviewdog/reviewdog/master/install.sh | sh -s -- -b /usr/local/bin latest

# Install trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin latest

# Install gitleaks
RUN curl -sfL https://raw.githubusercontent.com/gitleaks/gitleaks/master/scripts/install.sh | sh -s -- -b /usr/local/bin latest || true

WORKDIR /audit-agent

COPY . /audit-agent/

RUN chmod +x setup.sh run-audit.sh

ENV OLLAMA_URL=http://host.docker.internal:11434
ENV OLLAMA_MODEL=deepseek-r1:8b

ENTRYPOINT ["python", "audit_agent.py"]
CMD ["/workspace"]
