"""Diagnostic Orchestrator and Scanner Engine (Linux Doctor 2.0).

Runs standard and advanced diagnostic modules (PSI, direct storage latency,
thermal decay profiling, and cross-subsystem causality analysis).
"""

import time
from typing import Callable, Dict, List, Optional
from linux_doctor.core.causality import CausalityEngine, CausalityInsight
from linux_doctor.core.detector import OSDetector, OSInfo
from linux_doctor.core.findings import ModuleResult
from linux_doctor.core.scoring import HealthScoreReport, HealthScoringEngine
from linux_doctor.core.snapshots import SnapshotManager
from linux_doctor.diagnostics.audio import AudioDiagnostic
from linux_doctor.diagnostics.battery import BatteryDiagnostic
from linux_doctor.diagnostics.cpu import CPUDiagnostic
from linux_doctor.diagnostics.display import DisplayDiagnostic
from linux_doctor.diagnostics.drivers import DriversDiagnostic
from linux_doctor.diagnostics.gpu import GPUDiagnostic
from linux_doctor.diagnostics.memory import MemoryDiagnostic
from linux_doctor.diagnostics.network import NetworkDiagnostic
from linux_doctor.diagnostics.psi import PSIDiagnostic
from linux_doctor.diagnostics.security import SecurityDiagnostic
from linux_doctor.diagnostics.stability import StabilityDiagnostic
from linux_doctor.diagnostics.storage import StorageDiagnostic
from linux_doctor.diagnostics.storage_latency import StorageLatencyDiagnostic
from linux_doctor.diagnostics.temperature import TemperatureDiagnostic
from linux_doctor.diagnostics.thermal_decay import ThermalDecayDiagnostic


class DiagnosticScanner:
    """Coordinates and executes system diagnostics."""

    AVAILABLE_MODULES = [
        ("cpu", "Processor (CPU)", CPUDiagnostic),
        ("memory", "Memory (RAM)", MemoryDiagnostic),
        ("storage", "Storage & Disks", StorageDiagnostic),
        ("storage_latency", "Storage Latency & Jitter", StorageLatencyDiagnostic),
        ("gpu", "Graphics (GPU)", GPUDiagnostic),
        ("display", "Display & Monitors", DisplayDiagnostic),
        ("audio", "Audio & Sound", AudioDiagnostic),
        ("battery", "Battery & Power", BatteryDiagnostic),
        ("network", "Network & Connectivity", NetworkDiagnostic),
        ("temperature", "Thermals & Cooling", TemperatureDiagnostic),
        ("thermal_decay", "Thermal Decay Profiler", ThermalDecayDiagnostic),
        ("psi", "Kernel Pressure Stalls (PSI)", PSIDiagnostic),
        ("drivers", "Hardware Drivers", DriversDiagnostic),
        ("stability", "System Stability", StabilityDiagnostic),
        ("security", "Security & Updates", SecurityDiagnostic),
    ]

    def __init__(self):
        self.os_info: OSInfo = OSDetector.detect()
        self.results: Dict[str, ModuleResult] = {}
        self.score_report: Optional[HealthScoreReport] = None
        self.causality_insights: List[CausalityInsight] = []
        self.scan_start_time: float = 0.0
        self.scan_duration_seconds: float = 0.0

    def run_scan(
        self,
        module_keys: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str, int, int, Optional[ModuleResult]], None]] = None,
        save_snapshot: bool = True,
    ) -> Dict[str, ModuleResult]:
        """Runs the diagnostic scan with progress reporting and cross-subsystem analysis."""
        self.scan_start_time = time.time()
        self.results.clear()

        modules_to_run = [
            (k, name, diag_cls)
            for k, name, diag_cls in self.AVAILABLE_MODULES
            if module_keys is None or k in module_keys
        ]

        total = len(modules_to_run)
        for idx, (key, name, diag_cls) in enumerate(modules_to_run, start=1):
            if progress_callback:
                progress_callback(name, idx, total, None)

            try:
                result = diag_cls.run()
            except Exception as e:
                result = ModuleResult(
                    module_name=key,
                    display_name=name,
                    status="unsupported",
                    score=100.0,
                    confidence=0.0,
                    supported=False,
                    not_supported_reason=f"Diagnostic error: {str(e)}",
                    metrics={},
                    findings=[],
                )

            self.results[key] = result

            if progress_callback:
                progress_callback(name, idx, total, result)

        self.scan_duration_seconds = round(time.time() - self.scan_start_time, 2)
        self.score_report = HealthScoringEngine.calculate(self.results)

        # Run cross-subsystem causality analysis
        self.causality_insights = CausalityEngine.analyze(self.results)

        # Save historical snapshot if this was a full scan
        if save_snapshot and (module_keys is None or len(module_keys) >= len(self.AVAILABLE_MODULES) - 2):
            try:
                SnapshotManager.save_snapshot(
                    os_name=self.os_info.name,
                    score_report=self.score_report,
                    results=self.results,
                )
            except Exception:
                pass

        return self.results
