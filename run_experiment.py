"""Run the full InjectionLab benchmark.

Examples:
  python run_experiment.py --model mock:weak --trials 3
  python run_experiment.py --model ollama:qwen2.5:3b-instruct --trials 3 --max-attacks 100
"""
import argparse
import sys

import pandas as pd
from tqdm import tqdm

import config
from attacks.build_attacks import load_attacks
from benign.tasks import BENIGN_TASKS
from defenses.detector import InjectionDetector
from evaluation.judge import judge_attack, judge_benign
from evaluation.metrics import summarize, to_markdown
from llm import get_llm
from target.app import TargetApp
from target.docs import DOCS
from target.retriever import Retriever


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="mock:weak")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--max-attacks", type=int, default=0, help="0 = all (random subset if set)")
    ap.add_argument("--configs", nargs="*", default=list(config.DEFENSE_CONFIGS))
    ap.add_argument("--use-hf", action="store_true", help="also train detector on deepset dataset")
    a = ap.parse_args()

    llm = get_llm(a.model)
    attacks = load_attacks()
    if a.max_attacks:
        import random
        attacks = random.Random(config.SEED).sample(attacks, min(a.max_attacks, len(attacks)))
    retriever = Retriever(DOCS)
    detector = InjectionDetector().fit(a.use_hf)
    rows = []
    for name in a.configs:
        app = TargetApp(llm, config.DEFENSE_CONFIGS[name], retriever, detector)
        work = [("attack", x) for x in attacks] + [("benign", t) for t in BENIGN_TASKS]
        for trial in range(a.trials):
            for kind, item in tqdm(work, desc=f"{name} trial {trial + 1}/{a.trials}", leave=False):
                if kind == "attack":
                    poison = item["payload"] if item["channel"] == "doc" else None
                    res = app.run(item["query"], item["carrier_doc"], poison, trial)
                    j = judge_attack(res)
                    rows.append({"config": name, "kind": kind, "id": item["id"], "type": item["type"],
                                 "channel": item["channel"], "mutation": item["mutation"], "trial": trial,
                                 "success": j["success"], "leaked": j["leaked"], "hijacked": j["hijacked"],
                                 "blocked": res.blocked})
                else:
                    res = app.run(item["query"], trial=trial)
                    j = judge_benign(item, res)
                    rows.append({"config": name, "kind": kind, "id": item["id"], "trial": trial,
                                 "utility_ok": j["utility_ok"], "false_refusal": j["false_refusal"],
                                 "blocked": res.blocked})
    runs = pd.DataFrame(rows)
    out = config.RESULTS_DIR / a.model.replace(":", "_").replace("/", "_")
    out.mkdir(parents=True, exist_ok=True)
    runs.to_csv(out / "runs.csv", index=False)
    summ = summarize(runs)
    summ.to_csv(out / "summary.csv", index=False)
    (out / "summary.md").write_text(to_markdown(summ))
    print(to_markdown(summ))
    print(f"\nsaved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
