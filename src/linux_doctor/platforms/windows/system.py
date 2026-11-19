"""Windows platform adapter using safe CIM, WMI, and native PowerShell interfaces."""

import shutil
from typing import Any, Dict, List
from linux_doctor.platforms.base import PlatformAdapter, run_command_safe


class WindowsAdapter(PlatformAdapter):
    """Native Windows diagnostic provider."""

    def _run_ps(self, cmd: str, timeout: int = 8) -> str:
        if not shutil.which("powershell"):
            return ""
        ret, stdout, _ = run_command_safe(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            timeout=timeout,
        )
        return stdout if ret == 0 else ""

    def get_hardware_info(self) -> Dict[str, Any]:
        info: Dict[str, Any] = {"vendor": "Unknown", "product": "Unknown", "is_laptop": False}
        out = self._run_ps(
            "Get-CimInstance -ClassName Win32_ComputerSystem | Select-Object -Property Manufacturer,Model | ConvertTo-Json"
        )
        if out:
            import json
            try:
                data = json.loads(out)
                info["vendor"] = data.get("Manufacturer", "Unknown")
                info["product"] = data.get("Model", "Unknown")
            except Exception:
                pass
        # Check battery presence
        bat_out = self._run_ps("Get-CimInstance -ClassName Win32_Battery | Measure-Object | Select-Object -ExpandProperty Count")
        if bat_out and bat_out.isdigit() and int(bat_out) > 0:
            info["is_laptop"] = True
        return info

    def get_service_failures(self) -> List[Dict[str, Any]]:
        failures = []
        out = self._run_ps(
            "Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -ne 'Running' } | Select-Object Name,DisplayName | ConvertTo-Json"
        )
        if out:
            import json
            try:
                data = json.loads(out)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    failures.append({"unit": item.get("Name", ""), "description": item.get("DisplayName", "")})
            except Exception:
                pass
        return failures

    def get_package_updates_status(self) -> Dict[str, Any]:
        result = {"manager": "Windows Update / Winget", "pending_updates_count": 0, "broken_packages": [], "error": None}
        if shutil.which("winget"):
            ret, stdout, _ = run_command_safe(["winget", "upgrade"], timeout=10)
            if ret == 0 and stdout:
                lines = [l for l in stdout.splitlines() if "<" in l or "available" in l.lower()]
                result["pending_updates_count"] = len(lines)
        return result

    def get_firewall_status(self) -> Dict[str, Any]:
        out = self._run_ps("Get-NetFirewallProfile | Select-Object -ExpandProperty Enabled")
        if "True" in out:
            return {"active": True, "type": "Windows Defender Firewall", "details": "Active"}
        return {"active": False, "type": "Windows Defender Firewall", "details": "Profiles Inactive or Access Denied"}

    def get_secure_boot_status(self) -> Dict[str, Any]:
        out = self._run_ps("Confirm-SecureBootUEFI")
        if "True" in out:
            return {"enabled": True, "supported": True, "details": "Secure Boot Enabled"}
        elif "False" in out:
            return {"enabled": False, "supported": True, "details": "Secure Boot Disabled"}
        return {"enabled": False, "supported": False, "details": "Cmdlet Not Supported on Legacy BIOS"}
