"""Factory for obtaining current platform adapter."""

import platform
from linux_doctor.platforms.base import PlatformAdapter
from linux_doctor.platforms.linux.generic import GenericLinuxAdapter
from linux_doctor.platforms.windows.system import WindowsAdapter


def get_platform_adapter() -> PlatformAdapter:
    """Returns the adapter matching the current operating system."""
    sys_name = platform.system()
    if sys_name == "Windows":
        return WindowsAdapter()
    return GenericLinuxAdapter()
