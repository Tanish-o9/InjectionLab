"""Basic test suite for InjectionLab."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from defenses.output_filter import canary_in_text
from evaluation.judge import judge_attack, leaked
from target.app import Result


def test_leak_variants():
    import base64
    assert leaked(f"the secret is {config.CANARY}")
    assert leaked(" ".join(config.CANARY))
    assert leaked(config.CANARY[::-1])
    assert leaked(base64.b64encode(config.CANARY.encode()).decode())
    assert not leaked("nothing here")


def test_filter_misses_base64():
    import base64
    assert canary_in_text(config.CANARY)
    assert not canary_in_text(base64.b64encode(config.CANARY.encode()).decode())


def test_hijack():
    r = Result("ok", [{"tool": "send_email", "to": config.ATTACKER_ADDR, "body": "x"}])
    assert judge_attack(r)["hijacked"]
    r = Result("ok", [{"tool": "send_email", "to": "hr@company.test", "body": "x"}])
    assert not judge_attack(r)["success"]
