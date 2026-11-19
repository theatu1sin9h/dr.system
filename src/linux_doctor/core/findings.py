"""Diagnostic finding severity models and representations."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FindingSeverity(str, Enum):
    INFO = "info"
    PASSED = "passed"
    WARNING = "warning"
    CRITICAL = "critical"
    UNSUPPORTED = "unsupported"


class DiagnosticFinding(BaseModel):
    """Structured diagnostic finding with beginner-friendly and technical context."""

    id: str = Field(..., description="Unique identifier for finding category/type")
    title: str = Field(..., description="Short descriptive title of finding")
    severity: FindingSeverity = Field(
        default=FindingSeverity.INFO, description="Severity rating"
    )
    what_detected: str = Field(..., description="1. What was detected?")
    what_it_means: str = Field(..., description="2. What does it mean?")
    how_serious: str = Field(..., description="3. How serious is it?")
    what_could_cause: str = Field(..., description="4. What could cause it?")
    what_user_should_do: str = Field(..., description="5. What should the user do?")
    safe_next_step: str = Field(..., description="6. What is the safe next step?")
    technical_details: Dict[str, Any] = Field(
        default_factory=dict, description="Technical measurements and telemetry"
    )
    is_hardware_degradation: bool = Field(
        default=False,
        description="Distinguishes real physical degradation from transient resource usage",
    )
    deduction_points: float = Field(
        default=0.0,
        description="Points deducted from the category score (0.0 to 100.0 scale within category)",
    )


class ModuleResult(BaseModel):
    """Result from an individual diagnostic module."""

    module_name: str
    display_name: str
    status: str = "passed"  # passed, warning, critical, unsupported, skipped
    score: float = 100.0  # 0 to 100
    confidence: float = 1.0  # 0.0 to 1.0 based on sensor completeness
    supported: bool = True
    not_supported_reason: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    findings: List[DiagnosticFinding] = Field(default_factory=list)
    deductions_explanation: List[str] = Field(default_factory=list)
    execution_time_seconds: float = 0.0
