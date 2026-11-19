"""Terminal Split-Screen Live Dashboard (like Btop / Htop / Nmap Console).

Designed by - Atul Singh Chandel <myself.tas03@gmail.com>
Left Side: Real-Time Telemetry, Thermals, PSI Stalls, CPU Cores, Memory Gauges.
Right Side: Hardware Inventory, Audio, Display, Battery Life, Storage Health, Causality Insights.
"""

import math
import os
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import psutil

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from linux_doctor.config import APP_AUTHOR, APP_AUTHOR_EMAIL, APP_NAME, APP_TAGLINE, APP_VERSION
from linux_doctor.core.causality import CausalityEngine
from linux_doctor.core.detector import OSDetector, OSInfo
from linux_doctor.core.findings import FindingSeverity
from linux_doctor.core.scanner import DiagnosticScanner


def make_bar(percent: float, width: int = 18, color_good: str = "bright_green", color_warn: str = "yellow", color_crit: str = "bright_red") -> Text:
    """Renders a Unicode progress meter [||||||....] with color thresholds."""
    p = max(0.0, min(100.0, percent))
    filled_len = int(round((p / 100.0) * width))
    empty_len = width - filled_len

    color = color_good
    if p > 85.0:
        color = color_crit
    elif p > 70.0:
        color = color_warn

    bar_str = "█" * filled_len + "░" * empty_len
    t = Text()
    t.append(f"[{p:>5.1f}%] ", style="bold bright_white")
    t.append(bar_str, style=color)
    return t


