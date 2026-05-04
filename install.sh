#!/bin/bash
# install.sh - Install Bandwidth Guard monitoring daemon

set -e

echo "=== Bandwidth Guard Daemon Installer ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo ./install.sh"
    exit 1
fi

# Check if bpftrace is available
echo "[1/7] Checking dependencies..."
if ! command -v bpftrace &> /dev/null; then
    echo "Installing bpftrace..."
    apt-get update
    apt-get install -y bpftrace
else
    echo "✓ bpftrace already installed"
fi

# Install Python dependencies
echo "[2/7] Installing Python dependencies..."
python3 -m venv /opt/bandwidth-guard/venv
/opt/bandwidth-guard/venv/bin/pip install -r requirements.txt

# Create data directory
echo "[3/7] Creating data directory..."
mkdir -p /var/lib/bandwidth-guard
chmod 755 /var/lib/bandwidth-guard
echo "✓ Created /var/lib/bandwidth-guard"

# Install daemon files
echo "[4/7] Installing daemon files..."
INSTALL_DIR="/opt/bandwidth-guard"
mkdir -p $INSTALL_DIR/src
mkdir -p $INSTALL_DIR/scripts

# Copy daemon source files
cp src/monitor.py $INSTALL_DIR/src/
cp src/enforcer.py $INSTALL_DIR/src/
cp src/storage.py $INSTALL_DIR/src/
cp src/config_loader.py $INSTALL_DIR/src/
cp scripts/network_tracker.bt $INSTALL_DIR/scripts/

echo "✓ Installed to $INSTALL_DIR"

# Create default config
echo "[5/7] Setting up configuration..."
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

# Install systemd service
echo "[6/7] Installing systemd service..."
cp scripts/bandwidth-guard.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable bandwidth-guard
echo "✓ Service installed and enabled"

# Start service
echo "[7/7] Starting daemon..."
systemctl start bandwidth-guard
sleep 2

# Check status
if systemctl is-active --quiet bandwidth-guard; then
    echo "✓ Daemon started successfully"
else
    echo "⚠ Warning: Daemon failed to start"
    echo "Check logs: journalctl -u bandwidth-guard -n 50"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Installation complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Status:"
systemctl status bandwidth-guard --no-pager --lines=5
echo ""
echo "Next steps:"
echo "  1. Install CLI snap: sudo snap install bandwidth-guard --classic"
echo "  2. View usage: bwguard status"
echo "  3. Set limits: bwguard set-limit firefox 2048"
echo ""
echo "Useful commands:"
echo "  • View logs: journalctl -u bandwidth-guard -f"
echo "  • Restart: sudo systemctl restart bandwidth-guard"
echo "  • Stop: sudo systemctl stop bandwidth-guard"
echo ""