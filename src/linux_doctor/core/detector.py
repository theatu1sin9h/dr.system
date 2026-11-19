"""OS and Hardware Architecture Detection Engine.

Accurately detects operating system distributions, kernels, init systems,
package managers, desktop environments, display servers, and system architecture.
"""

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class OSInfo:
    system: str  # "Linux", "Windows", "Darwin", etc.
    name: str  # "Ubuntu", "Fedora", "Windows 11", etc.
    version: str
    kernel: str
    architecture: str
    is_linux: bool
    is_windows: bool
    package_manager: Optional[str] = None
    desktop_environment: Optional[str] = None
    display_server: Optional[str] = None  # "Wayland", "X11", "Windows DWM", None
    init_system: Optional[str] = None  # "systemd", "openrc", "init", "Windows SCM"
    audio_server: Optional[str] = None  # "PipeWire", "PulseAudio", "ALSA", "Windows Audio"
    powershell_version: Optional[str] = None
    windows_build: Optional[str] = None
    details: Dict[str, str] = field(default_factory=dict)


class OSDetector:
    """Detects OS environment cleanly without crashing or executing unsafe commands."""

    @staticmethod
    def detect_architecture() -> str:
        arch = platform.machine().lower()
        if arch in ("x86_64", "amd64"):
            return "x86_64"
        elif arch in ("aarch64", "arm64"):
            return "ARM64"
        elif "arm" in arch:
            return "ARM32"
        return arch or platform.architecture()[0]

    @classmethod
    def detect(cls) -> OSInfo:
        sys_type = platform.system()
        arch = cls.detect_architecture()

        if sys_type == "Linux":
            return cls._detect_linux(arch)
        elif sys_type == "Windows":
            return cls._detect_windows(arch)
        else:
            return OSInfo(
                system=sys_type,
                name=f"{sys_type} ({platform.release()})",
                version=platform.release(),
                kernel=platform.version(),
                architecture=arch,
                is_linux=False,
                is_windows=False,
            )

    @classmethod
    def _detect_linux(cls, arch: str) -> OSInfo:
        distro_id = "generic"
        distro_name = "Linux"
        distro_version = platform.release()
        details: Dict[str, str] = {}

        # Parse /etc/os-release or /usr/lib/os-release
        os_release_paths = [Path("/etc/os-release"), Path("/usr/lib/os-release")]
        for p in os_release_paths:
            if p.exists() and p.is_file():
                try:
                    with open(p, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            line = line.strip()
                            if "=" in line and not line.startswith("#"):
                                k, v = line.split("=", 1)
                                val = v.strip("\"'")
                                details[k] = val
                    if "NAME" in details:
                        distro_name = details["NAME"]
                    if "VERSION_ID" in details:
                        distro_version = details["VERSION_ID"]
                    elif "VERSION" in details:
                        distro_version = details["VERSION"]
                    if "ID" in details:
                        distro_id = details["ID"].lower()
                    break
                except Exception:
                    pass

        # Detect Package Manager
        pkg_manager = cls._detect_linux_package_manager()

        # Detect Desktop Environment
        de = (
            os.environ.get("XDG_CURRENT_DESKTOP")
            or os.environ.get("DESKTOP_SESSION")
            or os.environ.get("XDG_SESSION_DESKTOP")
        )

        # Detect Display Server
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session_type == "wayland":
            display_server = "Wayland"
        elif session_type == "x11":
            display_server = "X11"
        elif os.environ.get("WAYLAND_DISPLAY"):
            display_server = "Wayland"
        elif os.environ.get("DISPLAY"):
            display_server = "X11"
        else:
            display_server = "Headless / TTY"

        # Detect Init System
        init_system = cls._detect_linux_init_system()

        # Detect Audio Server
        audio_server = cls._detect_linux_audio_server()

        return OSInfo(
            system="Linux",
            name=distro_name,
            version=distro_version,
            kernel=platform.release(),
            architecture=arch,
            is_linux=True,
            is_windows=False,
            package_manager=pkg_manager,
            desktop_environment=de,
            display_server=display_server,
            init_system=init_system,
            audio_server=audio_server,
            details=details,
        )

    @classmethod
    def _detect_linux_package_manager(cls) -> str:
        # Check available package managers in order of specificity
        managers = [
            ("apt", "APT"),
            ("dnf", "DNF"),
            ("pacman", "Pacman"),
            ("zypper", "Zypper"),
            ("yum", "YUM"),
            ("apk", "APK"),
            ("xbps-install", "XBPS"),
            ("eopkg", "EOPKG"),
            ("emerge", "Portage"),
            ("nix-env", "Nix"),
        ]
        for binary, display in managers:
            if shutil.which(binary):
                return display
        return "Unknown"

    @classmethod
    def _detect_linux_init_system(cls) -> str:
        try:
            if Path("/run/systemd/system").exists():
                return "systemd"
            if Path("/sbin/openrc").exists() or Path("/etc/init.d").exists():
                return "SysVinit/OpenRC"
            # Read PID 1 comm
            comm_path = Path("/proc/1/comm")
            if comm_path.exists():
                name = comm_path.read_text().strip()
                if name:
                    return name
        except Exception:
            pass
        return "Unknown"

    @classmethod
    def _detect_linux_audio_server(cls) -> str:
        # Check active processes or runtime sockets
        user_runtime = os.environ.get("XDG_RUNTIME_DIR", "")
        if user_runtime:
            pipewire_sock = Path(user_runtime) / "pipewire-0"
            pulse_sock = Path(user_runtime) / "pulse" / "native"
            if pipewire_sock.exists():
                return "PipeWire"
            if pulse_sock.exists():
                return "PulseAudio"

        # Check binaries in path
        if shutil.which("pipewire") or shutil.which("pw-cli"):
            return "PipeWire"
        elif shutil.which("pulseaudio") or shutil.which("pactl"):
            return "PulseAudio"
        elif Path("/proc/asound").exists():
            return "ALSA"
        return "Audio Server Undetected"

    @classmethod
    def _detect_windows(cls, arch: str) -> OSInfo:
        version = platform.version()
        release = platform.release()  # e.g., '10', '11'
        build = ""
        win_name = f"Windows {release}"

        # If release is 10, check build number for Windows 11 (build >= 22000)
        try:
            parts = version.split(".")
            if len(parts) >= 3:
                build_num = int(parts[2])
                build = str(build_num)
                if build_num >= 22000 and release == "10":
                    win_name = "Windows 11"
        except Exception:
            pass

        # Check powershell version safely if on Windows
        pw_ver = None
        if shutil.which("powershell"):
            try:
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if res.returncode == 0:
                    pw_ver = res.stdout.strip()
            except Exception:
                pass

        return OSInfo(
            system="Windows",
            name=win_name,
            version=release,
            kernel=version,
            architecture=arch,
            is_linux=False,
            is_windows=True,
            package_manager="winget" if shutil.which("winget") else "None",
            desktop_environment="Windows Shell (Explorer)",
            display_server="Desktop Window Manager (DWM)",
            init_system="Service Control Manager (SCM)",
            audio_server="Windows Audio Service",
            powershell_version=pw_ver,
            windows_build=build or version,
        )
