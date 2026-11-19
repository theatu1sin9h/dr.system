"""Unit tests for Linux Doctor 2.0 innovations: PSI, Storage Latency, and Snapshots."""

import json
from pathlib import Path
from unittest.mock import patch, mock_open
from linux_doctor.core.causality import CausalityEngine
from linux_doctor.core.findings import ModuleResult
from linux_doctor.core.snapshots import SnapshotManager
from linux_doctor.diagnostics.psi import PSIDiagnostic, PSIReader
from linux_doctor.diagnostics.storage_latency import DirectStorageLatencyTest, StorageLatencyDiagnostic


def test_psi_parser():
    fake_psi = """some avg10=2.50 avg60=1.20 avg300=0.80 total=123456
full avg10=0.10 avg60=0.05 avg300=0.01 total=999
"""
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.read_text", return_value=fake_psi):
        data = PSIReader.parse_psi_file(Path("/fake/psi"))
        assert "some" in data
        assert data["some"]["avg10"] == 2.50
        assert data["full"]["avg10"] == 0.10


def test_storage_latency_measurement():
    res = DirectStorageLatencyTest.measure_read_latency(samples=10)
    assert "supported" in res
    if res["supported"]:
        assert "p50_latency_ms" in res
        assert "p99_latency_ms" in res


def test_causality_thermal_throttling():
    results = {
        "temperature": ModuleResult(
            module_name="temperature",
            display_name="Thermals",
            metrics={"max_temperature_celsius": 92.0},
        ),
        "cpu": ModuleResult(
            module_name="cpu",
            display_name="CPU",
            metrics={"current_frequency_mhz": 1200.0, "max_frequency_mhz": 4000.0},
        ),
    }
    insights = CausalityEngine.analyze(results)
    assert len(insights) > 0
    assert "Thermal Throttling" in insights[0].title


def test_snapshot_comparison(tmp_path):
    snap1 = tmp_path / "snap1.json"
    snap2 = tmp_path / "snap2.json"

    data1 = {
        "timestamp": "2026-11-18T10:00:00",
        "overall_score": 95,
        "category_scores": {"cpu": 100.0, "storage": 90.0},
    }
    data2 = {
        "timestamp": "2026-11-19T10:00:00",
        "overall_score": 85,
        "category_scores": {"cpu": 100.0, "storage": 70.0},
    }

    snap1.write_text(json.dumps(data1))
    snap2.write_text(json.dumps(data2))

    comp = SnapshotManager.compare_snapshots(snap1, snap2)
    assert comp["score_diff"] == -10
    assert len(comp["regressions"]) == 1
    assert "Storage" in comp["regressions"][0]
