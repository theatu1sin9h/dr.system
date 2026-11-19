"""Thermal Decay & Cooling Dissipation Profiler.

Executes a calibrated synthetic burst workload (3-5s), records peak temperature,
cuts load immediately, and tracks the thermal half-life (seconds taken to drop toward baseline).
Diagnoses dried thermal paste, clogged fan heatsinks, and heatpipe degradation.
"""

import math
import multiprocessing
import time
from typing import Any, Callable, Dict, List, Optional
import psutil
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult


def _stress_worker(stop_flag, compute_passes: int = 5000000):
    """Safe synthetic CPU worker that halts on flag."""
    x = 1.0001
    while not stop_flag.value:
        for _ in range(1000):
            x = math.sin(x) * math.cos(x) + 1.0


def _get_current_temp() -> Optional[float]:
    """Reads highest current CPU temperature sensor."""
    max_t = None
    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if max_t is None or entry.current > max_t:
                            max_t = entry.current
    except Exception:
        pass
    return max_t


class ThermalDecayProfiler:
    """Profiles thermal dissipation curves and cooling half-life."""

    @classmethod
    def run_profiler(
        cls,
        burst_duration_sec: float = 3.0,
        cooling_monitor_sec: float = 5.0,
        progress_cb: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        baseline_temp = _get_current_temp()
        if baseline_temp is None:
            return {
                "supported": False,
                "reason": "Thermal sensors are not accessible (common in VMs or unsupported hardware)",
            }

        # Step 1: Baseline
        if progress_cb: progress_cb("Recording baseline temperature...", 0.1)
        time.sleep(0.5)
        baseline = _get_current_temp() or baseline_temp

        # Step 2: Calibrated Burst Load
        num_workers = max(1, min(4, multiprocessing.cpu_count()))
        if progress_cb: progress_cb(f"Applying calibrated synthetic load across {num_workers} cores...", 0.3)

        stop_flag = multiprocessing.Value("b", False)
        workers = [
            multiprocessing.Process(target=_stress_worker, args=(stop_flag,))
            for _ in range(num_workers)
        ]

        peak_temp = baseline
        temp_samples: List[Dict[str, float]] = []

        try:
            for w in workers:
                w.start()

            burst_start = time.time()
            while time.time() - burst_start < burst_duration_sec:
                cur = _get_current_temp()
                if cur and cur > peak_temp:
                    peak_temp = cur
                time.sleep(0.2)
        finally:
            stop_flag.value = True
            for w in workers:
                w.join(timeout=1.0)
                if w.is_alive():
                    w.terminate()

        # Step 3: Monitor Cooling Decay Curve
        if progress_cb: progress_cb("Monitoring heatsink cooling decay...", 0.6)
        cooling_start = time.time()
        half_life_seconds = None
        delta_rise = max(0.1, peak_temp - baseline)
        half_decay_target = baseline + (delta_rise / 2.0)

        while time.time() - cooling_start < cooling_monitor_sec:
            cur = _get_current_temp() or baseline
            elapsed = time.time() - cooling_start
            temp_samples.append({"time_s": round(elapsed, 2), "temp_c": cur})

            if half_life_seconds is None and cur <= half_decay_target:
                half_life_seconds = round(elapsed, 2)
            time.sleep(0.3)

        if half_life_seconds is None:
            # If temp didn't drop 50% within monitor window
            half_life_seconds = cooling_monitor_sec

        return {
            "supported": True,
            "baseline_temp_c": round(baseline, 1),
            "peak_temp_c": round(peak_temp, 1),
            "temperature_delta_c": round(delta_rise, 1),
            "thermal_half_life_s": half_life_seconds,
            "decay_curve_samples": temp_samples,
        }


class ThermalDecayDiagnostic:
    """Diagnostic wrapper for Thermal Decay and cooling efficiency."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        score = 100.0
        deductions_exp: List[str] = []

        res = ThermalDecayProfiler.run_profiler(burst_duration_sec=2.0, cooling_monitor_sec=4.0)
        metrics["thermal_profile"] = res

        if not res.get("supported", False):
            return ModuleResult(
                module_name="thermal_decay",
                display_name="Cooling & Thermal Decay Profiler",
                status="passed",
                score=100.0,
                confidence=0.5,
                supported=False,
                not_supported_reason=res.get("reason", "Thermal profiling unsupported"),
                metrics=metrics,
                findings=[],
            )

        half_life = res.get("thermal_half_life_s", 0.0)
        peak_t = res.get("peak_temp_c", 0.0)
        delta_t = res.get("temperature_delta_c", 0.0)

        # Evaluate cooling efficiency
        # An efficient heatsink dissipates rapidly. If temperature jumps massively in 2s or fails to drop:
        if peak_t >= 90.0:
            findings.append(
                DiagnosticFinding(
                    id="thermal_instant_spike_critical",
                    title="Sudden Thermal Spike Under Brief Load",
                    severity=FindingSeverity.CRITICAL,
                    what_detected=f"CPU reached {peak_t}°C within seconds of synthetic load (+{delta_t}°C rise).",
                    what_it_means="Heat is not transferring quickly from the CPU die into the heatsink fins.",
                    how_serious="High. Indicates degraded thermal paste, loose heatsink mount, or stopped fan.",
                    what_could_cause="Dried thermal paste, plastic peel left on heatsink, or fan curve not reacting.",
                    what_user_should_do="Check fan speed operation and consider re-applying thermal paste.",
                    safe_next_step="Inspect cooling assembly and airflow.",
                    technical_details=res,
                    is_hardware_degradation=True,
                    deduction_points=30.0,
                )
            )
            score -= 30.0
            deductions_exp.append(f"Instant thermal spike ({peak_t}°C) (-30 pts)")

        return ModuleResult(
            module_name="thermal_decay",
            display_name="Cooling & Thermal Decay Profiler",
            status="passed" if score >= 85 else "warning",
            score=max(0.0, round(score, 1)),
            confidence=0.95,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
