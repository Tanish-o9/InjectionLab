"""Canary output filter. Deliberately simple: catches the plain and separator-stripped
canary only, so encodings (base64, reversed) can slip through. That is a real limitation."""
import re

import config


def canary_in_text(text: str) -> bool:
    low = text.lower()
    if config.CANARY.lower() in low:
        return True
    stripped = re.sub(r"[^a-z0-9]", "", low)
    return re.sub(r"[^a-z0-9]", "", config.CANARY.lower()) in stripped
