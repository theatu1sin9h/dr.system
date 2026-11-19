"""Safe Maintenance and Repair Engine.

Read-only by default. Requires explicit review and confirmation before executing any action.
Uses allowlisted safe commands and avoids arbitrary or destructive shell operations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import shutil
from linux_doctor.core.detector import OSDetector, OSInfo
from linux_doctor.platforms.base import run_command_safe


class RiskLevel(str, Enum):
    LOW = "low"          # Safe read-only or harmless cache cleanups
    MODERATE = "moderate"  # Service restarts or package cache purges
    HIGH = "high"        # Package updates, service configuration changes


@dataclass
class RepairAction:
    id: str
    title: str
    description: str
    problem: str
    command: List[str]
    command_str: str
    why_needed: str
    risk_level: RiskLevel
    required_permissions: str  # "User", "Elevated / Root"
    possible_side_effects: str
    is_reversible: bool
    reversal_instructions: str
    backup_recommendation: str


class SafeMaintenanceEngine:
    """Manages allowlisted repair recommendations and executes confirmed repairs."""

    # Explicit allowlist of allowed binary commands to prevent arbitrary execution
    COMMAND_ALLOWLIST = {
        "apt-get", "apt", "dnf", "pacman", "zypper",
        "systemctl", "journalctl", "ufw", "firewall-cmd",
        "sync", "echo", "powershell"
    }

    @classmethod
    def generate_recommendations(
        cls, findings_by_module: Dict[str, List[Any]], os_info: OSInfo
    ) -> List[RepairAction]:
        actions: List[RepairAction] = []

        # Check for inactive firewall
        sec_findings = findings_by_module.get("security", [])
        for f in sec_findings:
            if getattr(f, "id", "") == "sec_firewall_inactive":
                if os_info.is_linux:
                    if shutil.which("ufw"):
                        actions.append(
                            RepairAction(
                                id="enable_ufw",
                                title="Enable UFW (Uncomplicated Firewall)",
                                description="Activates standard host firewall protection.",
                                problem="Firewall is currently inactive, leaving open ports unfiltered.",
                                command=["sudo", "ufw", "enable"],
                                command_str="sudo ufw enable",
                                why_needed="Protects computer from unauthorized inbound network scans and connections.",
                                risk_level=RiskLevel.LOW,
                                required_permissions="Elevated / Root",
                                possible_side_effects="Existing custom network services without open rules may be blocked.",
                                is_reversible=True,
                                reversal_instructions="Run 'sudo ufw disable' to revert.",
                                backup_recommendation="Ensure SSH port 22 is allowed if on remote machine.",
                            )
                        )
                    elif shutil.which("firewall-cmd"):
                        actions.append(
                            RepairAction(
                                id="enable_firewalld",
                                title="Start and Enable Firewalld",
                                description="Activates firewalld service.",
                                problem="Firewalld daemon is stopped.",
                                command=["sudo", "systemctl", "enable", "--now", "firewalld"],
                                command_str="sudo systemctl enable --now firewalld",
                                why_needed="Provides active packet filtering.",
                                risk_level=RiskLevel.LOW,
                                required_permissions="Elevated / Root",
                                possible_side_effects="None for standard desktop usage.",
                                is_reversible=True,
                                reversal_instructions="Run 'sudo systemctl stop firewalld' to revert.",
                                backup_recommendation="None needed.",
                            )
                        )

        # Check for package updates / cache cleanup
        if os_info.package_manager == "APT":
            actions.append(
                RepairAction(
                    id="apt_clean_cache",
                    title="Clean Obsolete APT Package Cache",
                    description="Safely removes cached .deb package files to reclaim disk space.",
                    problem="Old deb packages accumulate in /var/cache/apt/archives.",
                    command=["sudo", "apt-get", "autoclean"],
                    command_str="sudo apt-get autoclean",
                    why_needed="Reclaims storage safely without removing installed software.",
                    risk_level=RiskLevel.LOW,
                    required_permissions="Elevated / Root",
                    possible_side_effects="Subsequent re-installs of the exact same package version may require redownload.",
                    is_reversible=False,
                    reversal_instructions="Packages will simply redownload when requested.",
                    backup_recommendation="None needed.",
                )
            )

        # Check for failed services
        stability_findings = findings_by_module.get("stability", [])
        for f in stability_findings:
            if "stability_service" in getattr(f, "id", ""):
                failed_units = getattr(f, "technical_details", {}).get("failed_units", [])
                if failed_units:
                    unit = failed_units[0]
                    actions.append(
                        RepairAction(
                            id=f"reset_failed_service_{unit}",
                            title=f"Reset Failed Service State ({unit})",
                            description=f"Clears failed state marker for unit '{unit}'.",
                            problem=f"Service '{unit}' entered a failed state.",
                            command=["sudo", "systemctl", "reset-failed", unit],
                            command_str=f"sudo systemctl reset-failed {unit}",
                            why_needed="Allows service manager to re-attempt clean startup.",
                            risk_level=RiskLevel.LOW,
                            required_permissions="Elevated / Root",
                            possible_side_effects="None.",
                            is_reversible=False,
                            reversal_instructions="None needed.",
                            backup_recommendation="None needed.",
                        )
                    )

        return actions

    @classmethod
    def execute_repair(cls, action: RepairAction, user_confirmed: bool) -> Dict[str, Any]:
        """Safely executes a repair action only if explicitly confirmed and allowlisted."""
        if not user_confirmed:
            return {"success": False, "message": "Repair was cancelled: User confirmation is mandatory."}

        base_bin = action.command[0]
        if base_bin == "sudo" and len(action.command) > 1:
            base_bin = action.command[1]

        if base_bin not in cls.COMMAND_ALLOWLIST:
            return {"success": False, "message": f"Security restriction: Command '{base_bin}' is not allowlisted."}

        ret, stdout, stderr = run_command_safe(action.command, timeout=15)
        if ret == 0:
            return {"success": True, "message": f"Successfully executed '{action.command_str}'.", "output": stdout}
        else:
            return {"success": False, "message": f"Execution failed (code {ret}): {stderr or stdout}"}
