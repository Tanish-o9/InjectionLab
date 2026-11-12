"""Make charts from results/<model>/summary.csv. Usage: python plot_results.py mock_weak"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config

PAL = {"direct": "#0072B2", "indirect": "#E69F00", "exfiltration": "#009E73"}  # Okabe-Ito (CVD-safe)
INK, MUTED = "#222222", "#666666"


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(colors=MUTED)


def main(tag):
    d = config.RESULTS_DIR / tag
    s = pd.read_csv(d / "summary.csv")

    # 1) ASR by attack type, per defense config
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
    w, x = 0.26, range(len(s))
    for k, t in enumerate(PAL):
        m, lo, hi = s[f"asr_{t}"] * 100, s[f"asr_{t}_lo"] * 100, s[f"asr_{t}_hi"] * 100
        ax.bar([i + (k - 1) * w for i in x], m, w * 0.92, color=PAL[t], label=t,
               yerr=[m - lo, hi - m], ecolor=INK, capsize=2, error_kw={"lw": 1})
    ax.set_xticks(list(x), s.config, rotation=20)
    ax.set(ylabel="Attack success rate (%)", ylim=(0, 105), title=f"ASR by attack type ({tag}, 95% CI)")
    ax.legend(frameon=False, ncol=3)
    style(ax)
    fig.tight_layout()
    fig.savefig(d / "asr_by_type.png")

    # 2) ASR vs utility trade-off
    fig, ax = plt.subplots(figsize=(6.5, 5), dpi=150)
    ax.errorbar(s.utility * 100, s.asr * 100,
                xerr=[(s.utility - s.utility_lo) * 100, (s.utility_hi - s.utility) * 100],
                yerr=[(s.asr - s.asr_lo) * 100, (s.asr_hi - s.asr) * 100],
                fmt="o", color="#0072B2", ecolor="#9bb7cc", capsize=2, ms=7)
    for _, r in s.iterrows():
        ax.annotate(r.config, (r.utility * 100, r.asr * 100), textcoords="offset points",
                    xytext=(6, 6), fontsize=8, color=INK)
    ax.set(xlabel="Utility on benign tasks (%)  (higher is better)",
           ylabel="Attack success rate (%)  (lower is better)",
           title=f"Security vs usefulness ({tag})")
    ax.invert_yaxis()
    style(ax)
    fig.tight_layout()
    fig.savefig(d / "asr_vs_utility.png")
    print("saved charts in", d)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mock_weak")
