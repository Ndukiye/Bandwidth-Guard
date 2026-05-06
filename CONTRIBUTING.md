# Developer Guide

## Local Development Setup

### Prerequisites

- Ubuntu 20.04+ or WSL2
- Python 3.8+
- bpftrace 0.18+
- Root/sudo access

### Setup

```bash
# 1. Clone repo
git clone https://github.com/yourusername/bandwidth-guard
cd bandwidth-guard

# 2. Install dependencies
sudo apt install bpftrace
pip3 install -r requirements.txt

# 3. Create local data directory
mkdir -p storage
```

### Running Locally (Without Installing)

**Terminal 1 - Start monitor daemon:**
```bash
sudo python3 src/monitor.py
```

**Terminal 2 - Use CLI:**
```bash
python3 src/main.py status
python3 src/main.py set-limit firefox 2048
python3 src/main.py history --days 7
```

**Interactive menu:**
```bash
python3 src/main.py
```

---

## Project Structure
bandwidth-guard/
├── src/
│   ├── main.py           # CLI entry point
│   ├── cli.py            # Display/UI functions
│   ├── monitor.py        # Daemon (eBPF tracking + enforcement)
│   ├── enforcer.py       # Limit enforcement logic
│   ├── storage.py        # Data persistence (JSON)
│   └── config_loader.py  # YAML config management
│
├── scripts/
│   ├── network_tracker.bt         # bpftrace eBPF script
│   └── bandwidth-guard.service    # systemd service file
│
├── install.sh            # Daemon installer
├── snapcraft.yaml        # Snap packaging config
└── requirements.txt      # Python dependencies

---

## Data Flow
┌─────────────────────────────────────────┐
│  monitor.py (runs as systemd daemon)    │
│  ├─ Runs bpftrace script                │
│  ├─ Aggregates network stats            │
│  ├─ Enforces limits                     │
│  └─ Writes to /var/lib/bandwidth-guard/ │
└────────────┬────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│  /var/lib/bandwidth-guard/              │
│  ├── config.yaml                        │
│  ├── data.json                          │
│  └── multi_tracker_history.json         │
└────────────▲────────────────────────────┘
│
┌────────────┴────────────────────────────┐
│  main.py (CLI - can be snap or local)   │
│  ├─ Reads config.yaml                   │
│  ├─ Reads JSON data                     │
│  ├─ Displays status                     │
│  └─ Writes config changes               │
└─────────────────────────────────────────┘

---

## Building the Snap

```bash
# Clean previous builds
snapcraft clean

# Build
snapcraft pack

# Install locally
sudo snap install bandwidth-guard_1.0_amd64.snap --dangerous --classic

# Test
bandwidth-guard status
```

---

## Testing

### Manual Testing Checklist

- [ ] Daemon starts and runs: `systemctl status bandwidth-guard`
- [ ] eBPF tracking works: Generate traffic, check `bwguard status`
- [ ] Limits enforcement: Set low limit, exceed it, verify kill/warn
- [ ] Desktop notifications: Check if visible (may fail in systemd)
- [ ] CLI commands: Test all commands (status, history, set-limit, etc.)
- [ ] Config persistence: Set limit, restart daemon, verify it persists
- [ ] Daily reset: Change system date, verify data resets

### Generating Test Traffic

```bash
# Download large file
wget https://releases.ubuntu.com/22.04/ubuntu-22.04.3-desktop-amd64.iso

# Stream video (Firefox)
# Open YouTube and play a video

# Continuous traffic
while true; do curl https://example.com; sleep 1; done
```

---

## Code Style

- **Formatting:** Follow PEP 8
- **Docstrings:** Add to all functions
- **Comments:** Explain complex logic (especially eBPF parsing)
- **Error handling:** Always use try/except for file I/O, subprocess calls

---

## Publishing to Snap Store

```bash
# 1. Login
snapcraft login

# 2. Upload
snapcraft upload bandwidth-guard_1.0_amd64.snap --release=edge

# 3. Test from edge channel
sudo snap install bandwidth-guard --edge --classic

# 4. Promote to stable
snapcraft promote bandwidth-guard --from-channel=edge --to-channel=stable
```

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test locally (both daemon and CLI)
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

---

## Known Issues

- Desktop notifications don't work when daemon runs as systemd service (no display session)
- WSL2 requires running X server for GUI notifications
- tc (traffic control) throttling not yet implemented (roadmap item)

---

## Roadmap

- [ ] Web dashboard (Flask + React)
- [ ] Email/Slack alerts
- [ ] Traffic control (tc) integration for throttling
- [ ] Docker container support
- [ ] macOS support (if eBPF becomes available)