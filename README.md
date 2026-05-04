# Bandwidth Guardian

Monitor and enforce per-process network bandwidth limits on Linux using eBPF.

![Bandwidth Guardian Demo](demo.png)

## What It Does

- **Real-time tracking**: See which apps are eating your bandwidth
- **Smart enforcement**: Set limits per app (kill or warn when exceeded)  
- **eBPF-powered**: Kernel-level monitoring with minimal overhead
- **Desktop notifications**: Get alerts at 80% and 100% usage
- **History reports**: View usage over days/weeks
- **Auto-reset**: Daily limits reset at midnight

## Quick Start

### Install via Snap (Easiest)

```bash
sudo snap install bandwidth-guard --classic
bandwidth-guard status
```

### Install from Source

```bash
# 1. Clone
git clone https://github.com/yourusername/bandwidth-guard
cd bandwidth-guard

# 2. Install dependencies
sudo apt install bpftrace python3-pip
pip3 install -r requirements.txt

# 3. Start monitoring
sudo python3 monitor.py &

# 4. View status
python3 main.py status
```

## Usage

### Interactive Menu

```bash
python3 main.py
```

Shows:
1. View Status (system + per-process usage)
2. View History (last 7/30 days)  
3. Set Limit (e.g., firefox: 2GB/day)
4. Configure Data Plan
5. Manage Limits

### CLI Commands

```bash
# Check today's usage
python3 main.py status

# View last 30 days
python3 main.py history --days 30

# Set Firefox limit (2GB, kill when exceeded)
python3 main.py set-limit firefox 2048

# Set Spotify limit (500MB, warn only)
python3 main.py set-limit spotify 500 --action warn

# List all limits
python3 main.py limits

# Remove a limit for a specifc process (firefox)
python3 main.py remove-limit firefox

# Remove all limits
python3 main.py clear-limit

# Configure user presets (data plan and daily usage limit)
python3 main.py configure-plan firefox
```

## How It Works

1. **eBPF hooks** (`bpftrace`) capture network events at kernel level
2. **monitor.py** aggregates data by process name (handles parent/child processes)
3. **enforcer.py** checks limits every update and takes action (warn/kill)
4. **Desktop notifications** alert you at 80% and 100% thresholds
5. **History** stored in JSON by date for reports

### Why eBPF?

- **Accurate**: Tracks at kernel level (can't be bypassed)
- **Fast**: No userspace polling overhead  
- **Per-process**: Knows which app used bandwidth, not just totals

## Configuration

Edit `config.yaml`:

```yaml
global:
  daily_limit_mb: 5120  # 5GB system-wide limit
  data_plan: "Home Fiber 100GB Monthly"

processes:
  firefox:
    limit_mb: 2048   # 2GB
    action: kill     # or "warn"
  
  spotify:
    limit_mb: 500
    action: warn

whitelist:
  - sshd    # Never enforce on these
  - systemd
```

## Systemd Service (Auto-start on Boot)

```bash
# 1. Edit service file paths
nano bandwidth-guardian.service

# 2. Install
sudo cp bandwidth-guardian.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bandwidth-guardian

# 3. Check status
sudo systemctl status bandwidth-guardian
```

## Platform Support

- ✅ **Ubuntu 20.04+** (tested)
- ✅ **Debian/Fedora/Arch** (should work)
- ✅ **WSL2** (Windows users can run in Ubuntu WSL)
- ❌ **macOS/Windows native** (eBPF is Linux-only)

## Requirements

- Linux kernel 5.2+ (for eBPF)
- bpftrace 0.18+
- Python 3.8+
- Root access (for eBPF)

## Troubleshooting

**"bpftrace not found"**
```bash
sudo apt install bpftrace
```

**"Permission denied"**
```bash
# Run monitor with sudo
sudo python3 monitor.py
```

**"No data tracked"**
```bash
# Check if monitor is running
ps aux | grep monitor.py

# Start it
sudo python3 monitor.py &
```

## Project Structure
bandwidth-guard/
├── src/
│   ├── main.py                  # CLI entry point
│   ├── monitor.py               # Background tracking daemon
│   ├── enforcer.py             # Limit enforcement logic
│   ├── cli.py                  # CLI command implementations
│   ├── storage.py              # Data persistence
│   └── config_loader.py        # Config management
│
├── scripts/
│   ├── bandwidth-guard.service # systemd file for running monitor.py      
│   └── network_tracker.bt      # eBPF/bpftrace script
│
├── storage/
│   ├── data.json               # System-wide usage
│   └── multi_tracker_history.json  # Per-process history
│
├── config.yaml                 # User configuration
├── README.md
├── requirements.txt
└── snapcraft.yaml

## Tech Stack

- **eBPF/bpftrace** - Kernel-level network hooks
- **Python 3** - Main logic
- **psutil** - Process management
- **Rich** - Terminal UI
- **PyYAML** - Configuration
- **Systemd** - Service management

## Contributing

PRs welcome! Areas to improve:

- [ ] Web dashboard (Flask + React)
- [ ] Email alerts
- [ ] Weekly reports
- [ ] Traffic control (tc) integration for throttling
- [ ] Container support (Docker/LXC)

## License

MIT

## Author

Built by [Ndukiye] as a learning project for systems programming and eBPF.

---

**Found this useful? Star the repo!** ⭐