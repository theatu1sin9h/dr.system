# Linux Doctor

**Know your PC. Understand its health.**

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](#)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey)](#)

Linux Doctor is a modern, lightweight, cross-platform PC health diagnostic application. It runs comprehensive local diagnostics across hardware and operating system subsystems, computes an understandable, weighted system health score (0–100), explains every issue in plain language with safe next steps, and offers an allowlisted maintenance engine that operates safely in read-only mode by default.

---

## Key Features

- **Cross-Platform Compatibility Engine**:
  - Automatically detects Linux distributions (Ubuntu, Debian, Fedora, Arch, Manjaro, openSUSE, Kali, Parrot, etc.) and package managers (APT, DNF, Pacman, Zypper, APK). Never assumes APT or Linux commands on Windows.
  - Native Windows 10/11 support via PowerShell, CIM, and WMI interfaces.
  - x86_64 and ARM64 architecture detection.
- **12 Dedicated Modular Diagnostics**:
  1. **CPU**: Physical/logical cores, frequency, utilization, load average, and hardware virtualization.
  2. **Memory (RAM & Swap)**: RAM capacity, memory pressure, swap utilization, thrashing protection.
  3. **Storage & Disks**: HDD/SSD/NVMe space, mount points, filesystem usage, and safe SMART telemetry.
  4. **Graphics (GPU)**: Intel, AMD, NVIDIA, VRAM, and OpenGL software fallback warnings (LLVMpipe).
  5. **Display & Monitors**: Connected displays, resolution modes, refresh rates, Wayland vs X11.
  6. **Audio**: ALSA, PipeWire, PulseAudio status and sound card availability.
  7. **Battery & Power**: Health percentage, design capacity, cycle count, and wear degradation. *Gracefully handles desktops without penalizing missing batteries.*
  8. **Network**: Interface states, link speeds, gateway/DNS reachability.
  9. **Thermals & Cooling**: CPU/GPU core temperatures, fan speeds, thermal throttling indicators.
  10. **Drivers & Kernel**: Loaded kernel modules and kernel driver error detection.
  11. **System Stability**: Service manager failures (`systemd`, Windows SCM) and boot warnings.
  12. **Security & Updates**: System firewall state (UFW/Firewalld/Windows Defender), Secure Boot, and pending updates.
- **Transparent Health Scoring Engine**:
  - Weighted algorithm (0–100) with category-level confidence metrics.
  - Distinguishes physical hardware degradation from transient workload spikes.
  - Explains all deductions and never fabricates telemetry.
- **Safe Maintenance & Repair Engine**:
  - **Read-Only by default**: No changes execute without explicit user approval.
  - Command allowlisting prevents arbitrary shell execution.
  - Clear risk level classifications (Low, Moderate, High), reversibility instructions, and backup guidance.
- **Privacy-First Report Export**:
  - Export reports in **Plain Text (TXT)**, **JSON**, or formatted **HTML**.
  - Automatic redaction of IP addresses, MAC addresses, and usernames by default.
  - Fully local: No data is sent to external cloud servers.
- **Dual Interface**:
  - Modern **PySide6 / Qt** GUI with dark/light design inspired by Linear, Raycast, and modern GNOME.
  - Full-featured **Typer & Rich** Command-Line Interface.

---

## Installation

### Prerequisites
- Python 3.11+
- Git

### Quickstart

```bash
# Clone the repository
git clone https://github.com/linux-doctor/linux-doctor.git
cd linux-doctor

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies and project in editable mode
pip install -e .
```

---

## CLI Usage

### 1. View System Environment
```bash
linux-doctor info
```

### 2. Run Full System Diagnostic Scan
```bash
linux-doctor scan
```

### 3. Run Targeted Scans
```bash
linux-doctor scan --cpu
linux-doctor scan --memory
linux-doctor scan --storage
linux-doctor scan --gpu
linux-doctor scan --battery
linux-doctor scan --network
```

### 4. Export Diagnostic Reports
```bash
# Export formatted Plain Text report
linux-doctor report --format txt --output report.txt

# Export structured JSON report
linux-doctor report --format json --output report.json

# Export clean HTML report
linux-doctor report --format html --output report.html
```

---

## Graphical User Interface (GUI)

Launch the desktop application:
```bash
linux-doctor-gui
```
*(Or run `linux-doctor --gui`)*

---

## Running Automated Tests

```bash
pytest tests/ -v
```

---

## Architecture

```
linux-doctor/
├── src/
│   └── linux_doctor/
│       ├── config.py             # Central application configuration & author branding
│       ├── main.py               # Application entrypoint
│       ├── core/
│       │   ├── detector.py       # Cross-platform OS & architecture detection
│       │   ├── scanner.py        # Diagnostic orchestrator
│       │   ├── scoring.py        # Weighted health scoring algorithm
│       │   ├── findings.py       # Diagnostic models & 6-point explanations
│       │   └── permissions.py    # Safe privilege checks
│       ├── platforms/
│       │   ├── base.py           # Abstract adapter & safe command execution
│       │   ├── linux/generic.py  # Sysfs, procfs, systemd adapter
│       │   └── windows/system.py # PowerShell & CIM adapter
│       ├── diagnostics/          # 12 Independent diagnostic modules
│       ├── maintenance/          # Allowlisted repair engine & confirmation
│       ├── reports/              # JSON, TXT, and HTML report generator
│       ├── gui/                  # PySide6 desktop views, sidebar, and theme
│       └── cli/                  # Rich & Typer CLI commands
├── tests/                        # Comprehensive unit & integration tests
├── LICENSE                       # MIT License
└── pyproject.toml                # Build system configuration
```

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

Made with care by **[YOUR NAME]**.
