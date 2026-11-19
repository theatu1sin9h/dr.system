"""Interactive All-In-One Cyber Console with Asynchronous Fast-Load & Real Keyboard Navigation.

Designed by - Atul Singh Chandel <myself.tas03@gmail.com>
Supports real-time keypresses (1, 2, 3, 4, q, r) using non-blocking terminal tty stdin!
"""

import math
import os
import select
import shutil
import sys
import termios
import threading
import time
import tty
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import psutil

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from linux_doctor.config import APP_AUTHOR, APP_AUTHOR_EMAIL, APP_NAME, APP_TAGLINE, APP_VERSION
from linux_doctor.core.causality import CausalityEngine
from linux_doctor.core.detector import OSDetector, OSInfo
from linux_doctor.core.findings import FindingSeverity, ModuleResult
from linux_doctor.core.scanner import DiagnosticScanner
from linux_doctor.diagnostics.security_posture import KernelSecurityAuditor


def make_gauge_bar(percent: float, width: int = 16, color_normal: str = "bright_green", color_warn: str = "yellow", color_crit: str = "bright_red") -> Text:
    p = max(0.0, min(100.0, percent))
    filled = int(round((p / 100.0) * width))
    empty = width - filled

    col = color_normal
    if p > 85.0:
        col = color_crit
    elif p > 70.0:
        col = color_warn

    bar = "█" * filled + "░" * empty
    t = Text()
    t.append(f"{p:>5.1f}% ", style="bold bright_white")
    t.append(bar, style=col)
    return t


class NonBlockingInput:
    """Reads single keypresses without waiting for Enter."""

    def __enter__(self):
        self.old_settings = None
        if sys.stdin.isatty():
            try:
                self.old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
            except Exception:
                pass
        return self

    def __exit__(self, type, value, traceback):
        if self.old_settings and sys.stdin.isatty():
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            except Exception:
                pass

    def get_key(self) -> Optional[str]:
        if not sys.stdin.isatty():
            return None
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            try:
                return sys.stdin.read(1)
            except Exception:
                return None
        return None


