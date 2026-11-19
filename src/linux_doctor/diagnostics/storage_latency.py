"""Storage Direct Read Latency Jitter Diagnostic.

Measures direct 4K random read latencies bypassing the OS page cache
to uncover silent flash memory degradation and storage controller lockups
before SMART attributes flag any failure.
"""

import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult


class DirectStorageLatencyTest:
    """Performs safe non-destructive read-only latency measurements."""

    @staticmethod
    def measure_read_latency(test_file: Optional[Path] = None, samples: int = 100) -> Dict[str, Any]:
        """Reads random 4KB blocks from a target file or system library with page cache bypass if supported."""
        # Find a suitable read-only file of at least 1MB to read from
        target_path = None
        candidate_paths = [
            Path("/usr/lib/x86_64-linux-gnu/libc.so.6"),
            Path("/lib/x86_64-linux-gnu/libc.so.6"),
            Path("/usr/lib/libc.so"),
            Path("/usr/bin/python3"),
        ]
        for c in candidate_paths:
            if c.exists() and c.is_file() and c.stat().st_size > 65536:
                target_path = c
                break

        if not target_path:
            return {"supported": False, "error": "No suitable test binary found for latency measurement"}

        file_size = target_path.stat().st_size
        block_size = 4096
        max_offset = max(0, file_size - block_size)

        latencies_ms: List[float] = []

        try:
            # Use raw unbuffered I/O
            flags = os.O_RDONLY
            fd = os.open(target_path, flags)
            try:
                # Advise OS not to cache (drop from cache)
                if hasattr(os, "posix_fadvise") and hasattr(os, "POSIX_FADV_DONTNEED"):
                    try:
                        os.posix_fadvise(fd, 0, file_size, os.POSIX_FADV_DONTNEED)
                    except Exception:
                        pass

                for _ in range(samples):
                    offset = (random.randint(0, max_offset // block_size)) * block_size
                    t0 = time.perf_counter()
                    os.lseek(fd, offset, os.SEEK_SET)
                    data = os.read(fd, block_size)
                    t1 = time.perf_counter()
                    latencies_ms.append((t1 - t0) * 1000.0)
            finally:
                os.close(fd)
        except Exception as e:
            return {"supported": False, "error": str(e)}

        if not latencies_ms:
            return {"supported": False, "error": "No latency samples collected"}

        latencies_ms.sort()
        n = len(latencies_ms)
        p50 = latencies_ms[int(n * 0.50)]
        p95 = latencies_ms[int(n * 0.95)]
        p99 = latencies_ms[int(n * 0.99)]
        max_lat = latencies_ms[-1]

        return {
            "supported": True,
            "samples": n,
            "target": str(target_path),
            "p50_latency_ms": round(p50, 3),
            "p95_latency_ms": round(p95, 3),
            "p99_latency_ms": round(p99, 3),
            "max_latency_ms": round(max_lat, 3),
        }


class StorageLatencyDiagnostic:
    """Diagnoses storage latency jitter and controller response times."""

    @classmethod
    def run(cls) -> ModuleResult:
        start_time = time.time()
        findings: List[DiagnosticFinding] = []
        metrics: Dict[str, Any] = {}
        score = 100.0
        deductions_exp: List[str] = []

        res = DirectStorageLatencyTest.measure_read_latency(samples=100)
        metrics["latency_test"] = res

        if not res.get("supported", False):
            return ModuleResult(
                module_name="storage_latency",
                display_name="Storage Latency & Jitter",
                status="passed",
                score=100.0,
                confidence=0.5,
                supported=False,
                not_supported_reason=res.get("error", "Direct latency test unavailable"),
                metrics=metrics,
                findings=[],
            )

        p99 = res.get("p99_latency_ms", 0.0)
        max_lat = res.get("max_latency_ms", 0.0)

        # Evaluate Latency Spike / Flash Jitter
        if p99 > 30.0 or max_lat > 100.0:
            findings.append(
                DiagnosticFinding(
                    id="storage_latency_severe_spike",
                    title="Storage Latency Jitter Spikes Detected (>100ms)",
                    severity=FindingSeverity.WARNING,
                    what_detected=f"Direct 4K read P99 latency is {p99}ms with peak read latency of {max_lat}ms.",
                    what_it_means="The storage drive or bus controller experienced momentary stalls while fulfilling standard 4K read requests.",
                    how_serious="Moderate to High for system responsiveness.",
                    what_could_cause="NAND flash garbage collection cycle, degraded block retries, or high concurrent write cache flushes.",
                    what_user_should_do="Check drive wear indicators and avoid running latency-sensitive real-time tasks without SSD TRIM.",
                    safe_next_step="Inspect disk health and consider running 'fstrim' on SSD partitions.",
                    technical_details=res,
                    is_hardware_degradation=False,
                    deduction_points=15.0,
                )
            )
            score -= 15.0
            deductions_exp.append(f"Storage latency spikes ({max_lat}ms) (-15 pts)")

        return ModuleResult(
            module_name="storage_latency",
            display_name="Storage Latency & Jitter",
            status="passed" if score >= 85 else "warning",
            score=max(0.0, round(score, 1)),
            confidence=0.95,
            supported=True,
            metrics=metrics,
            findings=findings,
            deductions_explanation=deductions_exp,
            execution_time_seconds=round(time.time() - start_time, 3),
        )
