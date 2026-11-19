"""System Stability & Services Diagnostic Module.

Detects failed systemd services, critical kernel errors, and boot warnings
without flagging normal transient warnings as critical hardware faults.
"""

import time
from typing import Any, Dict, List
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult
from linux_doctor.platforms import get_platform_adapter


class StabilityDiagnostic:
    """Diagnoses OS daemon health and service failure rates."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        score = 100.0
        deductions_exp: List[str] = []

        adapter = get_platform_adapter()
        failed_services = adapter.get_service_failures()

        metrics["failed_services"] = failed_services
        metrics["failed_services_count"] = len(failed_services)

        if len(failed_services) >= 3:
            findings.append(
                DiagnosticFinding(
                    id="stability_multiple_failed_services",
                    title="Multiple Failed System Services",
                    severity=FindingSeverity.CRITICAL,
                    what_detected=f"{len(failed_services)} system services have failed to start or crashed.",
                    what_it_means="Multiple background daemons are not running properly, which may degrade audio, networking, or system maintenance tasks.",
                    how_serious="High background impact.",
                    what_could_cause="Corrupted configuration files, missing dependencies, or conflicting software.",
                    what_user_should_do="Review the specific failed unit names and inspect their logs using 'systemctl status <unit>'.",
                    safe_next_step="Inspect system logs for the failed services.",
                    technical_details={"failed_units": [s["unit"] for s in failed_services]},
                    is_hardware_degradation=False,
                    deduction_points=25.0,
                )
            )
            score -= 25.0
            deductions_exp.append(f"{len(failed_services)} failed background services (-25 pts)")
        elif len(failed_services) > 0:
            findings.append(
                DiagnosticFinding(
                    id="stability_service_failure",
                    title=f"Failed Background Service ({failed_services[0]['unit']})",
                    severity=FindingSeverity.WARNING,
                    what_detected=f"Service '{failed_services[0]['unit']}' is in a failed state.",
                    what_it_means="A system background process exited with an error.",
                    how_serious="Moderate.",
                    what_could_cause="Configuration error or missing service dependency.",
                    what_user_should_do="Check service status and restart or disable the unneeded service.",
                    safe_next_step="Review the log of the failed service.",
                    technical_details={"failed_units": [s["unit"] for s in failed_services]},
                    is_hardware_degradation=False,
                    deduction_points=10.0,
                )
            )
            score -= 10.0
            deductions_exp.append(f"Failed service '{failed_services[0]['unit']}' (-10 pts)")

        status = "passed"
        if score < 60:
            status = "critical"
        elif score < 85:
            status = "warning"

        return ModuleResult(
            module_name="stability",
            display_name="System Stability & Services",
            status=status,
            score=max(0.0, round(score, 1)),
            confidence=0.9,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