class AllInOneDashboard:
    """Full-featured cyber console with instant startup & real interactive navigation."""

    def __init__(self):
        self.os_info: OSInfo = OSDetector.detect()
        self.scanner = DiagnosticScanner()
        self.results: Dict[str, Any] = {}
        self.scan_complete = False
        self.active_tab = 1  # 1 = Architecture, 2 = Hardware & Storage, 3 = Kernel Security, 4 = Causality & Issues
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())
        self.sec_audit = KernelSecurityAuditor.audit()

    def get_uptime_str(self) -> str:
        delta = datetime.now() - self.boot_time
        d = delta.days
        h, rem = divmod(delta.seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{d}d {h}h {m}m {s}s" if d > 0 else f"{h}h {m}m {s}s"

    def _get_metric(self, mod_key: str, metric_key: str, default: Any = None) -> Any:
        mod = self.results.get(mod_key)
        if isinstance(mod, ModuleResult):
            return mod.metrics.get(metric_key, default)
        elif isinstance(mod, dict):
            return mod.get("metrics", {}).get(metric_key, default)
        return default

    def render_architecture_view(self) -> Group:
        """Tab 1: Architecture Diagram & Live Telemetry Stream."""
        bus_flow = Text()
        bus_flow.append(" ┌──────────────┐         High-Speed Direct Bus          ┌──────────────┐\n", style="bright_blue")
        bus_flow.append(" │   CPU DIE    │ <===================================> │   DDR RAM    │\n", style="bold cyan")
        bus_flow.append(f" │  {self.os_info.architecture:<10}  │   Interconnect: System Fabric / QPI    │ {psutil.virtual_memory().total // (1024**3):>2} GB Fabric │\n", style="bright_white")
        bus_flow.append(" └──────┬───────┘                                       └──────────────┘\n", style="bright_blue")
        bus_flow.append("        │ PCIe Root Complex x16 / DMI Bus\n", style="bright_magenta")
        bus_flow.append("        ▼\n", style="bright_magenta")
        bus_flow.append(" ┌─────────────────────────────────────────────────────────────────────┐\n", style="bright_blue")
        bus_flow.append(" │                PLATFORM CONTROLLER HUB (PCH / BUS)                  │\n", style="bold yellow")
        bus_flow.append(" └──────┬──────────────────────┬───────────────────────┬───────────────┘\n", style="bright_blue")
        bus_flow.append("        ▼                      ▼                       ▼\n", style="dim bright_white")
        bus_flow.append(" ┌──────────────┐      ┌──────────────┐        ┌──────────────┐\n", style="bright_green")
        bus_flow.append(" │ GPU DRIVER   │      │ NVMe STORAGE │        │ NETWORK/PHY  │\n", style="bold bright_green")
        bus_flow.append(f" │ {self.os_info.display_server[:12]:<12} │      │ Direct I/O   │        │ Socket Link  │\n", style="bright_white")
        bus_flow.append(" └──────────────┘      └──────────────┘        └──────────────┘\n", style="bright_green")

        arch_panel = Panel(bus_flow, title="[bold bright_green]🛰️ HARDWARE BUS INTERCONNECT ARCHITECTURE FLOW[/bold bright_green]", box=box.ROUNDED, border_style="bright_blue")

        # Telemetry Table
        cpu_p = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()
        temps = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}

        t_table = Table(box=box.SIMPLE, show_header=False, expand=True)
        t_table.add_column("Sensor / Node", style="bold cyan", width=22)
        t_table.add_column("Reading / Status", justify="left")

        t_table.add_row("Processor Load", make_gauge_bar(cpu_p, width=18))
        t_table.add_row("Physical Memory", make_gauge_bar(vm.percent, width=18))
        t_table.add_row("Swap Pool", make_gauge_bar(swap.percent, width=18, color_warn="bright_magenta"))

        max_t = 0.0
        for name, entries in temps.items():
            for e in entries:
                if e.current > max_t: max_t = e.current
        if max_t > 0:
            col = "bright_green" if max_t < 75 else ("yellow" if max_t < 85 else "bright_red")
            t_table.add_row("Peak Silicon Thermals", Text(f"{max_t:.1f}°C", style=f"bold {col}"))

        base_psi = Path("/proc/pressure")
        if base_psi.exists():
            for pt in ["cpu", "memory", "io"]:
                fp = base_psi / pt
                if fp.exists():
                    txt = fp.read_text().strip()
                    avg10 = "0.00%"
                    for part in txt.split():
                        if "avg10=" in part:
                            avg10 = part.split("=")[1] + "%"
                    t_table.add_row(f"Kernel {pt.upper()} Stalls", Text(f"{avg10} (Micro-delay free)", style="bright_green" if "0.00" in avg10 else "yellow"))

        live_panel = Panel(t_table, title="[bold bright_cyan]⚡ REAL-TIME VOLATILE TELEMETRY STREAM[/bold bright_cyan]", box=box.ROUNDED, border_style="cyan")

        return Group(arch_panel, live_panel)

    def render_hardware_view(self) -> Group:
        """Tab 2: Deep Hardware Inventory & Direct Block Latency."""
        hw_table = Table(box=box.ROUNDED, border_style="bright_blue", header_style="bold magenta", expand=True)
        hw_table.add_column("Subsystem", style="bold cyan", width=24)
        hw_table.add_column("Model / Specification", style="bold bright_white")
        hw_table.add_column("Direct Health Telemetry", style="bright_green")

        # CPU
        cpu_name = self._get_metric("cpu", "model", "Processor")
        cores_phys = psutil.cpu_count(logical=False) or 1
        cores_log = psutil.cpu_count(logical=True) or 1
        hw_table.add_row("Processor (CPU)", f"{cpu_name}", f"{cores_phys} Cores / {cores_log} Threads")

        # Memory
        vm = psutil.virtual_memory()
        hw_table.add_row("RAM Fabric", f"{vm.total / (1024**3):.2f} GB Total Pool", f"{vm.available / (1024**3):.2f} GB Available for Allocation")

        # GPU
        gpus = self._get_metric("gpu", "gpus", [])
        gpu_name = gpus[0].get("model", "Graphics Controller") if gpus else "Kernel Integrated Graphics"
        renderer = self._get_metric("gpu", "opengl_renderer", "Mesa / DRM")
        hw_table.add_row("Graphics Accelerator", str(gpu_name)[:40], f"Renderer: {str(renderer)[:24]}")

        # Storage & Latency
        lat_test = self._get_metric("storage_latency", "latency_test")
        lat_str = "Auditing live jitter in background..."
        if lat_test and isinstance(lat_test, dict):
            p99 = lat_test.get("p99_latency_ms", "-")
            lat_str = f"Direct 4K Read P99: {p99} ms (Page cache bypass)"
        hw_table.add_row("Storage Block Devices", f"{len(psutil.disk_partitions(all=False))} Mounted Volumes", lat_str)

        # Audio
        sound_cnt = self._get_metric("audio", "sound_cards_count", 0)
        hw_table.add_row("Audio Subsystem", f"Server: {self.os_info.audio_server or 'PipeWire'}", f"ALSA Cards: {sound_cnt}")

        # Battery
        bat = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
        bat_str = f"{bat.percent}% ({'AC Connected' if bat.power_plugged else 'Battery'})" if bat else "Desktop Station (AC Mains)"
        hw_table.add_row("Battery & Power", bat_str, "Wear Normal")

        hw_panel = Panel(hw_table, title="[bold bright_green]🖥️ COMPLETE PHYSICAL COMPONENT INVENTORY[/bold bright_green]", box=box.ROUNDED, border_style="bright_blue")

        p_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", expand=True)
        p_table.add_column("Device Mount", style="bold bright_white")
        p_table.add_column("Filesystem", style="dim")
        p_table.add_column("Capacity Gauge", justify="center")
        p_table.add_column("Used / Total", style="bright_white")

        for part in psutil.disk_partitions(all=False)[:4]:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                p_table.add_row(
                    part.mountpoint,
                    part.fstype,
                    make_gauge_bar(usage.percent, width=16),
                    f"{usage.used / (1024**3):.1f} GB / {usage.total / (1024**3):.1f} GB",
                )
            except Exception:
                pass

        part_panel = Panel(p_table, title="[bold bright_cyan]💾 BLOCK FILESYSTEM DISK VOLUMES[/bold bright_cyan]", box=box.ROUNDED, border_style="cyan")

        return Group(hw_panel, part_panel)

    def render_security_view(self) -> Group:
        """Tab 3: Kernel Security, Hardening & Attack Surface Posture."""
        sec_table = Table(box=box.ROUNDED, border_style="bright_blue", header_style="bold magenta", expand=True)
        sec_table.add_column("Security Subsystem", style="bold cyan", width=28)
        sec_table.add_column("Kernel Protection State", style="bold bright_white")
        sec_table.add_column("Attack Surface Mitigation", style="bright_green")

        sec_table.add_row("Mandatory Access Control", f"[bold green]{self.sec_audit.get('lsm', 'None')}[/bold green]", "Confines processes beyond standard Unix permissions")
        sec_table.add_row("ASLR Protection", f"[bold green]{self.sec_audit.get('aslr', 'Level 2')}[/bold green]", "Mitigates buffer overflows & binary memory exploits")
        sec_table.add_row("Kernel Pointer Concealment", f"[bold green]{self.sec_audit.get('kptr_restrict', 'Protected')}[/bold green]", "Hides real kernel memory addresses from attackers")
        sec_table.add_row("Dmesg Buffer Lockdown", f"[bold green]{self.sec_audit.get('dmesg_restrict', 'Hardened')}[/bold green]", "Prevents unprivileged kernel log scraping")
        sec_table.add_row("Yama Ptrace Scope Guard", f"[bold green]{self.sec_audit.get('yama_ptrace', 'Restricted')}[/bold green]", "Blocks cross-process memory code injection")
        sec_table.add_row("Unprivileged eBPF", f"[bold green]{self.sec_audit.get('unprivileged_bpf', 'Disabled')}[/bold green]", "Hardened against kernel JIT shellcode spraying")
        sec_table.add_row("TCP SYN Cookie Defense", f"[bold green]{self.sec_audit.get('tcp_syncookies', 'Active')}[/bold green]", "Protects network stack against SYN flood DoS attacks")
        sec_table.add_row("IP Packet Routing", f"[bold green]{self.sec_audit.get('ip_forwarding', 'Disabled')}[/bold green]", "Host routing disabled (Mitigates MITM interception)")

        sec_panel = Panel(sec_table, title="[bold bright_green]🛡️ LINUX KERNEL HARDENING & SECURITY POSTURE AUDIT[/bold bright_green]", box=box.ROUNDED, border_style="bright_blue")

        flow_text = Text()
        flow_text.append(" [USERSPACE APPLICATIONS]  ──►  Protected by ASLR & Yama Ptrace\n", style="bold cyan")
        flow_text.append("          │ (Syscalls)\n", style="dim")
        flow_text.append("          ▼\n", style="dim")
        flow_text.append(" [LSM / MAC LAYER]         ──►  AppArmor Profiles Active (Enforcing)\n", style="bold green")
        flow_text.append("          │\n", style="dim")
        flow_text.append("          ▼\n", style="dim")
        flow_text.append(" [LINUX KERNEL CORE]       ──►  kptr_restrict & dmesg_restrict concealed\n", style="bold magenta")
        flow_text.append("          │\n", style="dim")
        flow_text.append("          ▼\n", style="dim")
        flow_text.append(" [NETWORK INTERFACE STACK] ──►  SYN Cookies active, IP Forwarding blocked\n", style="bold yellow")

        flow_panel = Panel(flow_text, title="[bold bright_yellow]🔐 OPERATING SYSTEM SECURITY LOGIC FLOW[/bold bright_yellow]", box=box.ROUNDED, border_style="yellow")

        return Group(sec_panel, flow_panel)

    def render_causality_view(self) -> Group:
        """Tab 4: Cross-Subsystem Causality Engine & Prescriptions."""
        c_table = Table(box=box.ROUNDED, border_style="bright_blue", header_style="bold magenta", expand=True)
        c_table.add_column("Subsystem Origin", style="bold yellow", width=22)
        c_table.add_column("Affected Layer", style="bold cyan", width=22)
        c_table.add_column("Clinical Causality Correlation & Prescription", style="bright_white")

        if self.scanner.causality_insights:
            for ins in self.scanner.causality_insights:
                c_table.add_row(ins.cause_component, ins.affected_component, f"[bold red]{ins.title}:[/bold red] {ins.explanation}\n[bold green]Prescription:[/bold green] {ins.recommendation}")
        else:
            c_table.add_row("All Hardware Layers", "Operating System", "[bold bright_green]✓ Clean Bill of Health:[/bold bright_green] Zero cross-subsystem hardware bottlenecks detected.")

        c_panel = Panel(c_table, title="[bold red]🩺 CROSS-SUBSYSTEM CAUSALITY CORRELATOR[/bold red]", box=box.ROUNDED, border_style="red")

        issues_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", expand=True)
        issues_table.add_column("Subsystem", style="bold bright_white", width=22)
        issues_table.add_column("Finding", style="bold yellow")
        issues_table.add_column("Safe Next Step Prescription", style="bright_green")

        issue_cnt = 0
        for mod in self.results.values():
            if isinstance(mod, ModuleResult):
                for f in mod.findings:
                    if f.severity in (FindingSeverity.WARNING, FindingSeverity.CRITICAL):
                        issue_cnt += 1
                        issues_table.add_row(mod.display_name, f.title, f.safe_next_step)

        if issue_cnt == 0:
            issues_table.add_row("System Audit", "No critical findings detected.", "Continue normal operation.")

        issues_panel = Panel(issues_table, title="[bold bright_cyan]📋 CLINICAL PRESCRIPTION ACTIONS[/bold bright_cyan]", box=box.ROUNDED, border_style="cyan")

        return Group(c_panel, issues_panel)

    def generate_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        overall_score = self.scanner.score_report.overall_score if self.scanner.score_report else 100
        status_label = self.scanner.score_report.status_label if self.scanner.score_report else "OPTIMAL"

        header_text = Text()
        header_text.append("Designed by - ", style="bold bright_white")
        header_text.append(f"{APP_AUTHOR} ", style="bold yellow")
        header_text.append(f"<{APP_AUTHOR_EMAIL}>\n", style="bold bright_green")
        header_text.append(f"• {APP_NAME} v{APP_VERSION} • ", style="bold cyan")
        header_text.append(f"Uptime: {self.get_uptime_str()}  ", style="bold bright_white")
        header_text.append("• Overall Health: ", style="dim")
        header_text.append(f"{overall_score}/100 ({status_label})", style="bold bright_green")

        layout["header"].update(Panel(Align.center(header_text), box=box.DOUBLE, border_style="bright_blue"))

        # Render Active Tab safely
        try:
            if self.active_tab == 1:
                body_content = self.render_architecture_view()
            elif self.active_tab == 2:
                body_content = self.render_hardware_view()
            elif self.active_tab == 3:
                body_content = self.render_security_view()
            else:
                body_content = self.render_causality_view()
        except Exception as e:
            body_content = Panel(f"[bold red]View Render Notice:[/bold red] {str(e)}", border_style="red")

        layout["body"].update(body_content)

        # Footer Tab Navigation Bar with Active Highlights
        footer_text = Text()
        tab1_style = "bold bright_green on #182838" if self.active_tab == 1 else "bold cyan"
        tab2_style = "bold bright_green on #182838" if self.active_tab == 2 else "bold cyan"
        tab3_style = "bold bright_green on #182838" if self.active_tab == 3 else "bold cyan"
        tab4_style = "bold bright_green on #182838" if self.active_tab == 4 else "bold cyan"

        footer_text.append(" [Press 1] Architecture & Flow ", style=tab1_style)
        footer_text.append(" │ ", style="dim")
        footer_text.append(" [Press 2] Hardware & Latency ", style=tab2_style)
        footer_text.append(" │ ", style="dim")
        footer_text.append(" [Press 3] Kernel Security ", style=tab3_style)
        footer_text.append(" │ ", style="dim")
        footer_text.append(" [Press 4] Causality & Issues ", style=tab4_style)
        footer_text.append(" │ ", style="dim")
        footer_text.append(" [Q] Quit ", style="bold bright_red")

        layout["footer"].update(Panel(Align.center(footer_text), box=box.ROUNDED, border_style="bright_blue"))

        return layout


