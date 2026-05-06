#!/bin/bash
# install.sh - Bandwidth Guard installer (daemon + CLI)

set -euo pipefail

echo "=== Bandwidth Guard Installer ==="
echo ""

# -----------------------------
# Root check
# -----------------------------
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run with sudo"
    echo "Usage: curl -fsSL <url> | sudo bash"
    exit 1
fi

# -----------------------------
# Config
# -----------------------------
REPO="https://github.com/Ndukiye/Bandwith-Guard"
INSTALL_DIR="/opt/bandwidth-guard"

ARCH=$(uname -m)
case "$ARCH" in
    x86_64)
        SNAP_ARCH="amd64"
        ;;
    aarch64)
        SNAP_ARCH="arm64"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# -----------------------------
# Clone repo (CRITICAL FIX)
# -----------------------------
echo "[0/9] Cloning repository..."
rm -rf "$INSTALL_DIR"
git clone "$REPO" "$INSTALL_DIR"
cd "$INSTALL_DIR"

# -----------------------------
# Dependencies
# -----------------------------
echo "[1/9] Installing system dependencies..."
apt-get update -qq
apt-get install -y bpftrace python3 python3-pip python3-venv snapd wget git >/dev/null
echo "✓ Dependencies installed"

# -----------------------------
# Data directory
# -----------------------------
echo "[2/9] Creating data directory..."
mkdir -p /var/lib/bandwidth-guard
chmod 755 /var/lib/bandwidth-guard
echo "✓ Data directory ready"

# -----------------------------
# Install daemon files
# -----------------------------
echo "[3/9] Installing daemon files..."

INSTALL_DIR="/opt/bandwidth-guard"

mkdir -p "$INSTALL_DIR/src"
mkdir -p "$INSTALL_DIR/scripts"

cp -r src/* "$INSTALL_DIR/src/"
cp -r scripts/* "$INSTALL_DIR/scripts/"

echo "✓ Daemon files installed"

# -----------------------------
# Python environment
# -----------------------------
echo "[4/9] Creating Python environment..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install -q --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -q -r requirements.txt
echo "✓ Python environment ready"

# -----------------------------
# Config
# -----------------------------
echo "[5/9] Setting up configuration..."

cat > /var/lib/bandwidth-guard/config.yaml << 'EOF'
global:
  daily_limit_mb: 5120
  data_plan: "Default Plan"

processes: {}

whitelist:
  - sshd
  - systemd
EOF

echo "✓ Config created"

# -----------------------------
# Data files
# -----------------------------
echo "[6/9] Initializing data files..."

echo "[]" > /var/lib/bandwidth-guard/data.json
echo "{}" > /var/lib/bandwidth-guard/multi_tracker_history.json

chmod 644 /var/lib/bandwidth-guard/*.json
chmod 644 /var/lib/bandwidth-guard/config.yaml

echo "✓ Data initialized"

# -----------------------------
# systemd service
# -----------------------------
echo "[7/9] Installing systemd service..."

cat > /etc/systemd/system/bandwidth-guard.service << EOF
[Unit]
Description=Bandwidth Guard - Network Usage Monitor
After=network.target
Documentation=$REPO

[Service]
Type=simple
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/src/monitor.py
WorkingDirectory=$INSTALL_DIR
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

Environment="DISPLAY=:0"
Environment="DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bandwidth-guard
echo "✓ Service installed"

# -----------------------------
# Start daemon
# -----------------------------
echo "[8/9] Starting daemon..."

systemctl start bandwidth-guard
sleep 2

if ! systemctl is-active --quiet bandwidth-guard; then
    echo "⚠ Daemon failed to start"
    echo "Check logs: journalctl -u bandwidth-guard -n 50"
    exit 1
fi

echo "✓ Daemon running"

# -----------------------------
# Snap CLI install (fixed)
# -----------------------------
echo "[9/9] Installing CLI snap..."

SNAP_NAME="bandwidth-guard_1.1_${SNAP_ARCH}.snap"
RELEASE_URL="https://github.com/Ndukiye/Bandwith-Guard/releases/latest/download/$SNAP_NAME"

TMP_SNAP="/tmp/bandwidth-guard.snap"

if wget -q --spider "$RELEASE_URL"; then
    echo "Downloading CLI snap..."
    wget -q --show-progress "$RELEASE_URL" -O "$TMP_SNAP"
    snap install --dangerous "$TMP_SNAP"
    rm -f "$TMP_SNAP"
else
    echo "⚠ Could not download snap from GitHub Releases"
    echo "Manual install:"
    echo "$RELEASE_URL"
fi

snap alias bandwidth-guard bwguard 2>/dev/null || true
echo "✓ CLI installed"

# -----------------------------
# Done
# -----------------------------
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Installation complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Test command:"
echo "  bwguard status"
echo ""

echo "Useful commands:"
echo "  journalctl -u bandwidth-guard -f"
echo "  sudo systemctl restart bandwidth-guard"
echo "  sudo systemctl stop bandwidth-guard"
echo ""