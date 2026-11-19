"""Base platform abstract interfaces and execution utilities."""

import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


def run_command_safe(
    cmd: List[str], timeout: int = 8
) -> Tuple[int, str, str]:
    """Execute command safely with strict timeout and no shell=True injection risk."""
    if not cmd or not shutil.which(cmd[0]):
        return -1, "", f"Command '{cmd[0] if cmd else ''}' not found"

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            errors="replace",
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except PermissionError:
        return -1, "", "Permission denied"
    except Exception as e:
        return -1, "", str(e)


class PlatformAdapter(ABC):
    """Abstract base adapter for OS-specific hardware/service operations."""

    @abstractmethod
    def get_hardware_info(self) -> Dict[str, Any]:
        """Collect platform specific hardware facts."""
        pass

    @abstractmethod
    def get_service_failures(self) -> List[Dict[str, Any]]:
        """Collect failed system background services."""
        pass

    @abstractmethod
    def get_package_updates_status(self) -> Dict[str, Any]:
        """Check for pending/broken packages or updates."""
        pass

    @abstractmethod
    def get_firewall_status(self) -> Dict[str, Any]:
        """Check status of system firewall."""
        pass

    @abstractmethod
    def get_secure_boot_status(self) -> Dict[str, Any]:
        """Check if Secure Boot is active."""
        pass
