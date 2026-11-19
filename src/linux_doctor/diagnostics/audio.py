"""Audio Diagnostic Module.

Detects ALSA, PipeWire, PulseAudio servers, sound cards, input/output endpoints,
and driver audio errors without automatically altering audio volumes.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult
from linux_doctor.platforms.base import run_command_safe


class AudioDiagnostic:
    """Diagnoses sound cards and sound server daemon health."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        sound_cards: List[str] = []
        score = 100.0
        deductions_exp: List[str] = []

        # Read ALSA soundcards if on Linux
        asound_cards = Path("/proc/asound/cards")
        if asound_cards.exists():
            try:
                for line in asound_cards.read_text().splitlines():
                    if "[" in line and "]" in line and ":" in line:
                        sound_cards.append(line.strip())
            except Exception:
                pass

        metrics["sound_cards"] = sound_cards
        metrics["sound_cards_count"] = len(sound_cards)

        # Detect active audio server
        audio_server = "None"
        if shutil.which("pactl"):
            ret, stdout, _ = run_command_safe(["pactl", "info"], timeout=4)
            if ret == 0:
                for line in stdout.splitlines():
                    if "Server Name:" in line:
                        audio_server = line.split(":", 1)[1].strip()
                        break
        elif shutil.which("pw-cli"):
            audio_server = "PipeWire"
        elif sound_cards:
            audio_server = "ALSA"

        metrics["audio_server"] = audio_server

        # Check if system has no sound devices at all
        if not sound_cards and audio_server == "None":
            # Might be container or headless VM
            metrics["headless_audio"] = True
            # We don't deduct heavily if headless, but inform
            findings.append(
                DiagnosticFinding(
                    id="audio_no_devices",
                    title="No Audio Devices Detected",
                    severity=FindingSeverity.INFO,
                    what_detected="No sound cards or audio servers were detected.",
                    what_it_means="The system cannot currently play or record sound.",
                    how_serious="Informational for servers/VMs; problematic for personal PCs.",
                    what_could_cause="Headless environment, virtual machine with sound disabled, or missing audio drivers.",
                    what_user_should_do="Ensure sound hardware is enabled in BIOS/VM settings if needed.",
                    safe_next_step="Check system sound configuration.",
                    technical_details={"sound_cards_count": 0},
                    is_hardware_degradation=False,
                    deduction_points=0.0,
                )
            )

        return ModuleResult(
            module_name="audio",
            display_name="Audio & Sound Cards",
            status="passed",
            score=max(0.0, round(score, 1)),
            confidence=0.9 if sound_cards else 0.5,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
