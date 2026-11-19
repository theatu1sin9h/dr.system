"""Generic Linux platform adapter using standard sysfs, procfs, and system tools."""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List
from linux_doctor.platforms.base import PlatformAdapter, run_command_safe


class GenericLinuxAdapter(PlatformAdapter):
    """Adapter for Linux systems using standardized kernel interfaces."""

    def get_hardware_info(self) -> Dict[str, Any]:
        info: Dict[str, Any] = {}
        # DMI product name / vendor if readable without root
        sys_vendor = Path("/sys/class/dmi/id/sys_vendor")
        product_name = Path("/sys/class/dmi/id/product_name")
        chassis_type = Path("/sys/class/dmi/id/chassis_type")

        if sys_vendor.exists():
            try:
                info["vendor"] = sys_vendor.read_text().strip()
            except Exception:
                pass
        if product_name.exists():
            try:
                info["product"] = product_name.read_text().strip()
            except Exception:
                pass
        if chassis_type.exists():
            try:
                # Chassis type 8, 9, 10, 11, 14, 30, 31, 32 are laptop/portable
                ct = int(chassis_type.read_text().strip())
                info["is_laptop"] = ct in (8, 9, 10, 11, 14, 30, 31, 32)
            except Exception:
                info["is_laptop"] = False
        else:
            # Check presence of battery in power_supply
            ps = Path("/sys/class/power_supply")
            if ps.exists():
                bats = [b for b in ps.iterdir() if b.name.startswith("BAT")]
                info["is_laptop"] = len(bats) > 0
            else:
                info["is_laptop"] = False

        return info

    def get_service_failures(self) -> List[Dict[str, Any]]:
        failures = []
        if shutil.which("systemctl"):
            ret, stdout, _ = run_command_safe(
                ["systemctl", "--failed", "--no-legend", "--plain"], timeout=5
            )
            if ret == 0 and stdout:
                for line in stdout.splitlines():
                    parts = line.strip().split()
                    if parts:
                        unit = parts[0]
                        desc = " ".join(parts[4:]) if len(parts) >= 5 else "Failed service"
                        failures.append({"unit": unit, "description": desc})
        return failures

    def get_package_updates_status(self) -> Dict[str, Any]:
        result = {
            "manager": "Unknown",
            "pending_updates_count": 0,
            "broken_packages": [],
            "error": None,
        }
        # Check APT
        if shutil.which("apt-get"):
            result["manager"] = "APT"
            # Safe simulate upgrade check
            ret, stdout, stderr = run_command_safe(
                ["apt-get", "-s", "upgrade"], timeout=8
            )
            if ret == 0:
                for line in stdout.splitlines():
                    if "upgraded," in line and "newly installed," in line:
                        parts = line.split(",")
                        try:
                            result["pending_updates_count"] = int(parts[0].strip().split()[0])
                        except Exception:
                            pass
            elif "Could not open lock file" in stderr or "Permission denied" in stderr:
                result["error"] = "Requires elevated permissions to check pending updates cache"
        # Check DNF
        elif shutil.which("dnf"):
            result["manager"] = "DNF"
            ret, stdout, _ = run_command_safe(["dnf", "check-update", "-q"], timeout=8)
            if ret == 100:  # DNF returns 100 if updates are available
                lines = [l for l in stdout.splitlines() if l.strip()]
                result["pending_updates_count"] = len(lines)
        # Check Pacman
        elif shutil.which("checkupdates"):
            result["manager"] = "Pacman"
            ret, stdout, _ = run_command_safe(["checkupdates"], timeout=8)
            if ret == 0 and stdout:
                result["pending_updates_count"] = len(stdout.splitlines())
        return result

    def get_firewall_status(self) -> Dict[str, Any]:
        res = {"active": False, "type": "None", "details": ""}
        if shutil.which("ufw"):
            ret, stdout, stderr = run_command_safe(["ufw", "status"], timeout=4)
            if ret == 0:
                is_active = "Status: active" in stdout
                return {"active": is_active, "type": "ufw", "details": stdout.splitlines()[0] if stdout else ""}
            elif "permission denied" in stderr.lower() or ret != 0:
                return {"active": False, "type": "ufw", "details": "Elevated privilege required to query UFW status"}
        if shutil.which("firewalld") or shutil.which("firewall-cmd"):
            ret, stdout, _ = run_command_safe(["firewall-cmd", "--state"], timeout=4)
            if ret == 0 and "running" in stdout:
                return {"active": True, "type": "firewalld", "details": "firewalld is running"}
        if shutil.which("nft"):
            return {"active": True, "type": "nftables", "details": "nftables installed"}
        return res

    def get_secure_boot_status(self) -> Dict[str, Any]:
        res = {"enabled": False, "supported": True, "details": "Unknown"}
        if shutil.which("mokutil"):
            ret, stdout, _ = run_command_safe(["mokutil", "--sb-state"], timeout=4)
            if ret == 0:
                enabled = "SecureBoot enabled" in stdout
                return {"enabled": enabled, "supported": True, "details": stdout}
        # Check EFI variables in sysfs
        efivars = Path("/sys/firmware/efi/efivars")
        if not efivars.exists():
            return {"enabled": False, "supported": False, "details": "Legacy BIOS / Non-EFI system"}
        return res
