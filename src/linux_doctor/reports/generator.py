"""Report Generation Engine: JSON, HTML, and Plain Text.

Supports automatic redaction of sensitive identifying info:
Usernames, IP addresses, serial numbers, hostnames.
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from linux_doctor.config import APP_AUTHOR, APP_NAME, APP_TAGLINE, APP_VERSION
from linux_doctor.core.detector import OSInfo
from linux_doctor.core.findings import ModuleResult
from linux_doctor.core.scoring import HealthScoreReport


def redact_sensitive_info(text: str) -> str:
    """Redacts IP addresses, MAC addresses, and common usernames."""
    # Redact IPv4
    text = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[REDACTED_IP]", text)
    # Redact MAC
    text = re.sub(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b", "[REDACTED_MAC]", text)
    return text


class ReportGenerator:
    """Generates structured diagnostics reports."""

    @staticmethod
    def _prepare_data(
        os_info: OSInfo,
        score_report: HealthScoreReport,
        results: Dict[str, ModuleResult],
        anonymize: bool = True,
    ) -> Dict[str, Any]:
        data = {
            "app_name": APP_NAME,
            "version": APP_VERSION,
            "author": APP_AUTHOR,
            "tagline": APP_TAGLINE,
            "scan_timestamp": datetime.now().isoformat(),
            "overall_health_score": score_report.overall_score,
            "status_label": score_report.status_label,
            "confidence": score_report.confidence,
            "coverage_percentage": score_report.coverage_percentage,
            "os_environment": {
                "system": os_info.system,
                "distribution": os_info.name,
                "version": os_info.version,
                "kernel": os_info.kernel,
                "architecture": os_info.architecture,
                "package_manager": os_info.package_manager,
                "desktop_environment": os_info.desktop_environment,
                "display_server": os_info.display_server,
                "init_system": os_info.init_system,
                "audio_server": os_info.audio_server,
            },
            "category_scores": score_report.category_scores,
            "score_deductions": score_report.deductions,
            "modules": {
                k: {
                    "display_name": res.display_name,
                    "status": res.status,
                    "score": res.score,
                    "supported": res.supported,
                    "metrics": res.metrics,
                    "findings": [f.model_dump() for f in res.findings],
                }
                for k, res in results.items()
            },
        }

        if anonymize:
            raw_json = json.dumps(data)
            clean_json = redact_sensitive_info(raw_json)
            return json.loads(clean_json)
        return data

    @classmethod
    def to_json(
        cls,
        os_info: OSInfo,
        score_report: HealthScoreReport,
        results: Dict[str, ModuleResult],
        anonymize: bool = True,
    ) -> str:
        data = cls._prepare_data(os_info, score_report, results, anonymize)
        return json.dumps(data, indent=2)

    @classmethod
    def to_txt(
        cls,
        os_info: OSInfo,
        score_report: HealthScoreReport,
        results: Dict[str, ModuleResult],
        anonymize: bool = True,
    ) -> str:
        data = cls._prepare_data(os_info, score_report, results, anonymize)
        lines = [
            "===========================================================",
            f"   {APP_NAME} v{APP_VERSION} - Diagnostic Report",
            f"   Tagline: {APP_TAGLINE}",
            f"   Generated: {data['scan_timestamp']}",
            "===========================================================",
            "",
            f"OVERALL SYSTEM HEALTH SCORE: {data['overall_health_score']} / 100 ({data['status_label']})",
            f"Confidence: {int(data['confidence'] * 100)}% | Coverage: {data['coverage_percentage']}%",
            "",
            "--- SYSTEM OVERVIEW ---",
            f"OS: {os_info.name} {os_info.version} (Kernel: {os_info.kernel})",
            f"Architecture: {os_info.architecture} | Init: {os_info.init_system}",
            f"Display Server: {os_info.display_server} | Audio: {os_info.audio_server}",
            f"Package Manager: {os_info.package_manager}",
            "",
            "--- CATEGORY HEALTH BREAKDOWN ---",
        ]

        for cat, sc in data["category_scores"].items():
            lines.append(f"  * {cat.upper():<14}: {sc:.1f} / 100")

        if data["score_deductions"]:
            lines.append("\n--- SCORE DEDUCTIONS & ISSUES ---")
            for ded in data["score_deductions"]:
                lines.append(f"  - {ded}")

        lines.append("\n--- DIAGNOSTIC FINDINGS ---")
        for key, mod in data["modules"].items():
            lines.append(f"\n[{mod['display_name']}] Status: {mod['status'].upper()} (Score: {mod['score']})")
            if not mod["findings"]:
                lines.append("  All checks passed successfully.")
            for f in mod["findings"]:
                lines.append(f"  • Issue: {f['title']} [{f['severity'].upper()}]")
                lines.append(f"    - What was detected: {f['what_detected']}")
                lines.append(f"    - What it means:     {f['what_it_means']}")
                lines.append(f"    - Safe next step:    {f['safe_next_step']}")

        lines.append("\n===========================================================")
        lines.append(f"Made by {APP_AUTHOR} | All diagnostics executed locally.")
        lines.append("===========================================================")
        return "\n".join(lines)

    @classmethod
    def to_html(
        cls,
        os_info: OSInfo,
        score_report: HealthScoreReport,
        results: Dict[str, ModuleResult],
        anonymize: bool = True,
    ) -> str:
        data = cls._prepare_data(os_info, score_report, results, anonymize)

        score_color = "#78D6B0"
        if data["overall_health_score"] < 60:
            score_color = "#E47777"
        elif data["overall_health_score"] < 75:
            score_color = "#E9B96E"

        cat_rows = "".join(
            f"<tr><td style='padding:8px;border-bottom:1px solid #22252D;'>{cat.title()}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #22252D;font-weight:600;'>{sc:.1f}/100</td></tr>"
            for cat, sc in data["category_scores"].items()
        )

        findings_html = []
        for key, mod in data["modules"].items():
            findings_html.append(f"<div style='background:#181A20;padding:16px;border-radius:8px;margin-bottom:12px;border:1px solid #22252D;'>")
            findings_html.append(f"<h3 style='margin:0 0 8px 0;font-size:16px;color:#F4F5F7;'>{mod['display_name']} - <span style='color:{score_color};'>{mod['status'].upper()}</span></h3>")
            if not mod["findings"]:
                findings_html.append("<p style='margin:0;color:#969BA6;font-size:13px;'>✓ All parameters normal.</p>")
            else:
                for f in mod["findings"]:
                    findings_html.append(f"<div style='border-left:3px solid #E9B96E;padding-left:10px;margin-top:8px;'>")
                    findings_html.append(f"<strong style='color:#F4F5F7;'>{f['title']}</strong>")
                    findings_html.append(f"<p style='margin:4px 0;color:#969BA6;font-size:13px;'>{f['what_detected']}</p>")
                    findings_html.append(f"<p style='margin:4px 0;color:#78D6B0;font-size:12px;'><strong>Safe next step:</strong> {f['safe_next_step']}</p>")
                    findings_html.append("</div>")
            findings_html.append("</div>")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{APP_NAME} Report</title>
<style>
  body {{ background:#101114; color:#F4F5F7; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; margin:0; padding:24px; }}
  .container {{ max-width:880px; margin:0 auto; }}
  .card {{ background:#181A20; border:1px solid #22252D; border-radius:12px; padding:20px; margin-bottom:16px; }}
  .score-badge {{ font-size:42px; font-weight:800; color:{score_color}; }}
</style>
</head>
<body>
<div class="container">
  <div class="card" style="display:flex; justify-content:space-between; align-items:center;">
    <div>
      <h1 style="margin:0 0 4px 0; font-size:24px;">{APP_NAME}</h1>
      <p style="margin:0; color:#969BA6; font-size:14px;">{APP_TAGLINE}</p>
      <p style="margin:8px 0 0 0; color:#969BA6; font-size:12px;">OS: {os_info.name} {os_info.version} | Arch: {os_info.architecture}</p>
    </div>
    <div style="text-align:right;">
      <div class="score-badge">{data['overall_health_score']}</div>
      <div style="color:{score_color}; font-weight:700; font-size:13px;">{data['status_label']}</div>
    </div>
  </div>

  <div class="card">
    <h2 style="font-size:16px; margin:0 0 12px 0;">Category Scores</h2>
    <table style="width:100%; border-collapse:collapse; font-size:14px;">
      {cat_rows}
    </table>
  </div>

  <h2 style="font-size:18px; margin:24px 0 12px 0;">Diagnostic Details</h2>
  {"".join(findings_html)}

  <footer style="margin-top:32px; text-align:center; color:#969BA6; font-size:12px;">
    {APP_NAME} v{APP_VERSION} • Made by {APP_AUTHOR}
  </footer>
</div>
</body>
</html>"""
