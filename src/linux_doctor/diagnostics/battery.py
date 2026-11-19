"""Battery & Power Diagnostic Module.

Detects battery state, design capacity, full charge capacity, wear level,
charge cycles, and charging status on laptops.
Carefully handles desktops without failing or penalizing them for missing batteries.
"""

import os
import time
from pathlib import Path
from typing import Any, Dict, List
import psutil
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult


class BatteryDiagnostic:
    """Diagnoses laptop battery health and wear safely."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        score = 100.0
        deductions_exp: List[str] = []

        # Check psutil battery representation first
        sensors_battery = None
        try:
            sensors_battery = psutil.sensors_battery()
        except Exception:
            pass

        # Check Linux sysfs power_supply
        power_supply_path = Path("/sys/class/power_supply")
        bat_dirs = []
        if power_supply_path.exists():
            bat_dirs = [d for d in power_supply_path.iterdir() if d.name.startswith("BAT")]

        # Determine if this is a desktop without a battery
        if sensors_battery is None and not bat_dirs:
            # System has no battery (Desktop PC, Server, or VM)
            metrics["is_desktop_no_battery"] = True
            metrics["battery_present"] = False
            return ModuleResult(
                module_name="battery",
                display_name="Battery & Power",
                status="passed",
                score=100.0,
                confidence=1.0,
                supported=False,  # Mark unsupported so HealthScoringEngine ignores it cleanly
                not_supported_reason="No battery installed (Desktop or VM system)",
                metrics=metrics,
                findings=[],
                deductions_explanation=[],
                execution_time_seconds=round(time.time() - start_time, 3),
            )

        # Battery exists
        metrics["battery_present"] = True
        if sensors_battery:
            metrics["percent"] = sensors_battery.percent
            metrics["power_plugged"] = sensors_battery.power_plugged
            metrics["seconds_left"] = sensors_battery.secsleft if sensors_battery.secsleft != psutil.POWER_TIME_UNLIMITED else None

        # Read Linux detailed sysfs attributes if available
        if bat_dirs:
            bat_dir = bat_dirs[0]
            metrics["battery_node"] = bat_dir.name

            def _read_int(filename: str) -> int:
                p = bat_dir / filename
                if p.exists():
                    try:
                        return int(p.read_text().strip())
                    except Exception:
                        pass
                return 0

            energy_full_design = _read_int("energy_full_design") or _read_int("charge_full_design")
            energy_full = _read_int("energy_full") or _read_int("charge_full")
            cycle_count = _read_int("cycle_count")
            status_p = bat_dir / "status"
            charge_status = status_p.read_text().strip() if status_p.exists() else "Unknown"

            metrics["charging_status"] = charge_status
            if cycle_count > 0:
                metrics["cycle_count"] = cycle_count

            if energy_full_design > 0 and energy_full > 0:
                wear_ratio = energy_full / energy_full_design
                health_pct = round(wear_ratio * 100.0, 1)
                metrics["health_percentage"] = health_pct
                metrics["design_capacity"] = energy_full_design
                metrics["full_charge_capacity"] = energy_full

                # Check for significant battery wear
                if health_pct < 50.0:
                    findings.append(
                        DiagnosticFinding(
                            id="battery_severe_wear",
                            title="Severe Battery Degradation Detected",
                            severity=FindingSeverity.CRITICAL,
                            what_detected=f"Current full-charge capacity is only {health_pct}% of original design capacity.",
                            what_it_means="The chemical battery cells have degraded significantly. Runtime will be much shorter than when the laptop was new.",
                            how_serious="High physical wear. May lead to unexpected shutdowns under load.",
                            what_could_cause="Normal chemical aging across extensive charge/discharge cycles or thermal stress.",
                            what_user_should_do="Plan for battery replacement if portable operation is needed.",
                            safe_next_step="Keep power adapter connected during critical tasks.",
                            technical_details={"health_pct": health_pct, "cycles": cycle_count},
                            is_hardware_degradation=True,
                            deduction_points=30.0,
                        )
                    )
                    score -= 30.0
                    deductions_exp.append(f"Severe battery capacity degradation ({health_pct}%) (-30 pts)")
                elif health_pct < 75.0:
                    findings.append(
                        DiagnosticFinding(
                            id="battery_wear_warning",
                            title="Noticeable Battery Wear Detected",
                            severity=FindingSeverity.WARNING,
                            what_detected=f"Current battery health is at {health_pct}% of original design capacity.",
                            what_it_means="Your laptop will not last as long on battery power as it originally did.",
                            how_serious="Moderate normal wear.",
                            what_could_cause="Natural battery wear over time.",
                            what_user_should_do="Monitor battery capacity and adjust power saver profile.",
                            safe_next_step="Observe remaining runtime under normal usage.",
                            technical_details={"health_pct": health_pct, "cycles": cycle_count},
                            is_hardware_degradation=True,
                            deduction_points=15.0,
                        )
                    )
                    score -= 15.0
                    deductions_exp.append(f"Noticeable battery wear ({health_pct}%) (-15 pts)")

        status = "passed"
        if score < 60:
            status = "critical"
        elif score < 85:
            status = "warning"

        return ModuleResult(
            module_name="battery",
            display_name="Battery & Power Health",
            status=status,
            score=max(0.0, round(score, 1)),
            confidence=0.95,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
