"""Live System Doctor & Diagnostic Command Center (like Nmap/Htop).

Styled with custom cyber-hacker aesthetic:
Designed by - Atul Singh Chandel <myself.tas03@gmail.com>
Dr. System - Know your PC. Understand its health.
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import typer
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
import psutil

from linux_doctor.config import APP_AUTHOR, APP_AUTHOR_EMAIL, APP_NAME, APP_TAGLINE, APP_VERSION
from linux_doctor.core.causality import CausalityEngine
from linux_doctor.core.detector import OSDetector
from linux_doctor.core.findings import FindingSeverity
from linux_doctor.core.scanner import DiagnosticScanner
from linux_doctor.core.snapshots import SnapshotManager
from linux_doctor.maintenance.repair import SafeMaintenanceEngine
from linux_doctor.reports.generator import ReportGenerator

app = typer.Typer(help=f"{APP_NAME} - Terminal Diagnostic & Hardware Doctor", add_completion=False)
console = Console()

BANNER_ART = r"""[bold cyan]
 ____             ____            _                 
|  _ \ _ __      / ___| _   _ ___| |_ ___ _ __ ___  
| | | | '__|_____\___ \| | | / __| __/ _ \ '_ ` _ \ 
| |_| | | |_____| ___) | |_| \__ \ ||  __/ | | | | |
|____/|_|        |____/ \__, |___/\__\___|_| |_| |_|
                        |___/                       
[/bold cyan]"""


def print_header(compact: bool = False):
    """Always prints the official, styled author signature and header."""
    if not compact:
        console.print(Align.center(BANNER_ART))
    
    header_text = Text()
    header_text.append("Designed by - ", style="bold bright_white")
    header_text.append(f"{APP_AUTHOR} ", style="bold yellow")
    header_text.append(f"<{APP_AUTHOR_EMAIL}>\n", style="bold green")
    header_text.append(f"• {APP_NAME} v{APP_VERSION} • ", style="bold cyan")
    header_text.append(f"{APP_TAGLINE}", style="italic dim bright_white")

    panel = Panel(
        Align.center(header_text),
        box=box.DOUBLE,
        border_style="bright_blue",
        padding=(0, 2),
    )
    console.print(panel)


@app.command()
def info():
    """Display in-depth detected operating system environment and architecture."""
    print_header()
    os_info = OSDetector.detect()

    table = Table(
        title="[bold green]HARDWARE & PLATFORM TOPOLOGY[/bold green]",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
    )
    table.add_column("Subsystem Property", style="bold cyan", width=26)
    table.add_column("Detected Telemetry", style="bright_white")

    table.add_row("Operating System", f"[bold green]{os_info.system}[/bold green]")
    table.add_row("Distribution / Edition", f"[yellow]{os_info.name}[/yellow]")
    table.add_row("Release Version", os_info.version)
    table.add_row("Kernel Release", f"[cyan]{os_info.kernel}[/cyan]")
    table.add_row("CPU Architecture", f"[bold magenta]{os_info.architecture}[/bold magenta]")
    table.add_row("Package Manager", f"[green]{os_info.package_manager or 'N/A'}[/green]")
    table.add_row("Desktop Environment", os_info.desktop_environment or "Headless / Server TTY")
    table.add_row("Display Compositor", os_info.display_server or "Headless")
    table.add_row("Init System Daemon", os_info.init_system or "Unknown")
    table.add_row("Sound Server", os_info.audio_server or "Unknown")

    console.print(table)
    console.print(f"[dim]All telemetry queried locally with zero external network transmission.[/dim]\n")


@app.command()
def live():
    """Launch the split-screen cyber hardware console."""
    from linux_doctor.cli.split_dashboard import run_split_dashboard
    run_split_dashboard()


@app.command()
def uninstall(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Completely remove Dr. System symlinks, desktop entries, and snapshots."""
    print_header(compact=True)
    if not yes:
        confirm = typer.confirm("Are you sure you want to completely uninstall Dr. System?")
        if not confirm:
            console.print("[green]Uninstallation aborted. No changes made.[/green]")
            raise typer.Exit()

    # 1. Remove symlinks
    bin_paths = [
        Path.home() / ".local" / "bin" / "dr-system",
        Path.home() / ".local" / "bin" / "dr-system-gui",
        Path.home() / ".local" / "bin" / "linux-doctor",
        Path.home() / ".local" / "bin" / "linux-doctor-gui",
    ]
    for bp in bin_paths:
        if bp.exists() or bp.is_symlink():
            bp.unlink(missing_ok=True)
            console.print(f"[dim]Removed binary link: {bp}[/dim]")

    # 2. Remove desktop shortcut
    desktop_file = Path.home() / ".local" / "share" / "applications" / "linux-doctor.desktop"
    if desktop_file.exists():
        desktop_file.unlink(missing_ok=True)
        console.print(f"[dim]Removed desktop shortcut: {desktop_file}[/dim]")

    # 3. Remove snapshot records
    snap_dir = Path.home() / ".config" / "linux-doctor"
    if snap_dir.exists():
        shutil.rmtree(snap_dir, ignore_errors=True)
        console.print(f"[dim]Removed config & snapshots: {snap_dir}[/dim]")

    console.print("\n[bold green]✓ Dr. System successfully uninstalled from your system.[/bold green]")
    console.print("[dim]To delete the cloned source folder, run: cd .. && rm -rf dr.system[/dim]\n")


@app.command()
def scan(
    full: bool = typer.Option(True, "--full", help="Perform complete system diagnostic"),
    cpu: bool = typer.Option(False, "--cpu", help="Scan CPU only"),
    memory: bool = typer.Option(False, "--memory", "--ram", help="Scan Memory (RAM) only"),
    storage: bool = typer.Option(False, "--storage", "--disk", help="Scan Storage only"),
    latency: bool = typer.Option(False, "--latency", help="Run direct 4K read latency test"),
    thermal_decay: bool = typer.Option(False, "--thermal-decay", help="Run thermal dissipation profiler"),
    psi: bool = typer.Option(False, "--psi", help="Scan kernel pressure stalls (PSI)"),
    gpu: bool = typer.Option(False, "--gpu", help="Scan GPU only"),
    battery: bool = typer.Option(False, "--battery", help="Scan Battery only"),
    network: bool = typer.Option(False, "--network", help="Scan Network only"),
    display: bool = typer.Option(False, "--display", help="Scan Display only"),
    audio: bool = typer.Option(False, "--audio", help="Scan Audio only"),
    save_report: bool = typer.Option(False, "--save", help="Automatically save diagnostic report"),
):
    """Run interactive Nmap-style PC health diagnostic & scoring scan."""
    print_header()

    module_keys = None
    specified = []
    if cpu: specified.append("cpu")
    if memory: specified.append("memory")
    if storage: specified.append("storage")
    if latency: specified.append("storage_latency")
    if thermal_decay: specified.append("thermal_decay")
    if psi: specified.append("psi")
    if gpu: specified.append("gpu")
    if battery: specified.append("battery")
    if network: specified.append("network")
    if display: specified.append("display")
    if audio: specified.append("audio")

    if specified:
        module_keys = specified

    scanner = DiagnosticScanner()
    console.print(f"[bold bright_green]>>> INITIALIZING CLINICAL HARDWARE AUDIT...[/bold bright_green]\n")

    # Animated Progress Bar (like Nmap/Metasploit)
    with Progress(
        SpinnerColumn(spinner_name="dots12", style="bold cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40, style="blue", complete_style="bright_green"),
        TextColumn("[bold bright_white]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task_id = progress.add_task("[cyan]Starting diagnostic modules...", total=100)

        def on_progress(mod_name: str, current: int, total: int, res):
            pct = (current / total) * 100
            if res is None:
                progress.update(task_id, completed=pct, description=f"[cyan]Auditing subsystem:[/cyan] [bold yellow]{mod_name}[/bold yellow] ({current}/{total})")
            else:
                st_color = "bright_green" if res.status == "passed" else ("yellow" if res.status == "warning" else "bright_red")
                progress.update(task_id, completed=pct, description=f"[{st_color}]Completed:[/{st_color}] {mod_name} [{st_color}OK[/{st_color}]")

        results = scanner.run_scan(module_keys=module_keys, progress_callback=on_progress)
        progress.update(task_id, completed=100, description="[bold bright_green]All diagnostic procedures completed![/bold bright_green]")

    report = scanner.score_report
    console.print()

    # Score Gauge Box
    score_color = "bright_green"
    if report.overall_score < 60:
        score_color = "bright_red"
    elif report.overall_score < 75:
        score_color = "yellow"

    gauge_text = (
        f"[bold bright_white]SYSTEM CLINICAL HEALTH SCORE:[/bold bright_white] "
        f"[bold {score_color}]{report.overall_score} / 100[/bold {score_color}] "
        f"([bold {score_color}]{report.status_label}[/bold {score_color}])\n"
        f"[dim bright_white]Sensor Confidence: {int(report.confidence * 100)}% | Test Coverage: {report.coverage_percentage}% | Elapsed: {scanner.scan_duration_seconds}s[/dim bright_white]"
    )
    console.print(Panel(gauge_text, box=box.HEAVY, border_style=score_color, title=f"[bold]CLINICAL EVALUATION[/bold]"))

    # Category Breakdown Table
    table = Table(
        title="[bold cyan]SUBSYSTEM CLINICAL AUDIT RATINGS[/bold cyan]",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold magenta",
    )
    table.add_column("Subsystem", style="bold cyan")
    table.add_column("Efficiency Score", justify="center", style="bold bright_white")
    table.add_column("Diagnostics", justify="center")
    table.add_column("Key Telemetry Measurement", style="dim bright_white")

    for key, mod in results.items():
        st_color = "bright_green" if mod.status == "passed" else ("yellow" if mod.status == "warning" else "bright_red")
        status_tag = f"[{st_color}]● {mod.status.upper()}[/{st_color}]"

        # Extract compact key metric
        key_metric = "-"
        if key == "cpu":
            key_metric = f"{mod.metrics.get('logical_cores')} threads | load: {mod.metrics.get('load_average', ['-'])[0]}"
        elif key == "memory":
            key_metric = f"{mod.metrics.get('used_ram_gb')}/{mod.metrics.get('total_ram_gb')} GB ({mod.metrics.get('ram_used_percent')}%)"
        elif key == "storage":
            key_metric = f"{mod.metrics.get('free_storage_gb')} GB free space"
        elif key == "storage_latency":
            lat = mod.metrics.get("latency_test", {})
            key_metric = f"P99 latency: {lat.get('p99_latency_ms', '-')}ms"
        elif key == "thermal_decay":
            prof = mod.metrics.get("thermal_profile", {})
            key_metric = f"Peak: {prof.get('peak_temp_c', '-')}°C (rise: +{prof.get('temperature_delta_c', '-')}°C)"
        elif key == "psi":
            psi_io = mod.metrics.get("io", {}).get("full", {}).get("avg10", 0.0)
            key_metric = f"I/O thread stall ratio: {psi_io:.2f}%"
        elif key == "network":
            key_metric = "Connected" if mod.metrics.get("internet_connectivity") else "Offline"

        table.add_row(mod.display_name, f"{mod.score:.1f}/100", status_tag, key_metric)

    console.print(table)

    # Cross-Subsystem Causality Engine Insights
    if scanner.causality_insights:
        console.print()
        for insight in scanner.causality_insights:
            c_text = (
                f"[bold red]ROOT CAUSE TRIGGER:[/bold red] [yellow]{insight.cause_component}[/yellow]\n"
                f"[bold red]AFFECTED SUBSYSTEM:[/bold red]  [cyan]{insight.affected_component}[/cyan]\n\n"
                f"{insight.explanation}\n\n"
                f"[bold green]RECOMMENDED PRESCRIPTION:[/bold green] {insight.recommendation}"
            )
            console.print(
                Panel(
                    c_text,
                    box=box.DOUBLE,
                    border_style="bright_magenta",
                    title="[bold yellow]⚠ CROSS-SUBSYSTEM CAUSALITY CORRELATION[/bold yellow]",
                )
            )

    # Detailed Findings & Prescriptions
    has_issues = False
    for key, mod in results.items():
        for finding in mod.findings:
            if finding.severity in (FindingSeverity.WARNING, FindingSeverity.CRITICAL):
                has_issues = True
                f_color = "bright_red" if finding.severity == FindingSeverity.CRITICAL else "yellow"
                f_text = (
                    f"[bold bright_white]1. What Was Detected:[/bold bright_white]\n   {finding.what_detected}\n\n"
                    f"[bold bright_white]2. Clinical Meaning:[/bold bright_white]\n   {finding.what_it_means}\n\n"
                    f"[bold bright_white]3. Safe Next Step:[/bold bright_white]\n   [bold green]{finding.safe_next_step}[/bold green]"
                )
                console.print(
                    Panel(
                        f_text,
                        box=box.ROUNDED,
                        border_style=f_color,
                        title=f"[{f_color}]DIAGNOSTIC PRESCRIPTION: {finding.title} ({mod.display_name})[/{f_color}]",
                    )
                )

    if not has_issues and not scanner.causality_insights:
        console.print("\n[bold bright_green]✓ CLEAN BILL OF HEALTH: All system sensors and performance thresholds normal.[/bold bright_green]")

    if save_report:
        out_file = Path(f"dr_system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        out_file.write_text(ReportGenerator.to_txt(scanner.os_info, report, results), encoding="utf-8")
        console.print(f"\n[bold green]✓ Diagnostic report saved to: {out_file.resolve()}[/bold green]")


@app.command()
def monitor(
    refresh: float = typer.Option(1.5, "--interval", "-i", help="Refresh interval in seconds"),
    duration: int = typer.Option(30, "--duration", "-d", help="Total monitor duration in seconds (0 for indefinite)"),
):
    """Real-time live terminal dashboard (like Htop/Btop) with PSI, thermals, and memory."""
    print_header(compact=True)
    console.print("[dim]Press Ctrl+C to exit live monitor...[/dim]\n")

    start_t = time.time()
    try:
        with Live(console=console, refresh_per_second=2) as live:
            while duration == 0 or (time.time() - start_t < duration):
                cpu_p = psutil.cpu_percent(interval=None)
                vm = psutil.virtual_memory()
                swap = psutil.swap_memory()
                temps = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}
                
                max_t = None
                for entries in temps.values():
                    for e in entries:
                        if max_t is None or e.current > max_t:
                            max_t = e.current

                # Live table
                table = Table(
                    title=f"[bold bright_green]{APP_NAME} LIVE TELEMETRY[/bold bright_green] • {datetime.now().strftime('%H:%M:%S')}",
                    box=box.ROUNDED,
                    border_style="bright_blue",
                )
                table.add_column("Metric", style="bold cyan", width=22)
                table.add_column("Live Measurement", style="bold bright_white")
                table.add_column("Status / Threshold", style="bright_green")

                # CPU
                cpu_color = "bright_green" if cpu_p < 75 else ("yellow" if cpu_p < 90 else "bright_red")
                table.add_row("CPU Utilization", f"[{cpu_color}]{cpu_p:.1f}%[/{cpu_color}]", f"[{cpu_color}]{'NORMAL' if cpu_p < 75 else 'ELEVATED'}[/{cpu_color}]")

                # RAM
                ram_color = "bright_green" if vm.percent < 80 else ("yellow" if vm.percent < 90 else "bright_red")
                table.add_row("Physical Memory", f"[{ram_color}]{vm.used / (1024**3):.2f} / {vm.total / (1024**3):.2f} GB ({vm.percent}%)[/{ram_color}]", f"[{ram_color}]{'HEALTHY' if vm.percent < 80 else 'HEAVY'}[/{ram_color}]")

                # Swap
                table.add_row("Swap Usage", f"{swap.used / (1024**3):.2f} / {swap.total / (1024**3):.2f} GB ({swap.percent}%)", "OK" if swap.percent < 50 else "SWAPPING")

                # Temp
                if max_t is not None:
                    t_color = "bright_green" if max_t < 75 else ("yellow" if max_t < 85 else "bright_red")
                    table.add_row("Peak Temperature", f"[{t_color}]{max_t:.1f}°C[/{t_color}]", f"[{t_color}]{'COOL' if max_t < 75 else 'WARM'}[/{t_color}]")

                # Kernel PSI
                base = Path("/proc/pressure")
                if base.exists():
                    io_psi = (base / "io").read_text() if (base / "io").exists() else ""
                    table.add_row("Kernel I/O Stalls", "0.0% full stall" if "full avg10=0.00" in io_psi else "Stalls Detected", "SMOOTH")

                live.update(table)
                time.sleep(refresh)
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Live telemetry monitor stopped.[/bold cyan]")


@app.command()
def diff():
    """Compare the last two diagnostic scans to find hardware regressions."""
    print_header()
    snaps = SnapshotManager.list_snapshots()
    if len(snaps) < 2:
        console.print("[yellow]At least 2 diagnostic snapshots are required to compute a differential comparison. Run 'dr-system scan' first.[/yellow]")
        return

    latest = snaps[0]
    previous = snaps[1]
    comparison = SnapshotManager.compare_snapshots(previous, latest)

    d_text = (
        f"Comparing Historical Diagnostic Records:\n"
        f"  • Previous Record: [cyan]{comparison['old_date']}[/cyan] (Score: {comparison['overall_score_old']}/100)\n"
        f"  • Current Record:  [cyan]{comparison['new_date']}[/cyan] (Score: {comparison['overall_score_new']}/100)\n"
        f"  • Health Delta:    [{'green' if comparison['score_diff'] >= 0 else 'red'}]{comparison['score_diff']:+d} points[/{'green' if comparison['score_diff'] >= 0 else 'red'}]"
    )
    console.print(Panel(d_text, box=box.ROUNDED, border_style="cyan", title="[bold]TIME-TRAVEL REGRESSION AUDIT[/bold]"))

    if comparison["regressions"]:
        for reg in comparison["regressions"]:
            console.print(f"[bold red]▼ REGRESSION DETECTED:[/bold red] {reg}")
    if comparison["improvements"]:
        for imp in comparison["improvements"]:
            console.print(f"[bold green]▲ CLINICAL IMPROVEMENT:[/bold green] {imp}")
    if not comparison["regressions"] and not comparison["improvements"]:
        console.print("[bold green]✓ System telemetry is consistent with no detected performance regressions.[/bold green]")


@app.command()
def report(
    format: str = typer.Option("txt", "--format", "-f", help="Output format: txt, json, html"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="File path to save the report"),
    anonymize: bool = typer.Option(True, "--anonymize/--no-anonymize", help="Redact personal IP & usernames"),
):
    """Run full diagnostics and export a professional diagnostic report."""
    print_header(compact=True)
    scanner = DiagnosticScanner()
    console.print(f"[dim]Running diagnostics for clinical report generation ({format.upper()})...[/dim]")
    results = scanner.run_scan()
    report_data = scanner.score_report

    fmt = format.lower()
    if fmt == "json":
        content = ReportGenerator.to_json(scanner.os_info, report_data, results, anonymize)
    elif fmt == "html":
        content = ReportGenerator.to_html(scanner.os_info, report_data, results, anonymize)
    else:
        content = ReportGenerator.to_txt(scanner.os_info, report_data, results, anonymize)

    if output:
        out_path = Path(output)
        out_path.write_text(content, encoding="utf-8")
        console.print(f"[bold green]✓ Diagnostic report successfully saved to {out_path.resolve()}[/bold green]")
    else:
        console.print(content)
