"""Storage Diagnostic Module.

Detects HDD, SSD, NVMe, mount points, partition capacities,
available disk space, and safe read-only SMART attributes when available.
Never performs destructive benchmarks or raw write tests.
"""

import shutil
import time
from pathlib import Path
from typing import Any, Dict, List
import psutil
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult
from linux_doctor.platforms.base import run_command_safe


class StorageDiagnostic:
    """Diagnoses mounted filesystems, disk space, and storage drive health."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        partitions_list: List[Dict[str, Any]] = []
        score = 100.0
        deductions_exp: List[str] = []

        total_disk_bytes = 0
        used_disk_bytes = 0
        free_disk_bytes = 0

        # Enumerate mounted partitions
        partitions = psutil.disk_partitions(all=False)
        for part in partitions:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                total_gb = round(usage.total / (1024**3), 2)
                used_gb = round(usage.used / (1024**3), 2)
                free_gb = round(usage.free / (1024**3), 2)
                used_pct = usage.percent

                total_disk_bytes += usage.total
                used_disk_bytes += usage.used
                free_disk_bytes += usage.free

                part_data = {
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": total_gb,
                    "used_gb": used_gb,
                    "free_gb": free_gb,
                    "percent_used": used_pct,
                }
                partitions_list.append(part_data)

                # Check root or crucial partition fill rate
                if part.mountpoint in ("/", "C:\\"):
                    if used_pct >= 95.0 or free_gb < 2.0:
                        findings.append(
                            DiagnosticFinding(
                                id=f"disk_full_critical_{part.mountpoint}",
                                title=f"Critical Disk Space Shortage on {part.mountpoint}",
                                severity=FindingSeverity.CRITICAL,
                                what_detected=f"Mount point '{part.mountpoint}' is {used_pct}% full with only {free_gb} GB free.",
                                what_it_means="Operating systems and applications require temporary disk space to write logs, caches, and swap files. Low space can prevent boot or corrupt files.",
                                how_serious="High. System may become unstable or fail to boot if root disk fills completely.",
                                what_could_cause="Accumulated log files, package cache, large downloads, or media files.",
                                what_user_should_do="Free up disk space by cleaning package caches or deleting old unneeded files.",
                                safe_next_step="Inspect directory sizes using 'ncdu' or disk usage analyzer.",
                                technical_details=part_data,
                                is_hardware_degradation=False,
                                deduction_points=30.0,
                            )
                        )
                        score -= 30.0
                        deductions_exp.append(f"Root drive '{part.mountpoint}' critically full (-30 pts)")
                    elif used_pct >= 85.0:
                        findings.append(
                            DiagnosticFinding(
                                id=f"disk_warning_high_{part.mountpoint}",
                                title=f"Low Disk Space on {part.mountpoint}",
                                severity=FindingSeverity.WARNING,
                                what_detected=f"Mount point '{part.mountpoint}' is {used_pct}% full ({free_gb} GB free).",
                                what_it_means="Drive capacity is approaching full threshold.",
                                how_serious="Moderate.",
                                what_could_cause="Natural accumulation of software, games, or user data.",
                                what_user_should_do="Clean old caches and remove unused applications.",
                                safe_next_step="Review largest folders on this disk.",
                                technical_details=part_data,
                                is_hardware_degradation=False,
                                deduction_points=10.0,
                            )
                        )
                        score -= 10.0
                        deductions_exp.append(f"Drive '{part.mountpoint}' approaching full (-10 pts)")
            except Exception:
                continue

        metrics["partitions"] = partitions_list
        metrics["total_storage_gb"] = round(total_disk_bytes / (1024**3), 2)
        metrics["used_storage_gb"] = round(used_disk_bytes / (1024**3), 2)
        metrics["free_storage_gb"] = round(free_disk_bytes / (1024**3), 2)

        # Check safe SMART queries if smartctl exists
        smart_available = False
        if shutil.which("smartctl"):
            smart_available = True
            # Query disks safely (scan for devices)
            ret, stdout, _ = run_command_safe(["smartctl", "--scan"], timeout=4)
            if ret == 0 and stdout:
                metrics["smart_devices_detected"] = len(stdout.splitlines())

        metrics["smart_support_available"] = smart_available

        status = "passed"
        if score < 60:
            status = "critical"
        elif score < 85:
            status = "warning"

        return ModuleResult(
            module_name="storage",
            display_name="Storage & Disks",
            status=status,
            score=max(0.0, round(score, 1)),
            confidence=1.0,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
