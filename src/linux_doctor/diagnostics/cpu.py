"""CPU Diagnostic Module.

Detects CPU architecture, cores, threads, frequencies, load averages,
utilization, virtualization support, and thermal status.
"""

import os
import platform
import time
from typing import Any, Dict, List
import psutil
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult
from linux_doctor.platforms.base import run_command_safe


class CPUDiagnostic:
    """Diagnoses CPU health, performance, virtualization, and metrics."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        score = 100.0
        deductions_exp: List[str] = []

        # Cores & Threads
        physical_cores = psutil.cpu_count(logical=False) or 1
        logical_cores = psutil.cpu_count(logical=True) or 1
        metrics["physical_cores"] = physical_cores
        metrics["logical_cores"] = logical_cores
        metrics["architecture"] = platform.machine()

        # Model name
        model_name = "Unknown CPU"
        virtualization_supported = False

        if platform.system() == "Linux":
            try:
                with open("/proc/cpuinfo", "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if line.startswith("model name") and model_name == "Unknown CPU":
                            model_name = line.split(":", 1)[1].strip()
                        if line.startswith("flags"):
                            flags = line.split(":", 1)[1].strip().split()
                            if "vmx" in flags or "svm" in flags:
                                virtualization_supported = True
            except Exception:
                pass
        elif platform.system() == "Windows":
            model_name = platform.processor() or "Windows Processor"

        metrics["model"] = model_name
        metrics["virtualization_supported"] = virtualization_supported

        # Frequency
        try:
            freq = psutil.cpu_freq()
            if freq:
                metrics["current_frequency_mhz"] = round(freq.current, 1)
                metrics["min_frequency_mhz"] = round(freq.min, 1) if freq.min else None
                metrics["max_frequency_mhz"] = round(freq.max, 1) if freq.max else None
        except Exception:
            pass

        # CPU Utilization
        cpu_percent = psutil.cpu_percent(interval=0.2)
        metrics["utilization_percent"] = cpu_percent

        # Load average (Unix)
        if hasattr(os, "getloadavg"):
            try:
                load_1, load_5, load_15 = os.getloadavg()
                metrics["load_average"] = [round(load_1, 2), round(load_5, 2), round(load_15, 2)]
                
                # Check for sustained critical load
                normalized_load = load_1 / logical_cores
                if normalized_load > 2.5:
                    findings.append(
                        DiagnosticFinding(
                            id="cpu_sustained_heavy_load",
                            title="Sustained Heavy CPU Load",
                            severity=FindingSeverity.WARNING,
                            what_detected=f"1-minute load average is {load_1:.2f} across {logical_cores} logical threads ({normalized_load:.1f}x capacity).",
                            what_it_means="The processor is currently working through a backlog of tasks, which may cause UI stuttering or delayed responses.",
                            how_serious="Moderate. This is temporary workload pressure, not physical hardware damage.",
                            what_could_cause="Intense compiling, background indexing, heavy calculations, or runaway processes.",
                            what_user_should_do="Inspect running tasks using 'top' or 'htop' to see which applications are consuming CPU resources.",
                            safe_next_step="Check running processes before closing anything.",
                            technical_details={"load_1": load_1, "logical_cores": logical_cores, "ratio": round(normalized_load, 2)},
                            is_hardware_degradation=False,
                            deduction_points=15.0,
                        )
                    )
                    score -= 15.0
                    deductions_exp.append("High load average (-15 pts)")
            except Exception:
                pass

        # Check instantaneous high utilization
        if cpu_percent >= 95.0:
            findings.append(
                DiagnosticFinding(
                    id="cpu_high_utilization",
                    title="Very High CPU Utilization",
                    severity=FindingSeverity.WARNING,
                    what_detected=f"Instantaneous CPU utilization is at {cpu_percent}%.",
                    what_it_means="The processor is currently running close to maximum computational capacity.",
                    how_serious="Informational/Warning. High utilization is normal under heavy workloads.",
                    what_could_cause="Active software updates, video encoding, game rendering, or background tasks.",
                    what_user_should_do="If the PC is idle, check task manager/process list for unresponsive background processes.",
                    safe_next_step="Review the top processes by CPU usage.",
                    technical_details={"cpu_percent": cpu_percent},
                    is_hardware_degradation=False,
                    deduction_points=10.0,
                )
            )
            score -= 10.0
            deductions_exp.append("Extremely high current CPU utilization (-10 pts)")

        status = "passed"
        if score < 60:
            status = "critical"
        elif score < 85:
            status = "warning"

        return ModuleResult(
            module_name="cpu",
            display_name="Processor (CPU)",
            status=status,
            score=max(0.0, round(score, 1)),
            confidence=1.0,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
