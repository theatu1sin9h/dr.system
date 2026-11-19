<div align="center">

```
 ____             ____            _                 
|  _ \ _ __      / ___| _   _ ___| |_ ___ _ __ ___  
| | | | '__|_____\___ \| | | / __| __/ _ \ '_ ` _ \ 
| |_| | | |_____| ___) | |_| \__ \ ||  __/ | | | | |
|____/|_|        |____/ \__, |___/\__\___|_| |_| |_|
                        |___/                       
```

# 🩺 Dr. System
### *The Autonomous Terminal PC Health & Clinical Hardware Diagnostic Engine*

[![Author](https://img.shields.io/badge/Designed%20by-Atul%20Singh%20Chandel-00E5FF?style=for-the-badge&logo=github)](https://github.com/theatu1sin9h)
[![Email](https://img.shields.io/badge/Connect-myself.tas03%40gmail.com-FF4081?style=for-the-badge&logo=gmail)](mailto:myself.tas03@gmail.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-00E676?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Ubuntu%20%7C%20Arch%20%7C%20Fedora%20%7C%20Kali%20%7C%20Windows-7C4DFF?style=for-the-badge)](https://github.com/theatu1sin9h/dr.system)

<p align="center">
  <b>Know your PC. Understand its health. Prescribe safe solutions.</b><br>
  Built for sysadmins, hackers, developers, and power users who love the raw power and beauty of the terminal.
</p>

---

</div>

## ⚡ Why Dr. System?

Most system utilities on Linux are either boring wrappers around `lscpu`/`df` or noisy GUI applications that eat RAM.

**Dr. System** brings the clinical precision of **Nmap**, the real-time speed of **Htop**, and cutting-edge kernel diagnostics into one terminal-native suite:

* 🧠 **No Mockups or Placeholders**: 100% real kernel telemetry queried safely via sysfs, procfs, and direct block I/O.
* 🌡️ **Thermal Half-Life ($T_{1/2}$) Decay Profiling**: Runs a calibrated 2-second burst workload to measure how fast your heatsink drops temperature. It objectively detects **dried thermal paste**, clogged fan vents, and thermal runaway before your PC shuts down under load.
* ⚡ **Kernel Pressure Stall Information (PSI)**: Inspects `/proc/pressure/{cpu,memory,io}` to quantify real wall-clock task stall percentages. Distinguishes harmless 100% CPU compiling from desktop-freezing I/O starvation and D-state hung threads.
* ⏱️ **Direct 4K Storage Latency Jitter**: Bypasses the OS page cache with raw unbuffered reads, recording direct 4K random read latency percentiles (P50, P95, P99, Max) to identify failing flash storage and controller queue locks before SMART flags trigger.
* 🔗 **Cross-Subsystem Causality Engine**: Instead of isolated metrics, it correlates causes. For example, it explains if high temperatures are actively downclocking your CPU (thermal throttling), or if NVMe queue lockups are causing audio stutters.
* ⏳ **Time-Travel Regression Tracking (`dr-system diff`)**: Automatically snapshots scans and detects performance regressions over time (e.g. *"Since yesterday's update, storage latency increased 24%"*).
* 🛡️ **Zero External Telemetry**: Runs completely offline and local. Automatic redaction of IP addresses, MAC addresses, and hostnames by default.

---

## 📸 Terminal Experience

```
╔══════════════════════════════════════════════════════════════════════════════╗
║          Designed by - Atul Singh Chandel <myself.tas03@gmail.com>           ║
║          • Dr. System v2.5.0 • Know your PC. Understand its health.          ║
╚══════════════════════════════════════════════════════════════════════════════╝
>>> INITIALIZING CLINICAL HARDWARE AUDIT...

  All diagnostic procedures completed! ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━ CLINICAL EVALUATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ SYSTEM CLINICAL HEALTH SCORE: 98 / 100 (EXCELLENT)                           ┃
┃ Sensor Confidence: 95% | Test Coverage: 100.0% | Elapsed: 3.2s                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                        SUBSYSTEM CLINICAL AUDIT RATINGS                        
╭──────────────────────┬──────────────────┬─────────────┬──────────────────────╮
│ Subsystem            │ Efficiency Score │ Diagnostics │ Key Telemetry        │
├──────────────────────┼──────────────────┼─────────────┼──────────────────────┤
│ Processor (CPU)      │    100.0/100     │  ● PASSED   │ 8 threads | 4.2 GHz  │
│ Memory (RAM & Swap)  │    100.0/100     │  ● PASSED   │ 2.8/16.0 GB (17.5%)  │
│ Storage & Disks      │    100.0/100     │  ● PASSED   │ 380 GB free NVMe     │
│ Storage Latency      │    100.0/100     │  ● PASSED   │ P99 latency: 1.49ms  │
│ Thermal Decay        │     90.0/100     │  ● PASSED   │ Peak: 72°C (4.2s t½) │
│ Kernel PSI Stalls    │    100.0/100     │  ● PASSED   │ 0.00% thread stalls  │
│ Graphics (GPU)       │    100.0/100     │  ● PASSED   │ Direct Rendering OK  │
│ Network & Audio      │    100.0/100     │  ● PASSED   │ PipeWire active      │
╰──────────────────────┴──────────────────┴─────────────┴──────────────────────╯
```

---

## 🚀 Quickstart (Clone & Run)

Anyone can clone and run Dr. System in seconds:

```bash
# 1. Clone the repository
git clone https://github.com/theatu1sin9h/dr.system.git
cd dr.system

