"""Unit tests for Diagnostics, missing commands, and permissions."""

from unittest.mock import patch
from linux_doctor.diagnostics.cpu import CPUDiagnostic
from linux_doctor.diagnostics.battery import BatteryDiagnostic
from linux_doctor.diagnostics.memory import MemoryDiagnostic
from linux_doctor.diagnostics.storage import StorageDiagnostic
from linux_doctor.maintenance.repair import SafeMaintenanceEngine, RepairAction, RiskLevel
from linux_doctor.reports.generator import redact_sensitive_info


def test_cpu_diagnostic():
    res = CPUDiagnostic.run()
    assert res.module_name == "cpu"
    assert res.supported is True
    assert "logical_cores" in res.metrics


def test_memory_diagnostic():
    res = MemoryDiagnostic.run()
    assert res.module_name == "memory"
    assert "total_ram_gb" in res.metrics


def test_storage_diagnostic():
    res = StorageDiagnostic.run()
    assert res.module_name == "storage"
    assert isinstance(res.metrics.get("partitions"), list)


def test_battery_desktop_graceful():
    with patch("psutil.sensors_battery", return_value=None), \
         patch("pathlib.Path.exists", return_value=False):
        res = BatteryDiagnostic.run()
        assert res.supported is False
        assert res.metrics.get("is_desktop_no_battery") is True


def test_safe_maintenance_unconfirmed_blocks_execution():
    action = RepairAction(
        id="test_act",
        title="Test",
        description="desc",
        problem="prob",
        command=["echo", "hello"],
        command_str="echo hello",
        why_needed="testing",
        risk_level=RiskLevel.LOW,
        required_permissions="User",
        possible_side_effects="None",
        is_reversible=True,
        reversal_instructions="None",
        backup_recommendation="None",
    )
    result = SafeMaintenanceEngine.execute_repair(action, user_confirmed=False)
    assert result["success"] is False
    assert "User confirmation is mandatory" in result["message"]


def test_safe_maintenance_non_allowlisted_blocks_execution():
    action = RepairAction(
        id="bad_cmd",
        title="Bad",
        description="desc",
        problem="prob",
        command=["rm", "-rf", "/tmp/fake"],
        command_str="rm -rf /tmp/fake",
        why_needed="testing",
        risk_level=RiskLevel.HIGH,
        required_permissions="Root",
        possible_side_effects="Loss",
        is_reversible=False,
        reversal_instructions="None",
        backup_recommendation="None",
    )
    result = SafeMaintenanceEngine.execute_repair(action, user_confirmed=True)
    assert result["success"] is False
    assert "not allowlisted" in result["message"]


def test_report_redaction():
    text = "User connected from IP 192.168.1.55 with MAC 00:1A:2B:3C:4D:5E"
    redacted = redact_sensitive_info(text)
    assert "192.168.1.55" not in redacted
    assert "[REDACTED_IP]" in redacted
    assert "[REDACTED_MAC]" in redacted
