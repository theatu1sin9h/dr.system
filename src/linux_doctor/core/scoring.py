"""System Health Scoring Engine.

Transparent, non-fabricated, confidence-weighted health calculation.
Distinguishes hardware degradation from temporary resource usage.
Treats missing sensors as N/A without unfair score penalties.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult


CATEGORY_WEIGHTS: Dict[str, float] = {
    "cpu": 0.10,
    "memory": 0.10,
    "storage": 0.15,
    "battery": 0.10,
    "gpu": 0.10,
    "display": 0.10,
    "audio": 0.05,
    "network": 0.05,
    "stability": 0.15,
    "security": 0.10,
}


@dataclass
class HealthScoreReport:
    overall_score: int  # 0 to 100
    status_label: str  # Excellent, Good, Needs attention, Poor, Critical
    category_scores: Dict[str, float] = field(default_factory=dict)
    confidence: float = 1.0  # 0.0 to 1.0
    coverage_percentage: float = 100.0
    active_weights: Dict[str, float] = field(default_factory=dict)
    deductions: List[str] = field(default_factory=list)
    hardware_degradations: List[str] = field(default_factory=list)
    temporary_load_factors: List[str] = field(default_factory=list)


class HealthScoringEngine:
    """Calculates transparent, realistic health score from diagnostic module outputs."""

    @staticmethod
    def get_status_label(score: int) -> str:
        if score >= 90:
            return "EXCELLENT"
        elif score >= 75:
            return "GOOD"
        elif score >= 60:
            return "NEEDS ATTENTION"
        elif score >= 40:
            return "POOR"
        else:
            return "CRITICAL"

    @classmethod
    def calculate(cls, results: Dict[str, ModuleResult]) -> HealthScoreReport:
        applicable_weights: Dict[str, float] = {}
        category_scores: Dict[str, float] = {}
        deductions: List[str] = []
        hardware_degradations: List[str] = []
        temporary_load_factors: List[str] = []

        total_possible_modules = len(CATEGORY_WEIGHTS)
        evaluated_modules = 0
        total_confidence = 0.0

        for category, base_weight in CATEGORY_WEIGHTS.items():
            result = results.get(category)

            # If module is not present, unsupported, or explicitly marked not supported
            if not result or not result.supported:
                # Missing or unsupported check is treated as N/A (e.g. desktop battery)
                continue

            # Check if this is a battery on desktop (unsupported/not applicable)
            if category == "battery" and result.metrics.get("is_desktop_no_battery", False):
                continue

            evaluated_modules += 1
            applicable_weights[category] = base_weight
            total_confidence += result.confidence

            # Calculate individual category score
            cat_score = max(0.0, min(100.0, result.score))
            category_scores[category] = round(cat_score, 1)

            # Process findings for explanation
            for finding in result.findings:
                if finding.severity in (FindingSeverity.WARNING, FindingSeverity.CRITICAL):
                    explanation = f"[{result.display_name}] {finding.title} (-{finding.deduction_points:.1f} pts)"
                    deductions.append(explanation)
                    if finding.is_hardware_degradation:
                        hardware_degradations.append(f"{result.display_name}: {finding.title}")
                    else:
                        temporary_load_factors.append(f"{result.display_name}: {finding.title}")

        # If no modules could be evaluated (edge case)
        if not applicable_weights:
            return HealthScoreReport(
                overall_score=100,
                status_label="UNKNOWN",
                category_scores={},
                confidence=0.0,
                coverage_percentage=0.0,
                active_weights={},
                deductions=["No diagnostic modules could be evaluated on this system."],
            )

        # Normalize weights so they sum to 1.0 across active, supported checks
        weight_sum = sum(applicable_weights.values())
        normalized_weights = {k: v / weight_sum for k, v in applicable_weights.items()}

        # Weighted calculation
        final_score = 0.0
        for cat, weight in normalized_weights.items():
            final_score += category_scores[cat] * weight

        overall_int_score = int(round(final_score))
        overall_int_score = max(0, min(100, overall_int_score))

        avg_confidence = total_confidence / evaluated_modules if evaluated_modules > 0 else 0.0
        coverage_pct = round((evaluated_modules / total_possible_modules) * 100.0, 1)

        return HealthScoreReport(
            overall_score=overall_int_score,
            status_label=cls.get_status_label(overall_int_score),
            category_scores=category_scores,
            confidence=round(avg_confidence, 2),
            coverage_percentage=coverage_pct,
            active_weights={k: round(v, 3) for k, v in normalized_weights.items()},
            deductions=deductions,
            hardware_degradations=hardware_degradations,
            temporary_load_factors=temporary_load_factors,
        )
