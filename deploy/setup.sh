#!/usr/bin/env bash
# ==============================================================================
# Idempotent Setup & Deploy Script for Debian LXC (Proxmox)
# ==============================================================================
set -euo pipefail

APP_DIR="/opt/packing-app"
DATA_DIR="${APP_DIR}/data"
CONFIG_DIR="/etc/packing-list"
ENV_FILE="${CONFIG_DIR}/packing-list.env"
SERVICE_NAME="packing-list.service"
APP_USER="packing"
APP_GROUP="packing"

echo "=== [1/6] Installing OS dependencies ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
    python3 \
    python3-venv \
    python3-pip \
    sqlite3 \
    curl \
    ca-certificates

echo "=== [2/6] Creating service user and directories ==="
if ! id -u "${APP_USER}" >/dev/null 2>&1; then
    useradd --system --shell /usr/sbin/nologin --home-dir "${APP_DIR}" "${APP_USER}"
fi

mkdir -p "${APP_DIR}"
mkdir -p "${DATA_DIR}"
mkdir -p "${CONFIG_DIR}"

chown -R "${APP_USER}:${APP_GROUP}" "${APP_DIR}"
chown -R "${APP_USER}:${APP_GROUP}" "${DATA_DIR}"
chmod 750 "${DATA_DIR}"

echo "=== [3/6] Setting up Python virtual environment ==="
if [ ! -d "${APP_DIR}/.venv" ]; then
    python3 -m venv "${APP_DIR}/.venv"
fi

# Ensure pip & runtime dependencies are up to date
"${APP_DIR}/.venv/bin/python" -m pip install -q --upgrade pip
"${APP_DIR}/.venv/bin/python" -m pip install -q -r "${APP_DIR}/requirements.txt"

echo "=== [4/6] Configuring environment ==="
if [ ! -f "${ENV_FILE}" ]; then
    cp "${APP_DIR}/deploy/env.example" "${ENV_FILE}"
    echo "Created default config at ${ENV_FILE}"
fi

echo "=== [5/6] Installing systemd service unit ==="
cp "${APP_DIR}/deploy/${SERVICE_NAME}" "/etc/systemd/system/${SERVICE_NAME}"
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

echo "=== [6/6] Verifying service health ==="
sleep 2
if curl -s -f "http://127.0.0.1:8000/api/health" >/dev/null 2>&1; then
    echo "=========================================================="
    echo " Family Packing App is running successfully! 🚀"
    echo " Access the app at: http://<container-ip>:8000"
    echo " Logs: journalctl -u ${SERVICE_NAME} -f"
    echo "=========================================================="
else
    echo "Service started, but health check failed. Checking logs:"
    journalctl -u "${SERVICE_NAME}" -n 20 --no-pager
    exit 1
fi
