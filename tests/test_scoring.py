"""Unit tests for the Health Scoring Engine."""

from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult
from linux_doctor.core.scoring import HealthScoringEngine


def test_scoring_perfect():
    results = {
        "cpu": ModuleResult(module_name="cpu", display_name="CPU", score=100.0),
        "memory": ModuleResult(module_name="memory", display_name="RAM", score=100.0),
        "storage": ModuleResult(module_name="storage", display_name="Storage", score=100.0),
    }
    report = HealthScoringEngine.calculate(results)
    assert report.overall_score == 100
    assert report.status_label == "EXCELLENT"


def test_scoring_with_deductions_and_unsupported_battery():
    results = {
        "cpu": ModuleResult(module_name="cpu", display_name="CPU", score=80.0),
        "memory": ModuleResult(module_name="memory", display_name="RAM", score=90.0),
        "battery": ModuleResult(
            module_name="battery",
            display_name="Battery",
            score=100.0,
            supported=False,
            metrics={"is_desktop_no_battery": True},
        ),
    }
    report = HealthScoringEngine.calculate(results)
    # Battery should not penalize score or appear as failure
    assert "battery" not in report.active_weights
    assert report.overall_score > 0
