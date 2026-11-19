"""Temperature & Thermal Sensors Diagnostic Module.

Detects CPU, GPU, and disk temperatures, fan speeds, and thermal throttling.
Distinguishes unavailable sensors from hardware faults.
"""

import time
from typing import Any, Dict, List
import psutil
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult


class TemperatureDiagnostic:
    """Diagnoses thermal sensors, fan status, and overheating risks."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        sensor_readings: Dict[str, float] = {}
        score = 100.0
        deductions_exp: List[str] = []

        max_temp_c = 0.0
        has_sensors = False

        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    has_sensors = True
                    for name, entries in temps.items():
                        for entry in entries:
                            label = entry.label or name
                            sensor_readings[label] = entry.current
                            if entry.current > max_temp_c:
                                max_temp_c = entry.current
        except Exception:
            pass

        metrics["sensors_available"] = has_sensors
        metrics["readings_celsius"] = sensor_readings
        metrics["max_temperature_celsius"] = max_temp_c if has_sensors else None

        # Fan speeds if available
        fans_available = False
        try:
            if hasattr(psutil, "sensors_fans"):
                fans = psutil.sensors_fans()
                if fans:
                    fans_available = True
                    metrics["fans"] = {k: [f.current for f in v] for k, v in fans.items()}
        except Exception:
            pass

        metrics["fans_available"] = fans_available

        if not has_sensors:
            metrics["note"] = "Thermal sensors not exposed (typical in VMs or unsupported hardware chips)."
            # Missing sensors are handled as N/A, NOT hardware failure
            return ModuleResult(
                module_name="temperature",
                display_name="Thermals & Temperatures",
                status="passed",
                score=100.0,
                confidence=0.5,
                supported=True,
                metrics=metrics,
                findings=[],
                deductions_explanation=[],
                execution_time_seconds=round(time.time() - start_time, 3),
            )

        # Check temperatures
        if max_temp_c >= 95.0:
            findings.append(
                DiagnosticFinding(
                    id="thermal_critical_throttling",
                    title="Critical Thermal Overheating Detected",
                    severity=FindingSeverity.CRITICAL,
                    what_detected=f"Sensor registered peak temperature of {max_temp_c:.1f}°C (Threshold >= 95°C).",
                    what_it_means="The processor is running near thermal maximum and will throttle clock speed to prevent permanent hardware damage.",
                    how_serious="High. Risk of thermal shutdown or component stress.",
                    what_could_cause="Clogged heatsink dust, failing fan, dried thermal paste, or blocked airflow.",
                    what_user_should_do="Ensure air vents are clear and fans are spinning. Avoid running intensive stress loads.",
                    safe_next_step="Inspect cooling vents and clean accumulated dust.",
                    technical_details={"max_temp_c": max_temp_c},
                    is_hardware_degradation=True,
                    deduction_points=30.0,
                )
            )
            score -= 30.0
            deductions_exp.append(f"Critical overheating ({max_temp_c:.1f}°C) (-30 pts)")
        elif max_temp_c >= 85.0:
            findings.append(
                DiagnosticFinding(
                    id="thermal_elevated",
                    title="Elevated Temperatures Detected",
                    severity=FindingSeverity.WARNING,
                    what_detected=f"Peak temperature reached {max_temp_c:.1f}°C.",
                    what_it_means="The PC is running warmer than usual under current conditions.",
                    how_serious="Moderate.",
                    what_could_cause="High ambient room temperature or sustained heavy load.",
                    what_user_should_do="Ensure proper ventilation around device.",
                    safe_next_step="Check system fan operation.",
                    technical_details={"max_temp_c": max_temp_c},
                    is_hardware_degradation=False,
                    deduction_points=10.0,
                )
            )
            score -= 10.0
            deductions_exp.append(f"Elevated temperatures ({max_temp_c:.1f}°C) (-10 pts)")

        status = "passed"
        if score < 60:
            status = "critical"
        elif score < 85:
            status = "warning"

        return ModuleResult(
            module_name="temperature",
            display_name="Thermals & Temperatures",
            status=status,
            score=max(0.0, round(score, 1)),
            confidence=1.0,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
