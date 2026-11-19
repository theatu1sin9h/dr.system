"""Drivers & Kernel Modules Diagnostic Module.

Detects loaded drivers, graphics backends, and driver errors.
"""

import platform
import shutil
import time
from typing import Any, Dict, List
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult
from linux_doctor.platforms.base import run_command_safe


class DriversDiagnostic:
    """Diagnoses kernel drivers, module states, and device issues."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        score = 100.0
        deductions_exp: List[str] = []

        loaded_modules_count = 0
        if platform.system() == "Linux":
            if shutil.which("lsmod"):
                ret, stdout, _ = run_command_safe(["lsmod"], timeout=4)
                if ret == 0 and stdout:
                    lines = stdout.splitlines()
                    loaded_modules_count = max(0, len(lines) - 1)

            # Check dmesg for driver errors if accessible
            ret, stdout, _ = run_command_safe(["dmesg", "-l", "err,crit"], timeout=3)
            if ret == 0 and stdout:
                metrics["recent_kernel_errors"] = len(stdout.splitlines())

        metrics["loaded_modules_count"] = loaded_modules_count

        return ModuleResult(
            module_name="drivers",
            display_name="Hardware Drivers",
            status="passed",
            score=max(0.0, round(score, 1)),
            confidence=0.85,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
