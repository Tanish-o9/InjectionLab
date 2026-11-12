"""Simulated tools. Nothing real happens: every call is only logged."""
import json
import re


class ToolBox:
    def __init__(self):
        self.log = []

    def send_email(self, to, body):
        self.log.append({"tool": "send_email", "to": to, "body": body})
        return "email queued (simulated)"

    def call(self, name, args):
        if name == "send_email":
            return self.send_email(str(args.get("to", "")), str(args.get("body", "")))
        return "unknown tool"


def parse_tool_calls(text):
    """Return (calls, text_without_tool_lines)."""
    calls, rest = [], []
    for line in text.splitlines():
        m = re.match(r"\s*TOOL_CALL:\s*(\{.*\})\s*$", line)
        if m:
            try:
                calls.append(json.loads(m.group(1)))
                continue
            except json.JSONDecodeError:
                pass
        rest.append(line)
    return calls, "\n".join(rest).strip()
