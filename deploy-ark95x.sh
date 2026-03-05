#!/usr/bin/env bash
# ARK95X Unified Sovereign Stack - Linux Bash Deployment Script
# Repo: Ark95x-sAn/ark95x-unified-sovereign-stack
# Stack: Python 3.11, Node.js, Ollama, Redis, PostgreSQL, MongoDB, Qdrant, FastAPI, CrewAI, n8n

set -euo pipefail
IFS=$'\n\t'

readonly INSTALL_DIR="${INSTALL_DIR:-/opt/ark95x}"
readonly LOG_DIR="${LOG_DIR:-/var/log/ark95x}"
readonly LOG_FILE="${LOG_DIR}/deploy-$(date +%Y%m%d-%H%M%S).log"
readonly BACKUP_DIR="${BACKUP_DIR:-/var/backups/ark95x}"
readonly REPO_URL="https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack.git"
readonly SERVICE_NAME="ark95x-stack"
readonly COMPOSE_PROJECT="ark95x"
readonly HEALTH_TIMEOUT=300
readonly HEALTH_INTERVAL=5
readonly OLLAMA_MODELS=("llama3" "deepseek-r1" "codellama")

declare -A SVC_ENDPOINTS=(
  [core]="http://localhost:8000/health"
  [postgres]="localhost:5432"
  [redis]="localhost:6379"
  [mongodb]="localhost:27017"
  [qdrant]="http://localhost:6333"
  [n8n]="http://localhost:5678"
  [ollama]="http://localhost:11434/api/tags"
)

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

mkdir -p "$LOG_DIR" "$BACKUP_DIR"

log()     { echo -e "$(date '+%Y-%m-%d %H:%M:%S') [$1] ${*:2}" | tee -a "$LOG_FILE"; }
info()    { log INFO    "${BLUE}i${RESET} $*"; }
ok()      { log OK      "${GREEN}v${RESET} $*"; }
warn()    { log WARN    "${YELLOW}!${RESET} $*"; }
err()     { log ERROR   "${RED}x${RESET} $*"; }
section() { echo; log '---' "${CYAN}=== $1 ===${RESET}"; }

cleanup() {
  local code=$?
  [[ $code -ne 0 ]] && { err "Failed (exit $code)"; rollback; }
  info "Cleanup complete"
}
trap cleanup EXIT ERR INT TERM

