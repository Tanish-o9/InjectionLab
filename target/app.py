"""The target: a small RAG assistant that holds a secret and can call a fake email tool."""
import json
from dataclasses import dataclass, field

import config
from defenses.output_filter import canary_in_text
from defenses.sanitizer import sanitize_text
from target import prompts
from target.tools import ToolBox, parse_tool_calls


@dataclass
class Result:
    final_text: str
    executed_calls: list = field(default_factory=list)
    blocked: bool = False
    flags: list = field(default_factory=list)


class TargetApp:
    def __init__(self, llm, defenses, retriever, detector=None):
        self.llm, self.D, self.ret, self.det = llm, set(defenses), retriever, detector
        if "detector" in self.D and detector is None:
            raise ValueError("detector defense needs a detector instance")

    def run(self, query, carrier=None, poison=None, trial=0) -> Result:
        docs = self.ret.search(query, config.TOP_K)
        if poison is not None:  # simulate a poisoned document being retrieved
            if carrier in [i for i, _ in docs]:
                docs = [(i, t + "\n" + poison if i == carrier else t) for i, t in docs]
            else:
                docs = docs[:-1] + [(carrier, self.ret.docs[carrier] + "\n" + poison)]
        flags = []
        if "sanitizer" in self.D:
            query = sanitize_text(query)
            docs = [(i, sanitize_text(t)) for i, t in docs]
            flags.append("sanitizer")

        if "detector" in self.D:
            if self.det.is_injection(query):
                return Result("[blocked by detector]", [], True, ["detector:query"])
            kept = []
            for i, t in docs:
                if self.det.is_injection(t):
                    flags.append(f"detector:doc:{i}")
                else:
                    kept.append((i, t))
            docs = kept

        if "privsep" in self.D:
            quarantined = self.llm.chat(prompts.quarantined_messages(docs, query, self.D), trial)
            _, q_text = parse_tool_calls(quarantined)  # quarantined LLM cannot call tools
            priv = self.llm.chat(prompts.privileged_messages(query, self.D), trial)
            calls, _ = parse_tool_calls(priv)
            for c in calls:  # privileged side never reads q_text, it only forwards it
                args = c.get("args", {})
                args["body"] = str(args.get("body", "")).replace("{{SUMMARY}}", q_text)
            text = q_text
        else:
            raw = self.llm.chat(prompts.main_messages(docs, query, self.D), trial)
            calls, text = parse_tool_calls(raw)

        blocked = False
        if "output_filter" in self.D:
            leak = canary_in_text(text) or any(canary_in_text(json.dumps(c.get("args", {}))) for c in calls)
            if leak:
                text, calls, blocked = "[blocked by output filter]", [], True
                flags.append("output_filter")

        box = ToolBox()
        for c in calls:
            if isinstance(c, dict) and isinstance(c.get("args"), dict):
                box.call(c.get("tool"), c["args"])
        return Result(text, box.log, blocked, flags)
