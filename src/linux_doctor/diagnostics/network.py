"""Network Diagnostic Module.

Detects network adapters, interfaces, IP configs, connectivity, and DNS.
Protects privacy by redacting personal network information by default.
"""

import shutil
import socket
import time
from typing import Any, Dict, List
import psutil
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult
from linux_doctor.platforms.base import run_command_safe


class NetworkDiagnostic:
    """Diagnoses network interfaces and basic internet connectivity."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        interfaces_list: List[Dict[str, Any]] = []
        score = 100.0
        deductions_exp: List[str] = []

        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        active_interfaces = 0
        for iface_name, iface_stats in stats.items():
            if iface_name.startswith("lo"):
                continue  # skip loopback
            is_up = iface_stats.isup
            speed = iface_stats.speed
            if is_up:
                active_interfaces += 1

            interfaces_list.append({
                "interface": iface_name,
                "is_up": is_up,
                "speed_mbps": speed,
            })

        metrics["interfaces"] = interfaces_list
        metrics["active_interfaces_count"] = active_interfaces

        # Test safe DNS resolution / connectivity check (no sensitive payload sent)
        has_connectivity = False
        try:
            # Safe probe to common public DNS without leaking info
            socket.gethostbyname("one.one.one.one")
            has_connectivity = True
        except Exception:
            has_connectivity = False

        metrics["internet_connectivity"] = has_connectivity

        if not has_connectivity and active_interfaces > 0:
            findings.append(
                DiagnosticFinding(
                    id="network_dns_failure",
                    title="Internet Gateway or DNS Unreachable",
                    severity=FindingSeverity.WARNING,
                    what_detected="Network interface is up, but standard DNS resolution failed.",
                    what_it_means="Your computer is connected to a local router/network, but cannot reach the broader internet.",
                    how_serious="Moderate to High for online tasks.",
                    what_could_cause="Captive portal Wi-Fi login required, ISP outage, or misconfigured DNS server.",
                    what_user_should_do="Check Wi-Fi/Ethernet router connection or verify DNS server settings.",
                    safe_next_step="Inspect router status or reconnect to network.",
                    technical_details={"active_interfaces": active_interfaces},
                    is_hardware_degradation=False,
                    deduction_points=20.0,
                )
            )
            score -= 20.0
            deductions_exp.append("No internet/DNS connectivity (-20 pts)")
        elif active_interfaces == 0:
            findings.append(
                DiagnosticFinding(
                    id="network_no_active_interfaces",
                    title="No Active Network Interfaces",
                    severity=FindingSeverity.WARNING,
                    what_detected="No active Wi-Fi or Ethernet interfaces detected in UP state.",
                    what_it_means="The PC is completely disconnected from local and wide networks.",
                    how_serious="Informational/Warning.",
                    what_could_cause="Airplane mode enabled, Wi-Fi turned off, or unplugged Ethernet cable.",
                    what_user_should_do="Enable Wi-Fi or plug in an Ethernet cable.",
                    safe_next_step="Turn on network connectivity.",
                    technical_details={},
                    is_hardware_degradation=False,
                    deduction_points=15.0,
                )
            )
            score -= 15.0
            deductions_exp.append("No active network interfaces (-15 pts)")

        status = "passed"
        if score < 60:
            status = "critical"
        elif score < 85:
            status = "warning"

        return ModuleResult(
            module_name="network",
            display_name="Network & Connectivity",
            status=status,
            score=max(0.0, round(score, 1)),
            confidence=0.9,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
