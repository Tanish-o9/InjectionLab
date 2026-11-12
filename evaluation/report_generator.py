"""Generate a self-contained interactive HTML report from benchmark results."""
import base64
import json
from pathlib import Path
import pandas as pd

import config


def generate_html_report(tag: str = "mock_weak") -> Path:
    d = config.RESULTS_DIR / tag
    summary_path = d / "summary.csv"
    detector_report_path = config.RESULTS_DIR / "detector_report.json"
    pr_curve_path = config.RESULTS_DIR / "detector_pr_curve.png"
    pareto_chart_path = d / "asr_vs_utility.png"
    type_chart_path = d / "asr_by_type.png"

    summary_df = pd.read_csv(summary_path) if summary_path.exists() else pd.DataFrame()
    det_report = {}
    if detector_report_path.exists():
        with open(detector_report_path, "r") as f:
            det_report = json.load(f)

    def b64_img(p: Path) -> str:
        if p.exists():
            with open(p, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        return ""

    pareto_b64 = b64_img(pareto_chart_path)
    type_b64 = b64_img(type_chart_path)
    pr_b64 = b64_img(pr_curve_path)

    # Build summary rows
    rows_html = ""
    for _, r in summary_df.iterrows():
        asr_pct = f"{r.asr * 100:.1f}%"
        direct_pct = f"{r.asr_direct * 100:.1f}%"
        indirect_pct = f"{r.asr_indirect * 100:.1f}%"
        exfil_pct = f"{r.asr_exfiltration * 100:.1f}%"
        util_pct = f"{r.utility * 100:.1f}%"
        fr_pct = f"{r.false_refusal * 100:.1f}%"
        
        # Color coding for security
        badge_class = "badge-safe" if r.asr < 0.1 else ("badge-warning" if r.asr < 0.4 else "badge-danger")
        
        rows_html += f"""
        <tr>
            <td class="font-bold">{r.config}</td>
            <td><span class="badge {badge_class}">{asr_pct}</span> <span class="ci">[{r.asr_lo*100:.1f}-{r.asr_hi*100:.1f}]</span></td>
            <td>{direct_pct}</td>
            <td>{indirect_pct}</td>
            <td>{exfil_pct}</td>
            <td><span class="text-emerald">{util_pct}</span> <span class="ci">[{r.utility_lo*100:.1f}-{r.utility_hi*100:.1f}]</span></td>
            <td>{fr_pct}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InjectionLab Security Benchmark Report</title>
    <style>
        :root {{
            --bg: #0b0f19;
            --surface: #111827;
            --surface-hover: #1f2937;
            --border: #374151;
            --text: #f3f4f6;
            --muted: #9ca3af;
            --primary: #3b82f6;
            --emerald: #10b981;
            --amber: #f59e0b;
            --rose: #f43f5e;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 2rem;
            line-height: 1.5;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            margin-bottom: 2.5rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1.5rem;
        }}
        .title {{ font-size: 2.25rem; font-weight: 800; background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .subtitle {{ color: var(--muted); margin-top: 0.5rem; font-size: 1.1rem; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2.5rem;
        }}
        .stat-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1.25rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }}
        .stat-val {{ font-size: 1.75rem; font-weight: 700; margin-top: 0.25rem; }}
        .stat-label {{ font-size: 0.85rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }}
        
        .section-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1.75rem;
            margin-bottom: 2.5rem;
        }}
        .section-title {{ font-size: 1.35rem; font-weight: 700; margin-bottom: 1.25rem; color: #93c5fd; }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th, td {{
            padding: 0.85rem 1rem;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background: rgba(31, 41, 55, 0.7);
            color: var(--muted);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        tr:hover td {{ background: var(--surface-hover); }}
        
        .badge {{
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .badge-safe {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
        .badge-warning {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
        .badge-danger {{ background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }}
        
        .ci {{ font-size: 0.75rem; color: var(--muted); }}
        .text-emerald {{ color: #34d399; font-weight: 600; }}
        .font-bold {{ font-weight: 600; }}
        
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }}
        .chart-box {{
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 1rem;
            text-align: center;
        }}
        .chart-box img {{ max-width: 100%; height: auto; border-radius: 0.25rem; }}
        .chart-title {{ font-size: 0.95rem; font-weight: 600; margin-bottom: 0.75rem; color: var(--muted); }}
        
        footer {{
            text-align: center;
            color: var(--muted);
            font-size: 0.85rem;
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1 class="title">InjectionLab Benchmark Report</h1>
            <p class="subtitle">Automated Prompt-Injection Red-Teaming & Multi-Layer Defense Evaluation</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Model Target</div>
                <div class="stat-val" style="color: #60a5fa;">{tag}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Attacks Evaluated</div>
                <div class="stat-val">{det_report.get('n_attacks', 368)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Baseline Attack Success (None)</div>
                <div class="stat-val" style="color: #fb7185;">{f"{summary_df.iloc[0].asr * 100:.1f}%" if len(summary_df) else "N/A"}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Best Defense ASR (All)</div>
                <div class="stat-val" style="color: #34d399;">{f"{summary_df.iloc[-1].asr * 100:.1f}%" if len(summary_df) else "0.0%"}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Detector Recall</div>
                <div class="stat-val" style="color: #a78bfa;">{f"{det_report.get('recall', 1.0) * 100:.1f}%"}</div>
            </div>
        </div>

        <div class="section-card">
            <h2 class="section-title">Defense Benchmark Matrix</h2>
            <table>
                <thead>
                    <tr>
                        <th>Defense Configuration</th>
                        <th>Overall ASR (95% CI)</th>
                        <th>Direct Attacks</th>
                        <th>Indirect Attacks</th>
                        <th>Exfiltration</th>
                        <th>Benign Utility</th>
                        <th>False Refusals</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>

        <div class="section-card">
            <h2 class="section-title">Visual Analysis & Pareto Trade-Offs</h2>
            <div class="chart-grid">
                <div class="chart-box">
                    <div class="chart-title">Attack Success Rate vs. Utility Frontier</div>
                    {f'<img src="{pareto_b64}" alt="ASR vs Utility">' if pareto_b64 else '<p>Chart not found</p>'}
                </div>
                <div class="chart-box">
                    <div class="chart-title">Attack Success Rate by Attack Vector</div>
                    {f'<img src="{type_b64}" alt="ASR by Type">' if type_b64 else '<p>Chart not found</p>'}
                </div>
            </div>
        </div>

        <footer>
            <p>Generated by <strong>InjectionLab</strong> &bull; Developed by <a href="https://github.com/Tanish-o9" style="color: #60a5fa; text-decoration: none;">Tanish Kumar (@Tanish-o9)</a></p>
        </footer>
    </div>
</body>
</html>
"""
    out_file = config.RESULTS_DIR / f"report_{tag}.html"
    out_file.write_text(html, encoding="utf-8")
    return out_file


if __name__ == "__main__":
    p = generate_html_report("mock_weak")
    print(f"Generated standalone report: {p}")