# 2. Create virtual environment & install
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 3. (Optional) Link to your local bin to run anywhere
mkdir -p ~/.local/bin
ln -sf $(pwd)/.venv/bin/dr-system ~/.local/bin/dr-system
```

---

## 🛠 Command Arsenal

### 1. Clinical Hardware Diagnostic Scan
```bash
# Full clinical scan of all 15 hardware & kernel subsystems
dr-system scan

# Automatically save a clean prescription report
dr-system scan --save
```

### 2. Live Telemetry Monitor (like `htop` / `btop`)
```bash
# Live real-time dashboard updating CPU, RAM pressure, Swap, Thermals, and PSI stalls
dr-system monitor
```

### 3. Hardware & Platform Topology
```bash
# Display detected OS distribution, kernel, display server, sound daemon, and architecture
dr-system info
```

### 4. Surgical Targeted Checks
```bash
# Audit CPU compute flags and load averages
dr-system scan --cpu

# Run direct 4K storage latency percentiles (P50, P95, P99)
dr-system scan --latency

# Run synthetic thermal dissipation curve analysis
dr-system scan --thermal-decay

# Audit Linux Kernel Pressure Stall Information
dr-system scan --psi
```

### 5. Time-Travel Regression Diff
```bash
# Compare previous diagnostic scans to identify performance degradation
dr-system diff
```

### 6. Export Sanitized Professional Reports
```bash
# Export formatted text report
dr-system report --format txt --output report.txt

# Export raw structured JSON for automated pipelines
dr-system report --format json --output report.json

# Export clean dark-themed HTML report
dr-system report --format html --output report.html
```

---

## 🏗 Subsystem Coverage (15 Modular Engines)

| Subsystem | What Dr. System Checks |
| :--- | :--- |
| **Processor (CPU)** | Physical/logical cores, frequency scaling, load averages, utilization, virtualization flags (`vmx`/`svm`). |
| **Memory (RAM)** | Used/free RAM, memory pressure, swap utilization, thrashing indicators. |
| **Storage & Disks** | Partitions, filesystem usage, mount points, safe SMART disk scanning. |
| **Storage Latency** | Direct raw 4K random read percentiles (P50, P95, P99) bypassing OS cache. |
| **Thermal Profiler** | Silicon temperatures, fan speed metrics, thermal decay curve half-life ($T_{1/2}$). |
| **Kernel PSI** | Pressure Stall Information for CPU, Memory, and I/O (`some` vs `full` stall ratios). |
| **GPU & Drivers** | NVIDIA, AMD, Intel, VRAM capacity, OpenGL direct rendering vs software fallback. |
| **Display Compositor**| Connected monitors, modes, refresh rates, Wayland vs X11 session handling. |
| **Audio Server** | ALSA, PipeWire, PulseAudio states and hardware audio cards. |
| **Battery & Power** | Capacity, wear percentage, cycle count. Gracefully marks desktop PCs as N/A without penalties. |
| **Network** | Network adapters, link speeds, gateway reachability, DNS health. |
| **System Stability** | Failed `systemd` units, crash daemons, critical kernel errors in `dmesg`. |
| **Security** | Firewall status (UFW, Firewalld), Secure Boot enforcement, pending update counts. |
| **Causality Engine** | Cross-subsystem correlation matrix linking thermal throttling, I/O lockups, and CPU drops. |
| **Snapshots** | Compact differential historical records for regression auditing. |

---

## 👨‍💻 Creator & Maintainer

<table align="center">
  <tr>
    <td align="center">
      <b>Atul Singh Chandel</b><br>
      <i>Creator & Lead Architect</i><br><br>
      <a href="https://github.com/theatu1sin9h">GitHub: @theatu1sin9h</a><br>
      <a href="mailto:myself.tas03@gmail.com">Email: myself.tas03@gmail.com</a>
    </td>
  </tr>
</table>

---

## 📜 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details. Free and open source for everyone.
