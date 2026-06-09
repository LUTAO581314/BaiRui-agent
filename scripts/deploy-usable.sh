#!/usr/bin/env bash
set -euo pipefail

MODE="${MODE:-local}"
DOMAIN="${DOMAIN:-}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-120}"

step() {
  printf '== %s ==\n' "$1"
}

new_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 24
  else
    tr -dc 'a-f0-9' </dev/urandom | head -c 48
  fi
}

ensure_env_file() {
  if [[ ! -f .env ]]; then
    [[ -f .env.example ]] || { echo ".env.example is missing" >&2; exit 1; }
    cp .env.example .env
    chmod 600 .env || true
  fi
}

ensure_env_value() {
  local name="$1"
  local value="$2"
  if grep -qE "^${name}=" .env; then
    if grep -qE "^${name}=$" .env; then
      sed -i.bak "s|^${name}=.*$|${name}=${value}|" .env
      rm -f .env.bak
    fi
  else
    printf '%s=%s\n' "$name" "$value" >> .env
  fi
}

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose -f docker-compose.production.yml "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f docker-compose.production.yml "$@"
  else
    echo "Docker Compose is required." >&2
    exit 1
  fi
}

wait_health() {
  local url="$1"
  local deadline=$((SECONDS + TIMEOUT_SECONDS))
  until curl -fsS "$url" >/dev/null 2>&1; do
    if (( SECONDS >= deadline )); then
      echo "Hermes health check timed out: $url" >&2
      exit 1
    fi
    sleep 2
  done
}

build_frontend_if_present() {
  local frontend_dir=""
  if [[ -f frontend/package.json ]]; then
    frontend_dir="frontend"
  elif [[ -f package.json ]]; then
    frontend_dir="."
  fi

  if [[ -z "$frontend_dir" ]]; then
    step "No npm frontend detected; skipping frontend build"
    return
  fi

  (
    cd "$frontend_dir"
    local manager="npm"
    local install_cmd=("npm" "install")
    local build_cmd=("npm" "run" "build")
    if [[ -f package-lock.json ]]; then
      manager="npm"
      install_cmd=("npm" "ci")
    elif [[ -f pnpm-lock.yaml ]]; then
      manager="pnpm"
      install_cmd=("pnpm" "install" "--frozen-lockfile")
      build_cmd=("pnpm" "run" "build")
    elif [[ -f yarn.lock ]]; then
      manager="yarn"
      install_cmd=("yarn" "install" "--frozen-lockfile")
      build_cmd=("yarn" "run" "build")
    elif [[ -f bun.lockb || -f bun.lock ]]; then
      manager="bun"
      install_cmd=("bun" "install" "--frozen-lockfile")
      build_cmd=("bun" "run" "build")
    fi
    if ! command -v "$manager" >/dev/null 2>&1; then
      echo "$manager is required because ${frontend_dir} uses ${manager}." >&2
      exit 1
    fi
    step "Building frontend in ${frontend_dir} with ${manager}"
    "${install_cmd[@]}"
    "${build_cmd[@]}"
  )
}

step "Preparing usable MOXI deployment"
ensure_env_file
ensure_env_value "POSTGRES_DB" "moxi"
ensure_env_value "POSTGRES_USER" "moxi"

if ! grep -qE '^POSTGRES_PASSWORD=.+$' .env; then
  ensure_env_value "POSTGRES_PASSWORD" "$(new_secret)"
fi

ensure_env_value "HERMES_ENV" "production"
ensure_env_value "HERMES_HOST" "127.0.0.1"
ensure_env_value "HERMES_PORT" "8787"

mkdir -p data/postgres data/hermes logs/hermes obsidian-vault

if [[ "$MODE" == "domain" && -z "$DOMAIN" ]]; then
  echo "Domain mode requires DOMAIN, for example: MODE=domain DOMAIN=moxi.example.com scripts/deploy-usable.sh" >&2
  exit 1
fi

build_frontend_if_present

step "Starting PostgreSQL and Hermes"
compose up -d --build

step "Waiting for Hermes health"
wait_health "http://127.0.0.1:8787/health"

step "Deployment is usable"
printf 'Hermes health: http://127.0.0.1:8787/health\n'
printf 'Hermes ready:  http://127.0.0.1:8787/ready\n'
printf 'Capabilities:  http://127.0.0.1:8787/capabilities\n'
if [[ "$MODE" == "domain" ]]; then
  printf 'Next domain step: configure DNS, HTTPS, and Nginx for https://%s/\n' "$DOMAIN"
else
  printf 'Local production mode is active. Public callbacks remain disabled unless a reviewed gateway is configured.\n'
fi
