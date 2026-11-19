"""Security & Updates Diagnostic Module.

Performs basic non-invasive checks: firewall status, Secure Boot,
pending updates. Never attempts invasive exploits or antivirus bypasses.
Clearly indicates when checks require elevated administrator privileges.
"""

import time
from typing import Any, Dict, List
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult
from linux_doctor.platforms import get_platform_adapter


class SecurityDiagnostic:
    """Diagnoses firewall protection, boot security, and pending security updates."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        score = 100.0
        deductions_exp: List[str] = []

        adapter = get_platform_adapter()

        # Check firewall
        fw = adapter.get_firewall_status()
        metrics["firewall"] = fw

        # Check Secure Boot
        sb = adapter.get_secure_boot_status()
        metrics["secure_boot"] = sb

        # Check pending updates
        updates = adapter.get_package_updates_status()
        metrics["package_updates"] = updates

        # Analyze firewall findings
        if not fw.get("active", False):
            # If requires elevation, report info
            if "elevated" in fw.get("details", "").lower():
                findings.append(
                    DiagnosticFinding(
                        id="sec_firewall_elevated_needed",
                        title="Firewall Status Check Requires Elevation",
                        severity=FindingSeverity.INFO,
                        what_detected="Checking detailed firewall rules requires administrator / root privileges.",
                        what_it_means="Linux Doctor ran non-invasively as standard user and did not force sudo escalation.",
                        how_serious="Informational.",
                        what_could_cause="Default restrictive permission policies on security subsystem.",
                        what_user_should_do="Run Linux Doctor with elevated privileges if you wish to verify deep firewall rules.",
                        safe_next_step="Check firewall status manually or run scan with permissions.",
                        technical_details=fw,
                        is_hardware_degradation=False,
                        deduction_points=0.0,
                    )
                )
            else:
                findings.append(
                    DiagnosticFinding(
                        id="sec_firewall_inactive",
                        title="System Firewall Inactive",
                        severity=FindingSeverity.WARNING,
                        what_detected="The standard system firewall (UFW, Firewalld, or Windows Firewall) is not currently active.",
                        what_it_means="Incoming unsolicited network connections are not being actively filtered by a local firewall daemon.",
                        how_serious="Moderate on public/untrusted Wi-Fi networks.",
                        what_could_cause="Firewall service was disabled or not enabled post-installation.",
                        what_user_should_do="Enable the system firewall before connecting to public networks.",
                        safe_next_step="Enable firewall service (e.g. 'sudo ufw enable').",
                        technical_details=fw,
                        is_hardware_degradation=False,
                        deduction_points=15.0,
                    )
                )
                score -= 15.0
                deductions_exp.append("Firewall inactive (-15 pts)")

        # Analyze pending updates
        pending_count = updates.get("pending_updates_count", 0)
        if pending_count > 50:
            findings.append(
                DiagnosticFinding(
                    id="sec_many_pending_updates",
                    title="Significant Number of Pending Updates",
                    severity=FindingSeverity.WARNING,
                    what_detected=f"{pending_count} software packages have pending updates available.",
                    what_it_means="Your system is running software that has newer patches, which often include security fixes.",
                    how_serious="Moderate.",
                    what_could_cause="System has not been updated recently.",
                    what_user_should_do="Review and install pending updates through your distribution's update manager.",
                    safe_next_step="Perform standard system update through package manager.",
                    technical_details={"pending_count": pending_count},
                    is_hardware_degradation=False,
                    deduction_points=10.0,
                )
            )
            score -= 10.0
            deductions_exp.append(f"{pending_count} pending updates (-10 pts)")

        status = "passed"
        if score < 60:
            status = "critical"
        elif score < 85:
            status = "warning"

        return ModuleResult(
            module_name="security",
            display_name="Security & Updates",
            status=status,
            score=max(0.0, round(score, 1)),
            confidence=0.85,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
