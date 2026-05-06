#!/bin/bash
# Bandwidth Guard Installer (daemon + CLI)

set -euo pipefail

echo "=== Bandwidth Guard Installer ==="
echo ""

# -----------------------------
# Root check
# -----------------------------
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Run with sudo"
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
# Clone repo (single source of truth)
# -----------------------------
echo "[0/7] Cloning repository..."

rm -rf "$INSTALL_DIR"
git clone "$REPO" "$INSTALL_DIR"
cd "$INSTALL_DIR"

# -----------------------------
# Dependencies
# -----------------------------
echo "[1/7] Installing dependencies..."

apt-get update -qq
apt-get install -y \
    bpftrace \
    python3 \
    python3-pip \
    python3-venv \
    snapd \
    wget \
    git >/dev/null

echo "✓ Dependencies installed"

# -----------------------------
# Data directory
# -----------------------------
echo "[2/7] Creating data directory..."

mkdir -p /var/lib/bandwidth-guard
chmod 755 /var/lib/bandwidth-guard

echo "✓ Data directory ready"

# -----------------------------
# Python environment
# -----------------------------
echo "[3/7] Setting up Python environment..."

python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

echo "✓ Python environment ready"

# -----------------------------
# systemd service
# -----------------------------
echo "[4/7] Installing systemd service..."

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
echo "[5/7] Starting daemon..."

systemctl start bandwidth-guard
sleep 2

if ! systemctl is-active --quiet bandwidth-guard; then
    echo "❌ Daemon failed to start"
    echo "Run: journalctl -u bandwidth-guard -n 50"
    exit 1
fi

echo "✓ Daemon running"

# -----------------------------
# CLI install (Snap)
# -----------------------------
echo "[6/7] Installing CLI snap..."

SNAP_NAME="bandwidth-guard_1.1_${SNAP_ARCH}.snap"
RELEASE_URL="https://github.com/Ndukiye/Bandwith-Guard/releases/latest/download/$SNAP_NAME"

TMP_SNAP="/tmp/bandwidth-guard.snap"

echo "Downloading CLI from GitHub releases..."

if wget -O "$TMP_SNAP" "$RELEASE_URL"; then
    if [ -s "$TMP_SNAP" ]; then
        snap install --dangerous "$TMP_SNAP"
        echo "✓ Snap installed"
    else
        echo "❌ Snap download empty"
        exit 1
    fi
else
    echo "❌ Failed to download snap"
    echo "Install manually:"
    echo "$RELEASE_URL"
fi

# -----------------------------
# Alias
# -----------------------------
snap alias bandwidth-guard bwguard 2>/dev/null || true

# -----------------------------
# Done
# -----------------------------
echo "[7/7] Finalizing..."

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Bandwidth Guard Installed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Test:"
echo "  bwguard status"
echo ""

echo "Logs:"
echo "  journalctl -u bandwidth-guard -f"
echo ""