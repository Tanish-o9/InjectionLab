"""Build attacks/attacks.jsonl = templates x mutations x channels (x carrier docs).
Usage: python -m attacks.build_attacks [--llm-mutate ollama:qwen2.5:3b-instruct]
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from attacks.mutate import MUTATIONS, mutate_llm, mutate_rule  # noqa: E402
from attacks.templates import TEMPLATES  # noqa: E402
from benign.tasks import BENIGN_TASKS  # noqa: E402

DOC_REPS = 2  # different carrier documents per doc-channel attack


def build(llm_spec=None, seed=config.SEED):
    rng = random.Random(seed)
    carriers = [t for t in BENIGN_TASKS if not t["tool"]]
    attacks, n = [], 0

    def add(a_type, channel, tpl_id, mut, payload):
        nonlocal n
        c = rng.choice(carriers)
        n += 1
        attacks.append({
            "id": f"a{n:04d}", "type": a_type, "channel": channel, "template": tpl_id,
            "mutation": mut, "payload": payload, "carrier_doc": c["doc"],
            "query": payload if channel == "user" else c["query"],
        })

    for ti, (a_type, channels, text) in enumerate(TEMPLATES):
        text = text.format(addr=config.ATTACKER_ADDR)
        for mut in MUTATIONS:
            payload = mutate_rule(text, mut)
            for ch in channels:
                for _ in range(DOC_REPS if ch == "doc" else 1):
                    add(a_type, ch, ti, mut, payload)
    if llm_spec:
        from llm import get_llm
        llm = get_llm(llm_spec)
        for ti, (a_type, channels, text) in enumerate(TEMPLATES):
            for v in mutate_llm(llm, text.format(addr=config.ATTACKER_ADDR)):
                for ch in channels:
                    add(a_type, ch, ti, "llm", v)
    config.ATTACKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(config.ATTACKS_FILE, "w") as f:
        for a in attacks:
            f.write(json.dumps(a) + "\n")
    return attacks


def load_attacks():
    if not config.ATTACKS_FILE.exists():
        build()
    return [json.loads(l) for l in open(config.ATTACKS_FILE)]


if __name__ == "__main__":
    spec = sys.argv[sys.argv.index("--llm-mutate") + 1] if "--llm-mutate" in sys.argv else None
    a = build(spec)
    from collections import Counter
    print(f"wrote {len(a)} attacks ->", config.ATTACKS_FILE, dict(Counter(x["type"] for x in a)))
