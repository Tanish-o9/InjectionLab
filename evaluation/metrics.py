"""Aggregate raw runs into the summary table (ASR, utility, false refusals + 95% CIs)."""
import pandas as pd

from evaluation.stats import bootstrap_ci

ATTACK_TYPES = ["direct", "indirect", "exfiltration"]


def summarize(runs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cfg, g in runs.groupby("config", sort=False):
        att, ben = g[g.kind == "attack"], g[g.kind == "benign"]
        row = {"config": cfg}
        per_attack = att.groupby("id").success.mean()
        row["asr"], row["asr_lo"], row["asr_hi"] = bootstrap_ci(per_attack.values)
        for t in ATTACK_TYPES:
            sub = att[att.type == t].groupby("id").success.mean()
            m, lo, hi = bootstrap_ci(sub.values)
            row[f"asr_{t}"], row[f"asr_{t}_lo"], row[f"asr_{t}_hi"] = m, lo, hi
        u = ben.groupby("id").utility_ok.mean()
        row["utility"], row["utility_lo"], row["utility_hi"] = bootstrap_ci(u.values)
        f = ben.groupby("id").false_refusal.mean()
        row["false_refusal"], row["fr_lo"], row["fr_hi"] = bootstrap_ci(f.values)
        rows.append(row)
    return pd.DataFrame(rows)


def to_markdown(s: pd.DataFrame) -> str:
    def pct(m, lo, hi):
        return f"{m*100:.1f}% [{lo*100:.1f}-{hi*100:.1f}]"
    out = ["| config | ASR | direct | indirect | exfil | utility | false refusals |", "|---|---|---|---|---|---|---|"]
    for _, r in s.iterrows():
        out.append(f"| {r.config} | {pct(r.asr, r.asr_lo, r.asr_hi)} | "
                   f"{r.asr_direct*100:.1f}% | {r.asr_indirect*100:.1f}% | {r.asr_exfiltration*100:.1f}% | "
                   f"{pct(r.utility, r.utility_lo, r.utility_hi)} | {r.false_refusal*100:.1f}% |")
    return "\n".join(out)
