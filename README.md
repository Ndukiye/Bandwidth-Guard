# Bandwidth Guard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Release](https://img.shields.io/github/v/release/Ndukiye/bandwidth-guard)](https://github.com/Ndukiye/bandwidth-guard/releases)

Monitor and enforce per-process network bandwidth limits on Linux using eBPF.


## Features

- 🚀 **Real-time tracking** - See which apps are using your bandwidth
- ⚡ **eBPF-powered** - Kernel-level monitoring with minimal overhead  
- 🎯 **Smart enforcement** - Set limits per app (kill or warn when exceeded)
- 📊 **Rich CLI** - Beautiful terminal UI with history reports
- 🔔 **Desktop notifications** - Get alerts at 80% and 100% usage
- 📅 **Daily tracking** - Automatic daily reset with historical data

## Quick Install

```bash
One-line installer
curl -fsSL https://raw.githubusercontent.com/Ndukiye/bandwidth-guard/main/install.sh | sudo bash

**Or manual installation:**

```bash1. Download latest release
wget https://github.com/Ndukiye/bandwidth-guard/releases/latest/download/bandwidth-guard-installer.tar.gz2. Extract and install
tar -xzf bandwidth-guard-installer.tar.gz
cd bandwidth-guard
sudo ./install.sh

**Test it:**
```bashbwguard status

## Usage

```bashView today's usage
bwguard statusView last 30 days
bwguard history --days 30Set Firefox limit (2GB/day, kill when exceeded)
bwguard set-limit firefox 2048Set Spotify limit (500MB/day, warn only)
bwguard set-limit spotify 500 --action warnList configured limits
bwguard limitsRemove a limit
bwguard remove-limit firefox

## How It Works┌─────────────────────────────────────────┐
│  eBPF Hooks (bpftrace)                  │
│  Kernel-level network tracking          │
└────────────┬────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│  Systemd Daemon (monitor.py)            │
│  • Aggregates per-process stats         │
│  • Enforces limits (kill/warn)          │
│  • Sends desktop notifications          │
└────────────┬────────────────────────────┘
│ Writes to
▼
┌─────────────────────────────────────────┐
│  /var/lib/bandwidth-guard/              │
│  • config.yaml                          │
│  • data.json                            │
│  • multi_tracker_history.json           │
└────────────▲────────────────────────────┘
│ Reads from
┌────────────┴────────────────────────────┐
│  CLI Snap (bwguard)                     │
│  • View status                          │
│  • Set limits                           │
│  • View history                         │
└─────────────────────────────────────────┘

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for local development setup.

## Platform Support

- ✅ **Ubuntu 20.04+** (tested)
- ✅ **Debian/Fedora/Arch** (should work)
- ✅ **WSL2** (Windows users)
- ❌ **macOS/Windows native** (eBPF is Linux-only)

## Requirements

- Linux kernel 5.2+ (for eBPF)
- bpftrace 0.18+
- Python 3.8+
- Root access (for eBPF monitoring)

## Tech Stack

- **eBPF/bpftrace** - Kernel-level network hooks
- **Python 3** - Main logic & CLI
- **Systemd** - Background daemon management
- **Snap** - Distribution packaging
- **Rich** - Terminal UI
- **PyYAML** - Configuration management

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

Areas to improve:
- Web dashboard (Flask + React)
- Traffic control (tc) integration for throttling
- Email/Slack alerts
- Container support

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built as a learning project for systems programming and eBPF
- Inspired by `nethogs` and `iftop`
- Thanks to the bpftrace and eBPF communities

## Author

**Orukaria Ndukiye**  
[GitHub](https://github.com/Ndukiye) • [LinkedIn](https://linkedin.com/in/orukaria-ndukiye)

---

**Found this useful? Star the repo!** ⭐