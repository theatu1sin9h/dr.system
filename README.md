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
### *The Autonomous All-In-One Cyber Console, Hardware Architecture Flow & Kernel Security Doctor*

[![Author](https://img.shields.io/badge/Designed%20by-Atul%20Singh%20Chandel-00E5FF?style=for-the-badge&logo=github)](https://github.com/theatu1sin9h)
[![Email](https://img.shields.io/badge/Connect-myself.tas03%40gmail.com-FF4081?style=for-the-badge&logo=gmail)](mailto:myself.tas03@gmail.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-00E676?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Ubuntu%20%7C%20Kali%20%7C%20Arch%20%7C%20Fedora%20%7C%20Debian-7C4DFF?style=for-the-badge)](https://github.com/theatu1sin9h/dr.system)

<p align="center">
  <b>Visual System Architecture Flow • Real-Time Volatile Telemetry • Deep Hardware Direct Latency • Kernel Security Hardening</b><br>
  Built for hackers, sysadmins, and Linux enthusiasts who demand an all-in-one terminal command center.
</p>

---

</div>

## 🚀 1-Click Launch (`./dr.system.sh`)

Clone the repo and run **one single file**:

```bash
git clone https://github.com/theatu1sin9h/dr.system.git
cd dr.system
./dr.system.sh
```

Everything installs and initializes automatically in an isolated virtual environment and launches the **Dr. System Interactive Terminal Console**.

---

## 🗑️ Clean Uninstallation (Remove Dr. System)

If you ever wish to remove Dr. System from your computer completely:

### Method 1: Interactive Uninstall Script
Run the automated cleanup script inside the repository:
```bash
./uninstall.sh
```
This cleanly removes:
- `~/.local/bin/dr-system` (CLI binary link)
- `~/.local/share/applications/linux-doctor.desktop` (Desktop menu entry)
- `~/.config/linux-doctor` (Saved historical snapshots & configs)
- `.venv/` (Virtual environment)

To remove the cloned source folder as well:
```bash
cd .. && rm -rf dr.system
```

### Method 2: Via Command-Line Interface
If installed in your path, you can run directly from anywhere:
```bash
dr-system uninstall
```
*(Use `dr-system uninstall --yes` to bypass the confirmation prompt)*.

---

## 🧭 Master Console Architecture (4 Cyber Views)

### 🛰️ View 1: Hardware Bus Interconnect Architecture Flow
Displays the physical and logical topology of your machine:
```text
 ┌──────────────┐         High-Speed Direct Bus          ┌──────────────┐
 │   CPU DIE    │ <===================================> │   DDR RAM    │
 │  x86_64      │   Interconnect: System Fabric / QPI    │ 16 GB Fabric │
 └──────┬───────┘                                       └──────────────┘
        │ PCIe Root Complex x16 / DMI Bus
        ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │                PLATFORM CONTROLLER HUB (PCH / BUS)                  │
 └──────┬──────────────────────┬───────────────────────┬───────────────┘
        ▼                      ▼                       ▼
 ┌──────────────┐      ┌──────────────┐        ┌──────────────┐
 │ GPU DRIVER   │      │ NVMe STORAGE │        │ NETWORK/PHY  │
 │ Wayland/DRM  │      │ Direct I/O   │        │ Socket Link  │
 └──────────────┘      └──────────────┘        └──────────────┘
```
Coupled with a **Live Telemetry Stream** showing real-time CPU utilization per core, physical memory vs swap pressure, ACPI thermal probes, and Linux Kernel PSI stall ratios.

---

### 🖥️ View 2: Complete Hardware Inventory & Direct Block Latency
- Comprehensive component audit: Processor microarchitecture, RAM capacity/available allocation, GPU driver and OpenGL rendering engine.
- **Direct 4K Read Latency**: Bypasses the OS page cache with raw unbuffered reads, recording direct 4K random read latency percentiles (**P50, P95, P99, Max**) to detect flash degradation and controller queue lockups before SMART flags trip.
- Mounted partition capacities with high-resolution visual percentage gauges.

---

### 🛡️ View 3: Linux Kernel Hardening & Security Logic Flow
Audits your operating system's security posture against binary exploits and network attacks:
- **Mandatory Access Control (MAC / LSM)**: Verifies active AppArmor / SELinux confinement.
- **ASLR (Address Space Layout Randomization)**: Audits `randomize_va_space` level 2 protection against buffer overflow and ROP exploits.
- **Kernel Pointer Protection**: Checks `kptr_restrict` to ensure kernel memory addresses are concealed.
- **Dmesg Buffer Lockdown**: Checks `dmesg_restrict` to prevent unprivileged kernel log scraping.
- **Yama Ptrace Scope**: Checks process memory injection guards against unauthorized debugger attachment.
- **Unprivileged eBPF**: Audits protection against JIT shellcode spraying.
- **TCP SYN Cookie Defense**: Checks network stack resilience against SYN flood DoS attacks.
- **IP Packet Routing**: Audits host routing configuration against MITM risks.

---

### 🩺 View 4: Cross-Subsystem Causality Correlator & Prescriptions
Instead of reporting isolated numbers, Dr. System correlates issues across layers:
- Detects if **high silicon temperatures** are actively throttling CPU frequencies.
- Detects if **storage I/O queue stalls** are causing audio dropouts or desktop micro-freezes.
- Translates issues into clinical prescriptions with actionable, safe next steps.

---

## 🛠️ Command Arsenal

Dr. System can also be used as a standard CLI tool:

```bash
# 1. Full clinical hardware scan
dr-system scan

# 2. Real-time live monitor
dr-system monitor

# 3. Hardware topology summary
dr-system info

# 4. Surgical targeted checks
dr-system scan --cpu
dr-system scan --latency
dr-system scan --thermal-decay
dr-system scan --psi

# 5. Differential time-travel regression comparison
dr-system diff

# 6. Export professional diagnostic reports
dr-system report --format txt --output report.txt
dr-system report --format json --output report.json
dr-system report --format html --output report.html

# 7. Cleanly uninstall Dr. System from your machine
dr-system uninstall
```

---

## 👨‍💻 Creator & Contact

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
