"""Cross-Subsystem Causality and Correlation Engine.

Examines findings across multiple independent subsystems (Thermals, PSI, I/O latency,
GPU, Audio, and CPU) to determine if an anomaly in one component is directly causing
symptoms in another.
"""

from typing import Dict, List
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult


class CausalityInsight:
    """A cross-subsystem causality conclusion."""

    def __init__(self, title: str, cause_component: str, affected_component: str, explanation: str, recommendation: str):
        self.title = title
        self.cause_component = cause_component
        self.affected_component = affected_component
        self.explanation = explanation
        self.recommendation = recommendation


class CausalityEngine:
    """Discovers root-cause links between separate hardware/OS metrics."""

    @classmethod
    def analyze(cls, results: Dict[str, ModuleResult]) -> List[CausalityInsight]:
        insights: List[CausalityInsight] = []

        # Rule 1: High Thermals causing CPU Frequency Drop / Throttling
        temp_res = results.get("temperature")
        cpu_res = results.get("cpu")
        if temp_res and cpu_res:
            max_temp = temp_res.metrics.get("max_temperature_celsius") or 0.0
            cpu_freq = cpu_res.metrics.get("current_frequency_mhz")
            max_freq = cpu_res.metrics.get("max_frequency_mhz")
            if max_temp >= 85.0 and cpu_freq and max_freq and (cpu_freq < max_freq * 0.6):
                insights.append(
                    CausalityInsight(
                        title="Thermal Throttling Depressing CPU Clock Speed",
                        cause_component="Thermals & Cooling",
                        affected_component="Processor (CPU)",
                        explanation=(
                            f"Peak temperatures reached {max_temp}°C while CPU clock is constrained to "
                            f"{cpu_freq:.0f} MHz (Max rated: {max_freq:.0f} MHz). The CPU processor is actively "
                            f"downclocking itself to protect the silicon from permanent thermal breakdown."
                        ),
                        recommendation="Improve chassis ventilation and verify cooling fan speeds.",
                    )
                )

        # Rule 2: Storage I/O Stalls (PSI) Causing UI/Audio Stutters
        psi_res = results.get("psi")
        audio_res = results.get("audio")
        latency_res = results.get("storage_latency")
        if psi_res:
            io_full = psi_res.metrics.get("io", {}).get("full", {}).get("avg10", 0.0)
            p99_lat = latency_res.metrics.get("latency_test", {}).get("p99_latency_ms", 0.0) if latency_res else 0.0
            if io_full > 5.0 or p99_lat > 50.0:
                insights.append(
                    CausalityInsight(
                        title="Storage I/O Bottleneck Inducing Real-Time Latency Stutters",
                        cause_component="Storage & Disks",
                        affected_component="Audio / Interactive Desktop UI",
                        explanation=(
                            f"Storage subsystem is suffering severe latency spikes (I/O stall ratio: {io_full:.1f}%, "
                            f"P99 latency: {p99_lat:.1f}ms). High-priority desktop worker threads and audio buffers "
                            f"are being blocked waiting for disk request returns."
                        ),
                        recommendation="Identify high disk-write background processes or perform SSD TRIM maintenance.",
                    )
                )

        # Rule 3: Software Rasterizer Fallback Overloading CPU
        gpu_res = results.get("gpu")
        if gpu_res and cpu_res:
            renderer = gpu_res.metrics.get("opengl_renderer", "").lower()
            cpu_load = cpu_res.metrics.get("utilization_percent", 0.0)
            if ("llvmpipe" in renderer or "software" in renderer) and cpu_load > 40.0:
                insights.append(
                    CausalityInsight(
                        title="Software 3D Rendering Straining CPU",
                        cause_component="Graphics (GPU Drivers)",
                        affected_component="Processor (CPU)",
                        explanation=(
                            f"Graphics acceleration is currently utilizing CPU software emulation ('{renderer}'). "
                            f"Window composition and video decoding are consuming substantial CPU cycles."
                        ),
                        recommendation="Install dedicated hardware graphics drivers for your GPU.",
                    )
                )

        return insights
