"""Differential Health Snapshot and Regression Tracking Engine.

Captures timestamped, signed compact state snapshots of system metrics.
Enables "Time-Travel Diffing" (e.g., 'What changed since yesterday or the last update?').
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from linux_doctor.core.findings import ModuleResult
from linux_doctor.core.scoring import HealthScoreReport


class SnapshotManager:
    """Stores and computes differences between historical diagnostic scans."""

    DEFAULT_STORE_DIR = Path.home() / ".config" / "linux-doctor" / "snapshots"

    @classmethod
    def save_snapshot(
        cls,
        os_name: str,
        score_report: HealthScoreReport,
        results: Dict[str, ModuleResult],
        label: Optional[str] = None,
        store_dir: Optional[Path] = None,
    ) -> Path:
        target_dir = store_dir or cls.DEFAULT_STORE_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{timestamp_str}.json"
        file_path = target_dir / filename

        snapshot_data = {
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "label": label or "Scheduled / Manual Scan",
            "overall_score": score_report.overall_score,
            "status_label": score_report.status_label,
            "os_name": os_name,
            "category_scores": score_report.category_scores,
            "metrics_summary": {
                k: {
                    "score": v.score,
                    "status": v.status,
                    "metrics": {
                        mk: mv
                        for mk, mv in v.metrics.items()
                        if isinstance(mv, (int, float, str, bool))
                    },
                }
                for k, v in results.items()
            },
        }

        file_path.write_text(json.dumps(snapshot_data, indent=2), encoding="utf-8")
        return file_path

    @classmethod
    def list_snapshots(cls, store_dir: Optional[Path] = None) -> List[Path]:
        target_dir = store_dir or cls.DEFAULT_STORE_DIR
        if not target_dir.exists():
            return []
        return sorted(target_dir.glob("snapshot_*.json"), reverse=True)

    @classmethod
    def compare_snapshots(cls, path_old: Path, path_new: Path) -> Dict[str, Any]:
        """Calculates differences between two historical snapshots."""
        data_old = json.loads(path_old.read_text(encoding="utf-8"))
        data_new = json.loads(path_new.read_text(encoding="utf-8"))

        score_diff = data_new.get("overall_score", 0) - data_old.get("overall_score", 0)

        category_diffs: Dict[str, Dict[str, float]] = {}
        old_cats = data_old.get("category_scores", {})
        new_cats = data_new.get("category_scores", {})

        for cat in set(old_cats.keys()).union(new_cats.keys()):
            s_old = old_cats.get(cat, 100.0)
            s_new = new_cats.get(cat, 100.0)
            diff = round(s_new - s_old, 1)
            category_diffs[cat] = {"old": s_old, "new": s_new, "delta": diff}

        regressions = []
        improvements = []
        for cat, vals in category_diffs.items():
            if vals["delta"] < -5.0:
                regressions.append(f"{cat.title()}: Score dropped by {abs(vals['delta']):.1f} points")
            elif vals["delta"] > 5.0:
                improvements.append(f"{cat.title()}: Score improved by {vals['delta']:.1f} points")

        return {
            "old_date": data_old.get("timestamp"),
            "new_date": data_new.get("timestamp"),
            "overall_score_old": data_old.get("overall_score"),
            "overall_score_new": data_new.get("overall_score"),
            "score_diff": score_diff,
            "category_diffs": category_diffs,
            "regressions": regressions,
            "improvements": improvements,
        }