rollback() {
  section "Rollback"
  cd "$INSTALL_DIR" 2>/dev/null || true
  docker-compose -p "$COMPOSE_PROJECT" down 2>/dev/null || true
  local latest; latest=$(ls -t "$BACKUP_DIR" 2>/dev/null | head -n1)
  if [[ -n "$latest" ]]; then
    rm -rf "${INSTALL_DIR:?}"/*
    tar -xzf "$BACKUP_DIR/$latest" -C "$INSTALL_DIR"
    docker-compose -p "$COMPOSE_PROJECT" up -d
    ok "Rolled back: $latest"
  else
    err "No backup found for rollback"
  fi
}

check_prereqs() {
  section "Prerequisites"
  [[ "$EUID" -ne 0 ]] && { err "Must run as root"; exit 1; }
  local missing=()
  for cmd in docker docker-compose git curl jq nc openssl; do
    command -v "$cmd" &>/dev/null && ok "$cmd" || missing+=("$cmd")
  done
  [[ ${#missing[@]} -gt 0 ]] && { err "Missing: ${missing[*]}"; exit 1; }
  docker info &>/dev/null || { err "Docker not running"; exit 1; }
  local space; space=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
  [[ "$space" -lt 10 ]] && warn "Low disk: ${space}GB" || ok "Disk: ${space}GB free"
  ok "All prerequisites OK"
}

setup_dirs() {
  section "Directories"
  for d in "$INSTALL_DIR" "$LOG_DIR" "$BACKUP_DIR"; do
    mkdir -p "$d" && ok "$d"
  done
  chmod 755 "$INSTALL_DIR" "$LOG_DIR"; chmod 700 "$BACKUP_DIR"
}

backup_existing() {
  section "Backup"
  if [[ -d "$INSTALL_DIR" && -n "$(ls -A "$INSTALL_DIR" 2>/dev/null)" ]]; then
    local bf="$BACKUP_DIR/ark95x-bak-$(date +%Y%m%d-%H%M%S).tar.gz"
    tar -czf "$bf" -C "$INSTALL_DIR" . 2>/dev/null || true
    [[ -f "$bf" ]] && ok "Backup: $bf"
    ls -t "$BACKUP_DIR"/ark95x-bak-*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f || true
  else
    info "Nothing to backup"
  fi
}

clone_repo() {
  section "Repository"
  if [[ -d "$INSTALL_DIR/.git" ]]; then
    cd "$INSTALL_DIR"
    git stash save "auto-$(date +%s)" 2>/dev/null || true
    git fetch origin && git reset --hard origin/main
    ok "Updated: $(git rev-parse --short HEAD)"
  else
    rm -rf "${INSTALL_DIR:?}/"*
    git clone "$REPO_URL" "$INSTALL_DIR" && cd "$INSTALL_DIR"
    ok "Cloned: $(git rev-parse --short HEAD)"
  fi
}

gen_env() {
  section "Environment"
  cd "$INSTALL_DIR"
  [[ -f .env ]] && cp .env ".env.bak.$(date +%s)"
  local pgp; pgp=$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-25)
  local n8k; n8k=$(openssl rand -hex 32)
  cat > .env <<-ENV
OPENAI_API_KEY=${OPENAI_API_KEY:-sk-your-key-here}
OLLAMA_HOST=http://localhost:11434
POSTGRES_PASSWORD=${pgp}
POSTGRES_URL=postgresql://ark95x:${pgp}@postgres:5432/sovereign
MONGODB_URL=mongodb://mongodb:27017/ark95x
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
N8N_URL=http://n8n:5678
N8N_API_KEY=${n8k}
TRADING_MODE=paper
APP_ENV=production
APP_PORT=8000
LOG_LEVEL=INFO
	ENV
  chmod 600 .env
  ok ".env written"
}

setup_ollama() {
  section "Ollama"
  if ! command -v ollama &>/dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
    systemctl enable --now ollama
  fi
  local r=0
  until curl -s http://localhost:11434/api/tags &>/dev/null; do
    sleep 2; ((r++)); [[ $r -gt 30 ]] && { err "Ollama timeout"; return 1; }
  done
  ok "Ollama ready"
  for m in "${OLLAMA_MODELS[@]}"; do
    ollama list | grep -q "^${m}" || ollama pull "$m"
    ok "Model: $m"
  done
}

deploy_stack() {
  section "Docker Deploy"
  cd "$INSTALL_DIR"
  docker-compose -p "$COMPOSE_PROJECT" build --no-cache 2>&1 | tee -a "$LOG_FILE"
  docker-compose -p "$COMPOSE_PROJECT" up -d 2>&1 | tee -a "$LOG_FILE"
  ok "Stack deployed"
  docker-compose -p "$COMPOSE_PROJECT" ps
}

health_checks() {
  section "Health Checks"
  local t0; t0=$(date +%s)
  local ok_flag=false
  while [[ $ok_flag == false ]]; do
    ok_flag=true
    for svc in "${!SVC_ENDPOINTS[@]}"; do
      local ep="${SVC_ENDPOINTS[$svc]}"
      if [[ "$ep" =~ ^http ]]; then
        curl -sf "$ep" &>/dev/null && ok "$svc up" || { warn "$svc waiting"; ok_flag=false; }
      else
        nc -z "${ep%%:*}" "${ep##*:}" &>/dev/null && ok "$svc up" || { warn "$svc waiting"; ok_flag=false; }
      fi
    done
    if [[ $ok_flag == false ]]; then
      [[ $(($(date +%s)-t0)) -gt $HEALTH_TIMEOUT ]] && { err "Health timeout"; return 1; }
      sleep "$HEALTH_INTERVAL"
    fi
  done
  ok "All services healthy"
}

gen_systemd() {
  section "Systemd"
  cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<-SVC
[Unit]
Description=ARK95X Unified Sovereign Stack
After=docker.service
Requires=docker.service
[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/docker-compose -p ${COMPOSE_PROJECT} up -d
ExecStop=/usr/bin/docker-compose -p ${COMPOSE_PROJECT} down
Restart=on-failure
RestartSec=10s
[Install]
WantedBy=multi-user.target
	SVC
  systemctl daemon-reload && systemctl enable "$SERVICE_NAME"
  ok "Service enabled: $SERVICE_NAME"
}

dashboard() {
  section "Status Dashboard"
  echo -e "\n${BOLD}ARK95X Sovereign Stack${RESET}\nInstall: ${GREEN}${INSTALL_DIR}${RESET}\nLog: ${LOG_FILE}\n"
  echo "Endpoints:"
  echo "  Core API  : http://localhost:8000"
  echo "  n8n       : http://localhost:5678"
  echo "  Qdrant    : http://localhost:6333"
  echo "  Ollama    : http://localhost:11434"
  echo "  PostgreSQL: localhost:5432"
  echo "  Redis     : localhost:6379"
  echo "  MongoDB   : localhost:27017"
  echo -e "\nContainers:"
  docker-compose -p "$COMPOSE_PROJECT" ps 2>/dev/null || true
  echo -e "\nOllama Models:"
  ollama list 2>/dev/null || true
  echo -e "\nService: sudo systemctl {start|stop|restart|status} $SERVICE_NAME"
  echo -e "\n${GREEN}${BOLD}Deployment complete!${RESET}\n"
}

main() {
  info "ARK95X Deployment - $(date '+%Y-%m-%d %H:%M:%S') on $(hostname)"
  check_prereqs
  setup_dirs
  backup_existing
  clone_repo
  gen_env
  setup_ollama
  deploy_stack
  health_checks
  gen_systemd
  dashboard
  ok "Total time: $(($(date +%s) - $(date -r "$LOG_FILE" +%s 2>/dev/null || echo 0)))s"
}

main "$@"