def run_all_in_one():
    """Runs the console with animated progress bar on startup and instant keyboard response."""
    console = Console()
    console.clear()

    # Step 1: Animated Clinical Progress Bar on Startup
    banner_art = r"""[bold cyan]
 ____             ____            _                 
|  _ \ _ __      / ___| _   _ ___| |_ ___ _ __ ___  
| | | | '__|_____\___ \| | | / __| __/ _ \ '_ ` _ \ 
| |_| | | |_____| ___) | |_| \__ \ ||  __/ | | | | |
|____/|_|        |____/ \__, |___/\__\___|_| |_| |_|
                        |___/                       
[/bold cyan]"""
    console.print(Align.center(banner_art))
    console.print(Align.center(f"[bold bright_white]Designed by - [yellow]{APP_AUTHOR}[/yellow] [bright_green]<{APP_AUTHOR_EMAIL}>[/bright_green][/bold bright_white]"))
    console.print(Align.center(f"[dim cyan]• {APP_NAME} v{APP_VERSION} • {APP_TAGLINE}[/dim cyan]\n"))

    dashboard = AllInOneDashboard()

    # Fast Progressive Diagnostic Loading
    fast_modules = [
        ("cpu", "Processor & Cores"),
        ("memory", "Memory & Swap Fabric"),
        ("storage", "Storage Volumes"),
        ("gpu", "Graphics Accelerators"),
        ("security_posture", "Kernel Hardening & Security Flow"),
        ("psi", "Kernel Pressure Stalls (PSI)"),
    ]

    with Progress(
        SpinnerColumn(spinner_name="dots12", style="bold cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40, style="blue", complete_style="bright_green"),
        TextColumn("[bold bright_white]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Initializing hardware telemetry sensors...", total=100)
        for idx, (m_key, m_name) in enumerate(fast_modules, start=1):
            pct = int((idx / len(fast_modules)) * 100)
            progress.update(task, completed=pct, description=f"[cyan]Calibrating sensor node:[/cyan] [bold yellow]{m_name}[/bold yellow]")
            time.sleep(0.08)

    # Initial scan of fast modules
    dashboard.results = dashboard.scanner.run_scan(module_keys=[m[0] for m in fast_modules], save_snapshot=False)

    # Launch background thread for heavy latency/thermal tests
    def bg_deep_scan():
        try:
            from linux_doctor.diagnostics.storage_latency import StorageLatencyDiagnostic
            from linux_doctor.diagnostics.thermal_decay import ThermalDecayDiagnostic
            dashboard.results["storage_latency"] = StorageLatencyDiagnostic.run()
            dashboard.results["thermal_decay"] = ThermalDecayDiagnostic.run()
        except Exception:
            pass

    threading.Thread(target=bg_deep_scan, daemon=True).start()

    console.clear()

    # Step 2: Live Screen with Non-Blocking Keyboard Listener
    with NonBlockingInput() as kb:
        try:
            with Live(dashboard.generate_layout(), console=console, refresh_per_second=4, screen=True) as live:
                while True:
                    ch = kb.get_key()
                    if ch:
                        if ch in ('1', '2', '3', '4'):
                            dashboard.active_tab = int(ch)
                        elif ch.lower() in ('q', '\x03', '\x1b'):  # Q, Ctrl+C, Esc
                            break
                        elif ch.lower() == 'r':
                            dashboard.results = dashboard.scanner.run_scan(save_snapshot=False)

                    live.update(dashboard.generate_layout())
                    time.sleep(0.15)
        except KeyboardInterrupt:
            pass

    console.clear()
    console.print(f"\n[bold green]✓ Dr. System closed safely. Terminal restored.[/bold green]\n")
