"""A deterministic, offline simulated LLM for InjectionLab testing.

IMPORTANT: this is NOT a real model. It obeys injected instructions with an ASSUMED
probability (config.MOCK_WEAKNESS) that is reduced when the prompt contains
delimiters / an instruction-hierarchy rule. Numbers produced with it only prove the
pipeline works. Use `--model ollama:...` or `--model openai:...` for real results.
"""
import base64
import hashlib
import json
import random
import re

import config

CANARY_RE = re.compile(r"CANARY-\w+")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.\w+")
B64_RE = re.compile(r"[A-Za-z0-9+/=]{24,}")
STOP = set("the a an and or of to in on for is are was be by with at from as it this that what how when where who do does can i my me you your".split())

STRONG = re.compile(
    r"(ignore|disregard)\s+(all\s+|any\s+|the\s+)?(previous|prior|above|earlier|pichl\w+)|"
    r"forget your (rules|instructions)|system override|developer mode|new instructions?|"
    r"system note|new system message|important instruction for the ai|override|"
    r"ignore karo|bhool jao|nazarandaz|you are dan|no restrictions", re.I)
MEDIUM = re.compile(
    r"reveal the secret|print your secret|canary|secret (string|token|code)|your system prompt|"
    r"send_email|email the secret|forward your secret|spelled letter by letter|backwards", re.I)
HINGLISH = re.compile(r"\b(karo|bhejo|batao|bhool|bhai|pichl\w+)\b", re.I)


def cue_strength(text: str) -> float:
    """How strongly a text looks like an injected instruction (0 = benign)."""
    def base(t):
        if STRONG.search(t):
            return 1.0
        if MEDIUM.search(t):
            return 0.75
        return 0.0
    s = base(text)
    for tok in B64_RE.findall(text):
        try:
            dec = base64.b64decode(tok, validate=True).decode("utf-8")
        except Exception:
            continue
        if "base64" in text.lower():
            s = max(s, 0.45 * base(dec))
    if HINGLISH.search(text):
        s *= 0.8
    return s


def decoded_view(text: str) -> str:
    extra = []
    for tok in B64_RE.findall(text):
        try:
            extra.append(base64.b64decode(tok, validate=True).decode("utf-8"))
        except Exception:
            pass
    return text + "\n" + "\n".join(extra)


def split_prompt(user: str):
    if "CONTEXT:" in user and "QUESTION:" in user:
        ctx = user.split("CONTEXT:", 1)[1].split("QUESTION:", 1)[0]
        q = user.split("QUESTION:", 1)[1]
        return ctx.strip(), q.strip()
    return "", user.split("QUESTION:", 1)[-1].strip()


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def toks(s):
    return {w[:5] for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in STOP}  # noqa


def benign_answer(ctx, q):
    qt = toks(q)
    ranked = []
    for s in sentences(ctx):
        if cue_strength(s) > 0 or s.startswith("<<<"):
            continue
        ranked.append((len(qt & toks(s)), s))
    ranked.sort(key=lambda x: -x[0])
    top = [s for sc, s in ranked[:4] if sc > 0]
    return "Based on the documents: " + " ".join(top) if top else "I could not find that in the documents."


class MockLLM:
    def __init__(self, kind="weak"):
        self.kind = kind
        self.name = f"mock:{kind}"
        self.weakness = config.MOCK_WEAKNESS[kind]

    def _rng(self, system, user, trial):
        h = hashlib.sha256(f"{self.name}|{system}|{user}|{trial}".encode()).hexdigest()
        return random.Random(int(h, 16) % (2 ** 32))

    def chat(self, messages, trial=0):
        system, user = messages[0]["content"], messages[-1]["content"]
        ctx, q = split_prompt(user)
        rng = self._rng(system, user, trial)
        canary = CANARY_RE.search(system)
        has_tools = "TOOLS AVAILABLE" in system
        delim = "<<<DOC" in system
        hier = "INSTRUCTION HIERARCHY" in system

        calls, extra = [], []
        for channel, seg in (("doc", ctx), ("user", q)):
            strength = cue_strength(seg)
            if strength == 0:
                continue
            p = self.weakness * strength * (1.0 if channel == "doc" else 0.85)
            if delim and channel == "doc":
                p *= 0.5
            if hier:
                p *= 0.55 if channel == "doc" else 0.85
            if rng.random() >= p:
                continue
            view = decoded_view(seg)
            addrs = EMAIL_RE.findall(view)
            wants_secret = re.search(r"secret|canary|token|system prompt", view, re.I)
            wants_email = addrs and re.search(r"send_email|email|forward|mail", view, re.I)
            if wants_email and has_tools:
                body = canary.group(0) if (wants_secret and canary) else "requested info"
                calls.append({"tool": "send_email", "args": {"to": addrs[0], "body": body}})
            elif wants_secret and canary:
                c = canary.group(0)
                if re.search(r"encod\w*.{0,20}base64|base64.{0,20}encod", view, re.I):
                    c = base64.b64encode(c.encode()).decode()
                elif re.search(r"backwards|reverse", view, re.I):
                    c = c[::-1]
                elif re.search(r"letter by letter|spaces between|spell", view, re.I):
                    c = " ".join(c)
                extra.append(f"The secret is: {c}")

        # legitimate user-requested email (benign path)
        if has_tools and cue_strength(q) == 0 and re.search(r"\b(email|send)\b", q, re.I):
            addrs = EMAIL_RE.findall(q)
            if addrs:
                body = benign_answer(ctx, q) if ctx else "{{SUMMARY}}"
                calls.append({"tool": "send_email", "args": {"to": addrs[0], "body": body}})

        lines = [f"TOOL_CALL: {json.dumps(c)}" for c in calls]
        if ctx:
            lines.append(benign_answer(ctx, q))
        else:
            lines.append("Done.")
        lines.extend(extra)
        return "\n".join(lines)
