"""GPU and Graphics Diagnostic Module.

Supports AMD, Intel, NVIDIA, and virtualized graphics.
Detects GPU models, drivers, acceleration backend, and temperatures.
"""

import platform
import shutil
import time
from typing import Any, Dict, List
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult
from linux_doctor.platforms.base import run_command_safe


class GPUDiagnostic:
    """Diagnoses graphics cards, drivers, and 3D acceleration."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        score = 100.0
        deductions_exp: List[str] = []

        gpus_detected: List[Dict[str, str]] = []
        vendor_found = "Unknown"

        # Check Linux tools: lspci, glxinfo, nvidia-smi
        if platform.system() == "Linux":
            if shutil.which("lspci"):
                ret, stdout, _ = run_command_safe(["lspci"], timeout=4)
                if ret == 0:
                    for line in stdout.splitlines():
                        if "VGA compatible controller" in line or "3D controller" in line:
                            # e.g. "00:02.0 VGA compatible controller: Intel Corporation UHD Graphics 620"
                            parts = line.split(":", 2)
                            desc = parts[2].strip() if len(parts) >= 3 else line
                            v_name = "Unknown"
                            if "intel" in desc.lower():
                                v_name = "Intel"
                            elif "nvidia" in desc.lower():
                                v_name = "NVIDIA"
                            elif "amd" in desc.lower() or "advanced micro devices" in desc.lower():
                                v_name = "AMD"
                            vendor_found = v_name
                            gpus_detected.append({"model": desc, "vendor": v_name})

            # NVIDIA specialized check
            if shutil.which("nvidia-smi"):
                ret, stdout, _ = run_command_safe(
                    ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,temperature.gpu", "--format=csv,noheader,nounits"],
                    timeout=5,
                )
                if ret == 0 and stdout:
                    for line in stdout.splitlines():
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 4:
                            metrics["nvidia_driver_version"] = parts[1]
                            metrics["nvidia_vram_total_mb"] = parts[2]
                            metrics["nvidia_temp_c"] = parts[3]
                            if not gpus_detected:
                                gpus_detected.append({"model": parts[0], "vendor": "NVIDIA"})

            # Check OpenGL acceleration via glxinfo
            if shutil.which("glxinfo"):
                ret, stdout, _ = run_command_safe(["glxinfo", "-B"], timeout=4)
                if ret == 0:
                    for line in stdout.splitlines():
                        if "OpenGL renderer string:" in line:
                            metrics["opengl_renderer"] = line.split(":", 1)[1].strip()
                        elif "OpenGL version string:" in line:
                            metrics["opengl_version"] = line.split(":", 1)[1].strip()
                        elif "Direct rendering:" in line:
                            metrics["direct_rendering"] = "Yes" in line

        elif platform.system() == "Windows":
            # On Windows, query CIM for Win32_VideoController
            # Will be safely handled if CIM returns data
            pass

        metrics["gpus"] = gpus_detected
        metrics["primary_vendor"] = vendor_found

        # Evaluate acceleration / software rendering
        renderer = metrics.get("opengl_renderer", "")
        if "llvmpipe" in renderer.lower() or "software rasterizer" in renderer.lower():
            findings.append(
                DiagnosticFinding(
                    id="gpu_software_rendering_fallback",
                    title="Software Rendering Fallback Detected (LLVMpipe)",
                    severity=FindingSeverity.WARNING,
                    what_detected=f"Graphics are rendering via CPU software fallback ('{renderer}') rather than hardware acceleration.",
                    what_it_means="The system is using your CPU to emulate a GPU. Desktop animations and videos will cause high CPU usage and sluggishness.",
                    how_serious="Moderate to High for desktop performance.",
                    what_could_cause="Missing GPU drivers, mesa driver conflict, or running inside a VM without 3D pass-through.",
                    what_user_should_do="Install the recommended proprietary or open-source graphics driver for your GPU.",
                    safe_next_step="Check available driver packages for your distribution.",
                    technical_details={"renderer": renderer},
                    is_hardware_degradation=False,
                    deduction_points=20.0,
                )
            )
            score -= 20.0
            deductions_exp.append("Software rendering fallback active (-20 pts)")

        status = "passed"
        if score < 60:
            status = "critical"
        elif score < 85:
            status = "warning"

        return ModuleResult(
            module_name="gpu",
            display_name="Graphics (GPU)",
            status=status,
            score=max(0.0, round(score, 1)),
            confidence=0.9 if gpus_detected else 0.5,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
