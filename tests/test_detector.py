"""Unit tests for OS detection engine across platforms."""

import platform
from unittest.mock import patch, mock_open
from linux_doctor.core.detector import OSDetector


def test_detect_architecture():
    arch = OSDetector.detect_architecture()
    assert arch in ("x86_64", "ARM64", "ARM32", platform.machine().lower())


def test_detect_linux():
    os_release_data = """NAME="Ubuntu"
VERSION_ID="24.04"
ID=ubuntu
"""
    with patch("platform.system", return_value="Linux"), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=os_release_data)):
        info = OSDetector.detect()
        assert info.is_linux is True
        assert info.is_windows is False
        assert info.name == "Ubuntu"
        assert info.version == "24.04"


def test_detect_windows():
    with patch("platform.system", return_value="Windows"), \
         patch("platform.release", return_value="11"), \
         patch("platform.version", return_value="10.0.22621"), \
         patch("shutil.which", return_value=None):
        info = OSDetector.detect()
        assert info.is_windows is True
        assert info.is_linux is False
        assert "Windows 11" in info.name
        assert info.init_system == "Service Control Manager (SCM)"
