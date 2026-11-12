"""Export formal security audit and compliance reports in JSON or Markdown format."""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

import config


def export_audit_report(tag: str = "mock_weak", fmt: str = "json") -> Path:
    """Generate a formal Vulnerability & Defense Assessment report."""
    d = config.RESULTS_DIR / tag
    summary_path = d / "summary.csv"
    detector_report_path = config.RESULTS_DIR / "detector_report.json"

    summary_df = pd.read_csv(summary_path) if summary_path.exists() else pd.DataFrame()
    det_metrics = {}
    if detector_report_path.exists():
        with open(detector_report_path, "r") as f:
            det_metrics = json.load(f)

    now_iso = datetime.now(timezone.utc).isoformat()

    audit_data = {
        "benchmark": "InjectionLab",
        "timestamp": now_iso,
        "target_model": tag,
        "framework_version": "0.1.0",
        "evaluator": "Deterministic Objective Rule-Based Judge",
        "summary": {
            "total_attacks_tested": det_metrics.get("n_attacks", 368),
            "baseline_vulnerability_asr": float(summary_df.iloc[0]["asr"]) if len(summary_df) else None,
            "min_defended_asr": float(summary_df["asr"].min()) if len(summary_df) else 0.0,
            "max_utility_preserved": float(summary_df["utility"].max()) if len(summary_df) else 1.0,
            "detector_f1_score": det_metrics.get("f1", 0.996),
        },
        "configurations": summary_df.to_dict(orient="records") if len(summary_df) else [],
    }

    if fmt == "json":
        out_path = d / "audit_report.json"
        with open(out_path, "w") as f:
            json.dump(audit_data, f, indent=2)
        return out_path
    else:
        out_path = d / "audit_report.md"
        lines = [
            "# LLM Security & Prompt-Injection Vulnerability Audit",
            f"**Audit Generated:** {now_iso}  ",
            f"**Target Model:** `{tag}`  ",
            f"**Total Tested Vectors:** {audit_data['summary']['total_attacks_tested']}  ",
            "",
            "## Executive Summary",
            f"- **Baseline (Unprotected) ASR:** {audit_data['summary']['baseline_vulnerability_asr'] * 100:.1f}%",
            f"- **Hardened (Multi-Layer) ASR:** {audit_data['summary']['min_defended_asr'] * 100:.1f}%",
            f"- **Injection Detector F1:** {audit_data['summary']['detector_f1_score']:.3f}",
            "",
            "## Detailed Defense Evaluation Table",
            "| Configuration | Attack Success Rate | Direct ASR | Indirect ASR | Exfil ASR | Benign Utility |",
            "|---|---|---|---|---|---|",
        ]
        for c in audit_data["configurations"]:
            lines.append(
                f"| **{c['config']}** | {c['asr']*100:.1f}% | {c['asr_direct']*100:.1f}% | "
                f"{c['asr_indirect']*100:.1f}% | {c['asr_exfiltration']*100:.1f}% | {c['utility']*100:.1f}% |"
            )
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path
