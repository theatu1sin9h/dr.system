"""Memory (RAM) Diagnostic Module.

Detects total capacity, available RAM, swap utilization, memory pressure,
and memory exhaustion warnings without performing destructive operations.
"""

import time
from typing import Any, Dict, List
import psutil
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult


class MemoryDiagnostic:
    """Diagnoses physical RAM and swap health safely."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        score = 100.0
        deductions_exp: List[str] = []

        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()

        total_gb = round(vm.total / (1024**3), 2)
        used_gb = round((vm.total - vm.available) / (1024**3), 2)
        avail_gb = round(vm.available / (1024**3), 2)
        used_pct = vm.percent

        metrics["total_ram_gb"] = total_gb
        metrics["used_ram_gb"] = used_gb
        metrics["available_ram_gb"] = avail_gb
        metrics["ram_used_percent"] = used_pct

        swap_total_gb = round(swap.total / (1024**3), 2)
        swap_used_gb = round(swap.used / (1024**3), 2)
        swap_pct = swap.percent

        metrics["swap_total_gb"] = swap_total_gb
        metrics["swap_used_gb"] = swap_used_gb
        metrics["swap_used_percent"] = swap_pct

        # Check critical RAM exhaustion
        if used_pct >= 95.0:
            findings.append(
                DiagnosticFinding(
                    id="ram_exhaustion_critical",
                    title="Critical Memory Pressure (RAM Nearly Full)",
                    severity=FindingSeverity.CRITICAL,
                    what_detected=f"RAM usage is currently at {used_pct}% ({avail_gb} GB remaining).",
                    what_it_means="The system is running dangerously low on physical memory and may trigger OOM (Out-Of-Memory) killer or freeze.",
                    how_serious="High. Active programs may crash or close unexpectedly.",
                    what_could_cause="Memory leaks, high-footprint web browser tabs, virtual machines, or heavy databases.",
                    what_user_should_do="Save work in progress immediately and close unnecessary memory-intensive applications.",
                    safe_next_step="Identify top memory-consuming applications and close non-critical ones.",
                    technical_details={"used_pct": used_pct, "available_gb": avail_gb, "total_gb": total_gb},
                    is_hardware_degradation=False,
                    deduction_points=35.0,
                )
            )
            score -= 35.0
            deductions_exp.append("Critical RAM exhaustion (-35 pts)")
        elif used_pct >= 85.0:
            findings.append(
                DiagnosticFinding(
                    id="ram_high_pressure",
                    title="Elevated Memory Usage",
                    severity=FindingSeverity.WARNING,
                    what_detected=f"RAM usage is elevated at {used_pct}%.",
                    what_it_means="The operating system is caching or using most available RAM.",
                    how_serious="Moderate. Some paging may occur.",
                    what_could_cause="Multiple concurrent applications or large datasets in memory.",
                    what_user_should_do="Monitor memory consumption if multitasking slows down.",
                    safe_next_step="Check memory footprint in task manager.",
                    technical_details={"used_pct": used_pct, "available_gb": avail_gb},
                    is_hardware_degradation=False,
                    deduction_points=15.0,
                )
            )
            score -= 15.0
            deductions_exp.append("Elevated RAM usage (-15 pts)")

        # Check Swap status
        if swap_total_gb == 0 and total_gb < 8.0:
            findings.append(
                DiagnosticFinding(
                    id="swap_missing_low_ram",
                    title="No Swap Space Configured on Low Memory System",
                    severity=FindingSeverity.WARNING,
                    what_detected="System has no active swap space configured while having under 8GB RAM.",
                    what_it_means="Without swap, sudden memory spikes cannot be safely paged out, leading to sudden app termination.",
                    how_serious="Moderate on systems with limited memory.",
                    what_could_cause="Swap partition or swapfile was not created during installation.",
                    what_user_should_do="Consider creating a safe swapfile (e.g. 2GB–4GB) to avoid unexpected OOM crashes.",
                    safe_next_step="Review system swap guidelines for your distribution.",
                    technical_details={"swap_total_gb": 0, "total_ram_gb": total_gb},
                    is_hardware_degradation=False,
                    deduction_points=10.0,
                )
            )
            score -= 10.0
            deductions_exp.append("No swap configured on low RAM system (-10 pts)")
        elif swap_pct >= 90.0 and swap_total_gb > 0:
            findings.append(
                DiagnosticFinding(
                    id="swap_thrashing_risk",
                    title="High Swap Utilization (Disk Thrashing Risk)",
                    severity=FindingSeverity.WARNING,
                    what_detected=f"Swap usage is at {swap_pct}%.",
                    what_it_means="The operating system is heavily offloading inactive memory pages to disk storage, causing latency.",
                    how_serious="Moderate to High responsiveness degradation.",
                    what_could_cause="Continuous physical memory shortfall forcing pages into swap.",
                    what_user_should_do="Free up RAM by quitting background applications.",
                    safe_next_step="Close unused background services.",
                    technical_details={"swap_pct": swap_pct, "swap_used_gb": swap_used_gb},
                    is_hardware_degradation=False,
                    deduction_points=15.0,
                )
            )
            score -= 15.0
            deductions_exp.append("High swap utilization (-15 pts)")

        status = "passed"
        if score < 60:
            status = "critical"
        elif score < 85:
            status = "warning"

        return ModuleResult(
            module_name="memory",
            display_name="Memory (RAM & Swap)",
            status=status,
            score=max(0.0, round(score, 1)),
            confidence=1.0,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
