"""User and process permission detection."""

import os
import ctypes
import platform


def is_root_or_admin() -> bool:
    """Returns True if the current process is running with root/administrator privileges."""
    if platform.system() == "Windows":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        try:
            return os.geteuid() == 0
        except AttributeError:
            return False


def get_current_user_name() -> str:
    """Safe user name lookup."""
    try:
        import getpass
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER") or os.environ.get("USERNAME") or "user"
