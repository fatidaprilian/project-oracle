#!/usr/bin/env bash
set -euo pipefail

APP_USER="oracle"
APP_DIR="/opt/project-oracle"
REPO_URL="${REPO_URL:-https://github.com/fatidaprilian/project-oracle.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"

if ! id -u "$APP_USER" >/dev/null 2>&1; then
  sudo useradd --create-home --shell /bin/bash "$APP_USER"
fi

sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip

if [ ! -d "$APP_DIR/.git" ]; then
  sudo mkdir -p "$APP_DIR"
  sudo chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
  sudo -u "$APP_USER" git clone --branch "$REPO_BRANCH" "$REPO_URL" "$APP_DIR"
else
  sudo -u "$APP_USER" git -C "$APP_DIR" fetch --all
  sudo -u "$APP_USER" git -C "$APP_DIR" checkout "$REPO_BRANCH"
  sudo -u "$APP_USER" git -C "$APP_DIR" pull --ff-only
fi

sudo -u "$APP_USER" python3 -m venv "$APP_DIR/.venv"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

if [ ! -f "$APP_DIR/.env" ]; then
  sudo -u "$APP_USER" cp "$APP_DIR/.env.example" "$APP_DIR/.env"
fi

sudo cp "$APP_DIR/scripts/gcp/oracle-api.service" /etc/systemd/system/oracle-api.service
sudo cp "$APP_DIR/scripts/gcp/oracle-scheduler.service" /etc/systemd/system/oracle-scheduler.service

sudo systemctl daemon-reload
sudo systemctl enable oracle-api.service oracle-scheduler.service
sudo systemctl restart oracle-api.service oracle-scheduler.service

echo "Bootstrap complete"
sudo systemctl --no-pager --full status oracle-api.service || true
sudo systemctl --no-pager --full status oracle-scheduler.service || true