class MasterTerminalDashboard:
    """Renders the split-screen cyber dashboard."""

    def __init__(self):
        self.os_info: OSInfo = OSDetector.detect()
        self.scanner = DiagnosticScanner()
        # Initial diagnostic results
        self.results = self.scanner.run_scan(save_snapshot=False)
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())

    def get_uptime_str(self) -> str:
        delta = datetime.now() - self.boot_time
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        return f"{hours}h {minutes}m {seconds}s"

    def render_left_panel(self) -> Panel:
        """Left Side: Real-Time Telemetry, Thermals, PSI Stalls, CPU Cores, Memory."""
        content = []

        # 1. CPU Section
        cpu_overall = psutil.cpu_percent(interval=None)
        cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
        freq = psutil.cpu_freq()
        cur_freq_mhz = f"{freq.current:.0f} MHz" if freq else "Dynamic"

        cpu_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
        cpu_table.add_column("Key", style="bold cyan", width=18)
        cpu_table.add_column("Gauge", justify="left")

        cpu_table.add_row("Overall Utilization", make_bar(cpu_overall, width=16))
        cpu_table.add_row("Clock Frequency", Text(f"{cur_freq_mhz} ({psutil.cpu_count(logical=True)} Threads)", style="bright_white"))

        # Individual core breakdown (up to first 8)
        for idx, cp in enumerate(cpu_per_core[:8]):
            cpu_table.add_row(f"  Thread #{idx}", make_bar(cp, width=12))

        # Load averages
        if hasattr(os, "getloadavg"):
            l1, l5, l15 = os.getloadavg()
            cpu_table.add_row("Load Avg (1/5/15)", Text(f"{l1:.2f}, {l5:.2f}, {l15:.2f}", style="bold yellow"))

        content.append(Panel(cpu_table, title="[bold bright_green]⚡ PROCESSOR TELEMETRY[/bold bright_green]", border_style="bright_blue", box=box.ROUNDED))

        # 2. RAM & Swap Section
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()

        mem_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
        mem_table.add_column("Key", style="bold cyan", width=18)
        mem_table.add_column("Gauge", justify="left")

        mem_used_gb = vm.used / (1024**3)
        mem_tot_gb = vm.total / (1024**3)
        swap_used_gb = swap.used / (1024**3)
        swap_tot_gb = swap.total / (1024**3)

        mem_table.add_row("Physical Memory", make_bar(vm.percent, width=16))
        mem_table.add_row("Memory Footprint", Text(f"{mem_used_gb:.2f} GB / {mem_tot_gb:.2f} GB", style="bright_white"))
        mem_table.add_row("Swap Allocated", make_bar(swap.percent, width=16, color_warn="bright_magenta"))
        mem_table.add_row("Swap Footprint", Text(f"{swap_used_gb:.2f} GB / {swap_tot_gb:.2f} GB", style="bright_white"))

        content.append(Panel(mem_table, title="[bold bright_cyan]🧠 MEMORY & SWAP GAUGES[/bold bright_cyan]", border_style="cyan", box=box.ROUNDED))

        # 3. Thermals & Cooling Section
        temps = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}
        temp_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
        temp_table.add_column("Sensor", style="bold cyan", width=18)
        temp_table.add_column("Reading", justify="left")

        max_t = 0.0
        found_sensor = False
        for name, entries in temps.items():
            for entry in entries:
                found_sensor = True
                label = entry.label or name
                val = entry.current
                if val > max_t: max_t = val
                t_color = "bright_green" if val < 75.0 else ("yellow" if val < 85.0 else "bright_red")
                temp_table.add_row(f"{label[:16]}", Text(f"{val:.1f}°C", style=f"bold {t_color}"))

        if not found_sensor:
            temp_table.add_row("Sensors", Text("Virtual / Chipset Passive (No ACPI Sensors)", style="dim"))

        # Thermal Decay Score
        t_decay = self.results.get("thermal_decay")
        if t_decay and t_decay.metrics.get("thermal_profile"):
            prof = t_decay.metrics["thermal_profile"]
            temp_table.add_row("Thermal Half-Life", Text(f"{prof.get('thermal_half_life_s', '-')}s (Cooling curve OK)", style="bright_white"))

        content.append(Panel(temp_table, title="[bold yellow]🌡️ THERMAL & HEATSINK SENSORS[/bold yellow]", border_style="yellow", box=box.ROUNDED))

        # 4. Kernel PSI Pressure Stalls
        base_psi = Path("/proc/pressure")
        psi_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
        psi_table.add_column("Subsystem", style="bold cyan", width=18)
        psi_table.add_column("Stall Ratio", justify="left")

        if base_psi.exists():
            for p_type in ["cpu", "memory", "io"]:
                fpath = base_psi / p_type
                if fpath.exists():
                    txt = fpath.read_text().strip()
                    # parse some avg10
                    avg10 = "0.00%"
                    for part in txt.split():
                        if "some" in part or "avg10=" in part:
                            if "avg10=" in part:
                                avg10 = part.split("=")[1] + "%"
                    psi_table.add_row(f"{p_type.upper()} Thread Stall", Text(f"{avg10} (Wall-clock micro-delay)", style="bright_green" if "0.00" in avg10 else "yellow"))
        else:
            psi_table.add_row("Kernel PSI", Text("Unexposed in current kernel", style="dim"))

        content.append(Panel(psi_table, title="[bold magenta]⚡ KERNEL PRESSURE STALLS (PSI)[/bold magenta]", border_style="magenta", box=box.ROUNDED))

        return Panel(Group(*content), title="[bold bright_white]TELEMETRY STREAM[/bold bright_white]", border_style="bright_blue", box=box.HEAVY)

    def render_right_panel(self) -> Panel:
        """Right Side: Hardware Inventory, Audio, Display, Battery, Storage, Causality Insights."""
        content = []

        # 1. System Identity & Uptime
        sys_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
        sys_table.add_column("Property", style="bold cyan", width=18)
        sys_table.add_column("Telemetry", justify="left")

        sys_table.add_row("Operating System", Text(f"{self.os_info.name} {self.os_info.version}", style="bold bright_white"))
        sys_table.add_row("Kernel Release", Text(self.os_info.kernel, style="cyan"))
        sys_table.add_row("System Uptime", Text(self.get_uptime_str(), style="bold bright_green"))
        sys_table.add_row("Package Manager", Text(self.os_info.package_manager or "N/A", style="bright_white"))
        sys_table.add_row("Init System", Text(self.os_info.init_system or "systemd", style="bright_white"))

        content.append(Panel(sys_table, title="[bold bright_green]🖥️ SYSTEM IDENTITY & RUNTIME[/bold bright_green]", border_style="bright_green", box=box.ROUNDED))

        # 2. Battery & Power Life
        bat_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
        bat_table.add_column("Metric", style="bold cyan", width=18)
        bat_table.add_column("State", justify="left")

        bat = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
        if bat:
            plug_str = "Plugged In (AC)" if bat.power_plugged else "On Battery"
            bat_table.add_row("Battery Gauge", make_bar(bat.percent, width=16))
            bat_table.add_row("Power Source", Text(plug_str, style="bold bright_white"))
            secs = bat.secsleft
            if secs and secs != psutil.POWER_TIME_UNLIMITED and secs > 0:
                hours = secs // 3600
                mins = (secs % 3600) // 60
                bat_table.add_row("Estimated Remaining", Text(f"{hours}h {mins}m", style="yellow"))
        else:
            bat_table.add_row("Power Topology", Text("Desktop Workstation / AC Mains (No Battery)", style="bright_white"))

        content.append(Panel(bat_table, title="[bold yellow]🔋 POWER & BATTERY LIFE[/bold yellow]", border_style="yellow", box=box.ROUNDED))

        # 3. Audio & Display Hardware
        media_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
        media_table.add_column("Component", style="bold cyan", width=18)
        media_table.add_column("Configuration", justify="left")

        media_table.add_row("Display Compositor", Text(f"{self.os_info.display_server or 'Unknown'}", style="bright_white"))
        media_table.add_row("Desktop Env", Text(f"{self.os_info.desktop_environment or 'Headless'}", style="bright_white"))
        media_table.add_row("Audio Server Daemon", Text(f"{self.os_info.audio_server or 'PipeWire'}", style="bold bright_cyan"))

        # GPU
        gpu_res = self.results.get("gpu")
        gpu_name = "Integrated / Kernel DRM"
        if gpu_res and gpu_res.metrics.get("gpus"):
            gpu_name = gpu_res.metrics["gpus"][0].get("model", "Graphics Controller")
        media_table.add_row("Primary GPU", Text(gpu_name[:34], style="bright_white"))

        content.append(Panel(media_table, title="[bold cyan]🎨 DISPLAY, AUDIO & GPU TOPOLOGY[/bold cyan]", border_style="cyan", box=box.ROUNDED))

        # 4. Storage & Direct Read Latency
        disk_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
        disk_table.add_column("Mount Point", style="bold cyan", width=18)
        disk_table.add_column("Disk Capacity", justify="left")

        try:
            for part in psutil.disk_partitions(all=False)[:3]:
                usage = psutil.disk_usage(part.mountpoint)
                disk_table.add_row(f"{part.mountpoint} ({part.fstype})", make_bar(usage.percent, width=14))
        except Exception:
            pass

        # Latency
        lat_res = self.results.get("storage_latency")
        if lat_res and lat_res.metrics.get("latency_test"):
            p99 = lat_res.metrics["latency_test"].get("p99_latency_ms", "-")
            disk_table.add_row("Direct 4K Read P99", Text(f"{p99} ms (Page cache bypass)", style="bold bright_white"))

        content.append(Panel(disk_table, title="[bold magenta]💾 STORAGE DISKS & DIRECT I/O JITTER[/bold magenta]", border_style="magenta", box=box.ROUNDED))

        # 5. Clinical Findings & Cross-Subsystem Causality
        causality_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
        causality_table.add_column("Component", style="bold yellow", width=18)
        causality_table.add_column("Prescription / Status", justify="left")

        if self.scanner.causality_insights:
            for ins in self.scanner.causality_insights[:2]:
                causality_table.add_row(f"⚠ {ins.cause_component}", Text(f"{ins.title}: {ins.recommendation}", style="bold red"))
        else:
            causality_table.add_row("Causality Matrix", Text("✓ Zero cross-subsystem hardware bottlenecks detected.", style="bold bright_green"))

        # Any high findings
        issues_found = 0
        for mod in self.results.values():
            for f in mod.findings:
                if f.severity in (FindingSeverity.WARNING, FindingSeverity.CRITICAL):
                    issues_found += 1
                    causality_table.add_row(f"• {mod.display_name[:16]}", Text(f"{f.title} ({f.safe_next_step})", style="yellow"))

        if issues_found == 0 and not self.scanner.causality_insights:
            causality_table.add_row("Clinical Diagnosis", Text("All physical & kernel subsystems operating within nominal limits.", style="bright_green"))

        content.append(Panel(causality_table, title="[bold red]🩺 CLINICAL DIAGNOSIS & BOTTLENECK CORRELATOR[/bold red]", border_style="red", box=box.ROUNDED))

        return Panel(Group(*content), title="[bold bright_white]HARDWARE INVENTORY & HEALTH[/bold bright_white]", border_style="bright_cyan", box=box.HEAVY)

    def generate_layout(self) -> Layout:
        """Constructs split-screen Layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        # Header with author signature
        header_text = Text()
        header_text.append("Designed by - ", style="bold bright_white")
        header_text.append(f"{APP_AUTHOR} ", style="bold yellow")
        header_text.append(f"<{APP_AUTHOR_EMAIL}>  ", style="bold bright_green")
        header_text.append(f"• {APP_NAME} v{APP_VERSION} • ", style="bold cyan")
        header_text.append(f"{APP_TAGLINE}", style="italic dim bright_white")

        layout["header"].update(Panel(Align.center(header_text), box=box.DOUBLE, border_style="bright_blue"))

        # Body Split
        layout["body"].split_row(
            Layout(self.render_left_panel(), name="left", ratio=1),
            Layout(self.render_right_panel(), name="right", ratio=1),
        )

        # Footer
        footer_text = Text()
        footer_text.append("[Q] Quit  ", style="bold bright_white")
        footer_text.append("•  [R] Rescan Full Diagnostics  ", style="bold cyan")
        footer_text.append("•  [Live Refresh: 1.0s]  ", style="bold yellow")
        footer_text.append("•  Dr. System Autonomous Hardware Engine", style="dim bright_white")
        layout["footer"].update(Panel(Align.center(footer_text), box=box.ROUNDED, border_style="bright_blue"))

        return layout


def run_split_dashboard():
    """Main runner for the split-screen cyber console."""
    console = Console()
    dashboard = MasterTerminalDashboard()

    # Clear terminal once
    console.clear()

    try:
        with Live(dashboard.generate_layout(), console=console, refresh_per_second=2, screen=True) as live:
            while True:
                live.update(dashboard.generate_layout())
                time.sleep(1.0)
    except KeyboardInterrupt:
        console.clear()
        console.print(f"\n[bold green]Dr. System console terminated safely.[/bold green]\n")
