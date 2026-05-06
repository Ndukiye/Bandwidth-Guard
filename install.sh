#!/bin/bash
# install.sh - Install Bandwidth Guard monitoring daemon and CLI

set -e

echo "=== Bandwidth Guard Installer ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo ./install.sh"
    exit 1
fi

# Detect architecture
ARCH=$(uname -m)
case $ARCH in
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

# Install system dependencies
echo "[1/9] Installing system dependencies..."
apt-get update -qq
apt-get install -y bpftrace python3 python3-pip python3-venv snapd wget 2>/dev/null
echo "✓ Dependencies installed"

# Create data directory
echo "[2/9] Creating data directory..."
mkdir -p /var/lib/bandwidth-guard
chmod 755 /var/lib/bandwidth-guard
echo "✓ Created /var/lib/bandwidth-guard"

# Install daemon files
echo "[3/9] Installing daemon files..."
INSTALL_DIR="/opt/bandwidth-guard"
mkdir -p $INSTALL_DIR/src
mkdir -p $INSTALL_DIR/scripts

# Copy daemon source files
cp src/monitor.py $INSTALL_DIR/src/
cp src/enforcer.py $INSTALL_DIR/src/
cp src/storage.py $INSTALL_DIR/src/
cp src/config_loader.py $INSTALL_DIR/src/
cp scripts/network_tracker.bt $INSTALL_DIR/scripts/
echo "✓ Installed daemon files"

# Create virtual environment
echo "[4/9] Creating Python virtual environment..."
python3 -m venv $INSTALL_DIR/venv
$INSTALL_DIR/venv/bin/pip install -q --upgrade pip
$INSTALL_DIR/venv/bin/pip install -q -r requirements.txt
echo "✓ Virtual environment created"

# Create default config
echo "[5/9] Setting up configuration..."
if [ ! -f /var/lib/bandwidth-guard/config.yaml ]; then
    cat > /var/lib/bandwidth-guard/config.yaml << 'EOF'
global:
  daily_limit_mb: 5120
  data_plan: "Default Plan"

processes: {}

whitelist:
  - sshd
  - systemd
EOF
    echo "✓ Created default config"
else
    echo "✓ Config already exists (not overwriting)"
fi

# Initialize JSON files
echo "[6/9] Initializing data files..."
if [ ! -f /var/lib/bandwidth-guard/data.json ]; then
    echo "[]" > /var/lib/bandwidth-guard/data.json
fi
if [ ! -f /var/lib/bandwidth-guard/multi_tracker_history.json ]; then
    echo "{}" > /var/lib/bandwidth-guard/multi_tracker_history.json
fi
chmod 644 /var/lib/bandwidth-guard/*.json
chmod 644 /var/lib/bandwidth-guard/config.yaml
echo "✓ Data files initialized"

# Install systemd service
echo "[7/9] Installing systemd service..."
cat > /etc/systemd/system/bandwidth-guard.service << 'EOF'
[Unit]
Description=Bandwidth Guard - Network Usage Monitor
After=network.target
Documentation=https://github.com/Ndukiye/bandwidth-guard

[Service]
Type=simple
ExecStart=/opt/bandwidth-guard/venv/bin/python /opt/bandwidth-guard/src/monitor.py
WorkingDirectory=/opt/bandwidth-guard
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Desktop notification support
Environment="DISPLAY=:0"
Environment="DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bandwidth-guard
echo "✓ Service installed and enabled"

# Start daemon
echo "[8/9] Starting daemon..."
systemctl start bandwidth-guard
sleep 2

if ! systemctl is-active --quiet bandwidth-guard; then
    echo "⚠ Warning: Daemon failed to start"
    echo "Check logs with: journalctl -u bandwidth-guard -n 50"
    exit 1
fi
echo "✓ Daemon started successfully"

# Download and install snap
echo "[9/9] Installing CLI snap..."

# Check if snap file exists locally (for offline install)
if [ -f "bandwidth-guard_1.1_${SNAP_ARCH}.snap" ]; then
    echo "Using local snap file..."
    snap install --dangerous --classic bandwidth-guard_1.1_${SNAP_ARCH}.snap
else
    # Download from GitHub releases
    echo "Downloading latest snap from GitHub..."
    RELEASE_URL="https://github.com/Ndukiye/bandwidth-guard/releases/latest/download/bandwidth-guard_1.1_${SNAP_ARCH}.snap"
    
    if wget -q --spider "$RELEASE_URL"; then
        wget -q --show-progress "$RELEASE_URL" -O /tmp/bandwidth-guard.snap
        snap install --dangerous --classic /tmp/bandwidth-guard.snap
        rm /tmp/bandwidth-guard.snap
    else
        echo "⚠ Could not download snap from GitHub releases"
        echo "Please download manually from: https://github.com/Ndukiye/bandwidth-guard/releases"
        echo "Then run: sudo snap install bandwidth-guard_1.1_${SNAP_ARCH}.snap --dangerous --classic"
    fi
fi

# Set alias
snap alias bandwidth-guard bwguard 2>/dev/null || true
echo "✓ CLI installed"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Installation complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Daemon status:"
systemctl status bandwidth-guard --no-pager --lines=5
echo ""
echo "Test it:"
echo "  bwguard status"
echo ""
echo "Useful commands:"
echo "  • View logs: journalctl -u bandwidth-guard -f"
echo "  • Restart: sudo systemctl restart bandwidth-guard"
echo "  • Stop: sudo systemctl stop bandwidth-guard"
echo ""