# Installation Guide

Bandwidth Guard requires two components:
1. **Monitoring daemon** (runs as systemd service with root)
2. **CLI tool** (snap package)

## Quick Install (Recommended)

```bash
# One-line installer
curl -fsSL https://raw.githubusercontent.com/Ndukiye/bandwidth-guard/main/install.sh | sudo bash
```

This script automatically:
- Installs the monitoring daemon
- Downloads and installs the CLI snap from GitHub Releases
- Configures everything

---

## Manual Installation

### Step 1: Download Latest Release

```bash
# Download installer package
wget https://github.com/Ndukiye/bandwidth-guard/releases/latest/download/bandwidth-guard-installer.tar.gz

# Extract
tar -xzf bandwidth-guard-installer.tar.gz
cd bandwidth-guard
```

### Step 2: Run Installer

```bash
sudo ./install.sh
```

**What this does:**
- Installs bpftrace and Python dependencies
- Copies daemon files to `/opt/bandwidth-guard/`
- Creates data directory at `/var/lib/bandwidth-guard/`
- Installs and starts systemd service
- Downloads and installs CLI snap from GitHub Releases
- Sets up `bwguard` alias

**Verify it's running:**
```bash
systemctl status bandwidth-guard
```

### Step 3: Test

```bash
bwguard status
```

---

## System Requirements

- Ubuntu 20.04+ (or any Linux with kernel 5.2+)
- bpftrace 0.18+
- Python 3.8+
- Root/sudo access (for eBPF)
- snapd installed

---

## First-Time Setup

Configure your data plan:
```bash
bwguard configure-plan
# Enter: "MTN 5GB Daily"
# Enter: 5120 (MB)
```

Set a process limit:
```bash
bwguard set-limit firefox 2048
```

View current usage:
```bash
bwguard status
```

---

## Offline Installation

If you don't have internet access on the target machine:

```bash
# 1. Download on a machine with internet
wget https://github.com/Ndukiye/bandwidth-guard/releases/latest/download/bandwidth-guard-installer.tar.gz

# 2. Transfer to target machine via USB/SCP

# 3. Extract and install
tar -xzf bandwidth-guard-installer.tar.gz
cd bandwidth-guard
sudo ./install.sh
```

The installer will use the local snap file if available.

---

## Troubleshooting

**"Command 'bwguard' not found"**

The snap installed successfully but alias wasn't set:
```bash
sudo snap alias bandwidth-guard bwguard
```

**"No data tracked today yet"**

The daemon isn't running or just started:
```bash
# Check daemon status
systemctl status bandwidth-guard

# View daemon logs
journalctl -u bandwidth-guard -f

# Restart daemon
sudo systemctl restart bandwidth-guard
```

**"Snap download failed"**

Download manually:
```bash
# Download snap for your architecture
wget https://github.com/Ndukiye/bandwidth-guard/releases/latest/download/bandwidth-guard_1.1_amd64.snap

# Install
sudo snap install bandwidth-guard_1.1_amd64.snap --dangerous --classic

# Set alias
sudo snap alias bandwidth-guard bwguard
```

**Desktop notifications not showing**

This is a known limitation when the daemon runs as a systemd service. Enforcement (killing processes) still works. Notifications will be logged to journalctl instead.

---

## Uninstall

```bash
# Stop and remove daemon
sudo systemctl stop bandwidth-guard
sudo systemctl disable bandwidth-guard
sudo rm /etc/systemd/system/bandwidth-guard.service
sudo rm -rf /opt/bandwidth-guard
sudo systemctl daemon-reload

# Remove data (optional)
sudo rm -rf /var/lib/bandwidth-guard

# Remove snap
sudo snap remove bandwidth-guard
```

---

## WSL2 (Windows Users)

Bandwidth Guard works in WSL2 with Ubuntu:

1. Install WSL2: `wsl --install -d Ubuntu`
2. Inside WSL2: Run the one-line installer
3. Test: `bwguard status`

---

## Getting Help

- **View logs:** `journalctl -u bandwidth-guard -f`
- **Check daemon status:** `systemctl status bandwidth-guard`
- **Report issues:** https://github.com/Ndukiye/bandwidth-guard/issues