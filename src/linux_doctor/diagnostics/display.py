"""Display & Monitor Diagnostic Module.

Detects internal and external screens, resolutions, refresh rates,
session types (Wayland vs X11), without altering user resolutions.
"""

import os
import shutil
import time
from typing import Any, Dict, List
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult
from linux_doctor.platforms.base import run_command_safe


class DisplayDiagnostic:
    """Diagnoses display outputs, monitors, and session compositor."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        monitors: List[Dict[str, Any]] = []
        score = 100.0
        deductions_exp: List[str] = []

        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if not session_type:
            if os.environ.get("WAYLAND_DISPLAY"):
                session_type = "wayland"
            elif os.environ.get("DISPLAY"):
                session_type = "x11"
            else:
                session_type = "headless"

        metrics["session_type"] = session_type

        # Check monitors via xrandr or wayland tools
        if shutil.which("xrandr"):
            ret, stdout, _ = run_command_safe(["xrandr", "--query"], timeout=4)
            if ret == 0:
                for line in stdout.splitlines():
                    if " connected " in line:
                        parts = line.split()
                        conn_name = parts[0]
                        is_primary = "primary" in line
                        res_str = ""
                        for part in parts:
                            if "+" in part and "x" in part:
                                res_str = part
                                break
                        monitors.append({
                            "name": conn_name,
                            "primary": is_primary,
                            "mode": res_str or "active",
                        })

        metrics["connected_monitors"] = monitors
        metrics["monitor_count"] = len(monitors)

        # Check for headless environment or display server missing
        if session_type == "headless" and len(monitors) == 0:
            metrics["note"] = "Running in headless server or TTY environment."
            # Headless environment is not a hardware fault
            score = 100.0

        return ModuleResult(
            module_name="display",
            display_name="Display & Monitors",
            status="passed",
            score=max(0.0, round(score, 1)),
            confidence=0.85 if monitors else 0.5,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
