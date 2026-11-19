"""Command Line Interface (Linux Doctor 2.0).

Supports full scans, real-time PSI diagnostics, direct storage latency testing,
thermal decay profiling, causality insights, and differential snapshots.
"""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from linux_doctor.config import APP_AUTHOR, APP_NAME, APP_TAGLINE, APP_VERSION
from linux_doctor.core.detector import OSDetector
from linux_doctor.core.findings import FindingSeverity
from linux_doctor.core.scanner import DiagnosticScanner
from linux_doctor.core.snapshots import SnapshotManager
from linux_doctor.reports.generator import ReportGenerator

app = typer.Typer(help=f"{APP_NAME} 2.0 - {APP_TAGLINE}")
console = Console()


@app.command()
def version():
    """Display Linux Doctor version and creator information."""
    console.print(
        Panel(
            f"[bold green]{APP_NAME}[/bold green] v[cyan]{APP_VERSION}[/cyan] (Next-Gen Autonomous Diagnostic Engine)\n"
            f"[dim]{APP_TAGLINE}[/dim]\n\n"
            f"Creator: [yellow]{APP_AUTHOR}[/yellow]",
            title="Version Info",
            border_style="green",
        )
    )


@app.command()
def info():
    """Display detected operating system environment and architecture."""
    os_info = OSDetector.detect()
    table = Table(title="Detected System Environment", border_style="cyan")
    table.add_column("Property", style="bold cyan")
    table.add_column("Detected Value", style="white")

    table.add_row("Operating System", os_info.system)
    table.add_row("Distribution / Edition", os_info.name)
    table.add_row("Version", os_info.version)
    table.add_row("Kernel Release", os_info.kernel)
    table.add_row("CPU Architecture", os_info.architecture)
    table.add_row("Package Manager", os_info.package_manager or "N/A")
    table.add_row("Desktop Environment", os_info.desktop_environment or "None (Headless/TTY)")
    table.add_row("Display Server", os_info.display_server or "Unknown")
    table.add_row("Init System", os_info.init_system or "Unknown")
    table.add_row("Audio Server", os_info.audio_server or "Unknown")

    console.print(table)


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
):
    """Run diagnostics and calculate PC Health Score."""
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
    console.print(f"[bold cyan]Starting {APP_NAME} 2.0 Autonomous Diagnostic Scan...[/bold cyan]")

    def on_progress(mod_name: str, current: int, total: int, res):
        if res is None:
            console.print(f"  [dim]Scanning ({current}/{total}):[/dim] {mod_name}...")

    results = scanner.run_scan(module_keys=module_keys, progress_callback=on_progress)
    report = scanner.score_report

    # Overall Summary
    color = "green"
    if report.overall_score < 60:
        color = "red"
    elif report.overall_score < 75:
        color = "yellow"

    console.print()
    console.print(
        Panel(
            f"[bold {color}]SYSTEM HEALTH: {report.overall_score} / 100 ({report.status_label})[/bold {color}]\n"
            f"[dim]Confidence: {int(report.confidence * 100)}% | Coverage: {report.coverage_percentage}% | Time: {scanner.scan_duration_seconds}s[/dim]",
            title="Scan Summary",
            border_style=color,
        )
    )

    # Categories Table
    table = Table(title="Category Health Ratings", border_style="dim")
    table.add_column("Category", style="cyan")
    table.add_column("Score", style="bold")
    table.add_column("Status", style="white")

    for key, mod in results.items():
        st_color = "green" if mod.status == "passed" else ("yellow" if mod.status == "warning" else "red")
        table.add_row(
            mod.display_name,
            f"{mod.score:.1f}/100",
            f"[{st_color}]{mod.status.upper()}[/{st_color}]"
        )
    console.print(table)

    # Cross-Subsystem Causality Insights
    if scanner.causality_insights:
        console.print()
        for insight in scanner.causality_insights:
            console.print(
                Panel(
                    f"[bold yellow]Root Cause Component:[/bold yellow] {insight.cause_component}\n"
                    f"[bold yellow]Affected Subsystem:[/bold yellow]   {insight.affected_component}\n\n"
                    f"{insight.explanation}\n\n"
                    f"[bold green]Autonomous Recommendation:[/bold green] {insight.recommendation}",
                    title=f"[bold cyan]CROSS-SUBSYSTEM CAUSALITY: {insight.title}[/bold cyan]",
                    border_style="cyan",
                )
            )

    # Show Findings
    has_issues = False
    for key, mod in results.items():
        for finding in mod.findings:
            if finding.severity in (FindingSeverity.WARNING, FindingSeverity.CRITICAL):
                has_issues = True
                f_color = "red" if finding.severity == FindingSeverity.CRITICAL else "yellow"
                console.print(
                    Panel(
                        f"[bold]Detected:[/bold] {finding.what_detected}\n"
                        f"[bold]Meaning:[/bold] {finding.what_it_means}\n"
                        f"[bold]Safe Next Step:[/bold] [green]{finding.safe_next_step}[/green]",
                        title=f"[{f_color}]ISSUE: {finding.title} ({mod.display_name})[/{f_color}]",
                        border_style=f_color,
                    )
                )

    if not has_issues and not scanner.causality_insights:
        console.print("[bold green]✓ No critical or warning-level issues detected![/bold green]")


@app.command()
def diff():
    """Compare the last two diagnostic snapshots to find regressions."""
    snaps = SnapshotManager.list_snapshots()
    if len(snaps) < 2:
        console.print("[yellow]At least 2 diagnostic snapshots are required to compute a differential comparison. Run 'linux-doctor scan' first.[/yellow]")
        return

    latest = snaps[0]
    previous = snaps[1]
    comparison = SnapshotManager.compare_snapshots(previous, latest)

    console.print(
        Panel(
            f"Comparing:\n"
            f"  • Previous: [cyan]{comparison['old_date']}[/cyan] (Score: {comparison['overall_score_old']}/100)\n"
            f"  • Current:  [cyan]{comparison['new_date']}[/cyan] (Score: {comparison['overall_score_new']}/100)\n"
            f"  • Delta:    [{'green' if comparison['score_diff'] >= 0 else 'red'}]{comparison['score_diff']:+d} points[/{'green' if comparison['score_diff'] >= 0 else 'red'}]",
            title="Time-Travel Snapshot Comparison",
            border_style="cyan",
        )
    )

    if comparison["regressions"]:
        for reg in comparison["regressions"]:
            console.print(f"[bold red]▼ REGRESSION:[/bold red] {reg}")
    if comparison["improvements"]:
        for imp in comparison["improvements"]:
            console.print(f"[bold green]▲ IMPROVEMENT:[/bold green] {imp}")
    if not comparison["regressions"] and not comparison["improvements"]:
        console.print("[green]✓ System metrics are stable across snapshots with no detected regressions.[/green]")


@app.command()
def report(
    format: str = typer.Option("txt", "--format", "-f", help="Output format: txt, json, html"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="File path to save the report"),
    anonymize: bool = typer.Option(True, "--anonymize/--no-anonymize", help="Redact personal IP & usernames"),
):
    """Run full diagnostics and export a professional report."""
    scanner = DiagnosticScanner()
    console.print(f"[dim]Generating diagnostic report ({format.upper()})...[/dim]")
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
        console.print(f"[bold green]✓ Report saved successfully to {out_path.resolve()}[/bold green]")
    else:
        console.print(content)
