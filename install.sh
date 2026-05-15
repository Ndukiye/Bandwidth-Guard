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
# Data directory (with snap write access)
# -----------------------------
echo "[2/7] Creating data directory..."

mkdir -p /var/lib/bandwidth-guard

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"

# Allow user write access
chown -R "$ACTUAL_USER:$ACTUAL_USER" /var/lib/bandwidth-guard
chmod -R 755 /var/lib/bandwidth-guard

echo "✓ Data directory ready (accessible by $ACTUAL_USER)"

# -----------------------------
# Python environment
# -----------------------------
echo "[3/7] Setting up Python environment..."

python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

echo "✓ Python environment ready"

# -----------------------------
# systemd services
# -----------------------------
echo "[4/7] Installing systemd services..."

SERVICE_FILE="$INSTALL_DIR/scripts/bandwidth-guard.service"
TIMER_FILE="$INSTALL_DIR/scripts/bwguard-timer.service"

# Validate files exist
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Missing service file: $SERVICE_FILE"
    exit 1
fi

if [ ! -f "$TIMER_FILE" ]; then
    echo "❌ Missing timer file: $TIMER_FILE"
    exit 1
fi

# Install service file (proper systemd deployment)
install -Dm644 "$SERVICE_FILE" /etc/systemd/system/bandwidth-guard.service

# Install timer file (proper systemd deployment)
install -Dm644 "$TIMER_FILE" /etc/systemd/system/bwguard-timer.service

# Reload systemd so it sees new units
systemctl daemon-reload

# Enable services
systemctl enable bandwidth-guard.service
systemctl enable bwguard-timer.service

echo "✓ Service + Timer installed"

# -----------------------------
# Start daemon
# -----------------------------
echo "[5/7] Starting daemon..."

# Start service (immediate run)
systemctl start bandwidth-guard.service

# Small delay to allow initialization
sleep 2

# Check service status
if ! systemctl is-active --quiet bandwidth-guard.service; then
    echo "❌ Daemon failed to start"
    echo "Run: journalctl -u bandwidth-guard.service -n 50"
    exit 1
fi

echo "✓ Daemon running"

# Optional: verify timer is enabled
if ! systemctl is-enabled --quiet bwguard-timer.service; then
    echo "⚠️ Warning: timer is not enabled"
else
    echo "✓ Timer enabled"
fi

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
        snap install --dangerous --classic "$TMP_SNAP"
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