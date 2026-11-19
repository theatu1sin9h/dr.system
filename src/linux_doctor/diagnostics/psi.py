"""Kernel Pressure Stall Information (PSI) Diagnostic Module.

Reads wall-clock thread stall ratios directly from the Linux Kernel (/proc/pressure/*).
Distinguishes real desktop micro-stutters and I/O bus starvation from harmless CPU usage.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult


class PSIReader:
    """Parses /proc/pressure/{cpu,memory,io} statistics."""

    @staticmethod
    def parse_psi_file(path: Path) -> Dict[str, Dict[str, float]]:
        data: Dict[str, Dict[str, float]] = {}
        if not path.exists():
            return data
        try:
            content = path.read_text(encoding="utf-8").strip()
            for line in content.splitlines():
                parts = line.split()
                if not parts:
                    continue
                tier = parts[0]  # 'some' or 'full'
                metrics = {}
                for item in parts[1:]:
                    if "=" in item:
                        k, v = item.split("=", 1)
                        metrics[k] = float(v)
                data[tier] = metrics
        except Exception:
            pass
        return data


class PSIDiagnostic:
    """Diagnoses real-time system pressure stalls across CPU, RAM, and IO."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        score = 100.0
        deductions_exp: List[str] = []

        base = Path("/proc/pressure")
        if not base.exists():
            return ModuleResult(
                module_name="psi",
                display_name="Kernel Pressure Stalls (PSI)",
                status="passed",
                score=100.0,
                confidence=0.5,
                supported=False,
                not_supported_reason="Kernel PSI not compiled into running kernel",
                metrics={"supported": False},
                findings=[],
            )

        cpu_psi = PSIReader.parse_psi_file(base / "cpu")
        mem_psi = PSIReader.parse_psi_file(base / "memory")
        io_psi = PSIReader.parse_psi_file(base / "io")

        metrics["cpu"] = cpu_psi
        metrics["memory"] = mem_psi
        metrics["io"] = io_psi
        metrics["supported"] = True

        # Check I/O stalls (frequent cause of desktop freezes and audio dropouts)
        io_some_avg10 = io_psi.get("some", {}).get("avg10", 0.0)
        io_full_avg10 = io_psi.get("full", {}).get("avg10", 0.0)

        if io_full_avg10 > 10.0:
            findings.append(
                DiagnosticFinding(
                    id="psi_io_critical_stall",
                    title="Severe Storage I/O Bus Starvation (Micro-Freezes)",
                    severity=FindingSeverity.CRITICAL,
                    what_detected=f"10-second I/O full stall ratio is at {io_full_avg10:.1f}%. ALL runnable threads were stalled waiting on disk I/O.",
                    what_it_means="Your system is suffering micro-freezes because CPU threads are blocked waiting for disk read/write requests to complete.",
                    how_serious="High. Noticeable UI lag, mouse stutter, or application unresponsive popups.",
                    what_could_cause="Saturated slow disk, heavy background sync, swap thrashing, or failing SSD controller.",
                    what_user_should_do="Check active disk I/O tasks using 'iotop' or reduce background disk-heavy tasks.",
                    safe_next_step="Inspect processes performing heavy disk writes.",
                    technical_details={"io_full_avg10": io_full_avg10, "io_some_avg10": io_some_avg10},
                    is_hardware_degradation=False,
                    deduction_points=30.0,
                )
            )
            score -= 30.0
            deductions_exp.append(f"Severe I/O stall ({io_full_avg10:.1f}%) (-30 pts)")
        elif io_some_avg10 > 15.0:
            findings.append(
                DiagnosticFinding(
                    id="psi_io_elevated_stall",
                    title="Elevated Storage I/O Pressure",
                    severity=FindingSeverity.WARNING,
                    what_detected=f"10-second I/O pressure stall is at {io_some_avg10:.1f}%.",
                    what_it_means="Some CPU tasks were delayed waiting for storage operations to finish.",
                    how_serious="Moderate.",
                    what_could_cause="Large file copy, backup process, or package installation.",
                    what_user_should_do="Wait for heavy disk tasks to finish or check disk throughput.",
                    safe_next_step="Monitor storage write queue.",
                    technical_details={"io_some_avg10": io_some_avg10},
                    is_hardware_degradation=False,
                    deduction_points=10.0,
                )
            )
            score -= 10.0
            deductions_exp.append(f"Elevated I/O pressure ({io_some_avg10:.1f}%) (-10 pts)")

        # Check Memory stalls
        mem_full_avg10 = mem_psi.get("full", {}).get("avg10", 0.0)
        if mem_full_avg10 > 5.0:
            findings.append(
                DiagnosticFinding(
                    id="psi_memory_thrashing_stall",
                    title="Active Memory Thrashing Stall Detected",
                    severity=FindingSeverity.CRITICAL,
                    what_detected=f"Memory full stall is at {mem_full_avg10:.1f}%. Threads are actively blocked waiting for memory page reclamation.",
                    what_it_means="The kernel cannot allocate memory without blocking execution to reclaim pages, causing severe performance drops.",
                    how_serious="High. Risk of immediate OOM crash.",
                    what_could_cause="Physical RAM exhaustion or intense swap swapping.",
                    what_user_should_do="Close unused heavy memory processes immediately.",
                    safe_next_step="Free physical RAM.",
                    technical_details={"mem_full_avg10": mem_full_avg10},
                    is_hardware_degradation=False,
                    deduction_points=25.0,
                )
            )
            score -= 25.0
            deductions_exp.append(f"Memory thrashing stall ({mem_full_avg10:.1f}%) (-25 pts)")

        status = "passed"
        if score < 60:
            status = "critical"
        elif score < 85:
            status = "warning"

        return ModuleResult(
            module_name="psi",
            display_name="Kernel Pressure Stalls (PSI)",
            status=status,
            score=max(0.0, round(score, 1)),
            confidence=1.0,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
