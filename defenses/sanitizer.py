"""Unicode and homoglyph sanitizer defense against character-level injection evasion."""
import unicodedata
import re

# Common invisible and zero-width characters used for evasion
INVISIBLE_CHARS = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u202a\u202b\u202c\u202d\u202e\u2060\u00ad]"
)

# Common Cyrillic and Greek homoglyphs mapped to ASCII equivalents
HOMOGLYPH_MAP = {
    "а": "a", "А": "A",
    "с": "c", "С": "C",
    "е": "e", "Е": "E",
    "о": "o", "О": "O",
    "р": "p", "Р": "P",
    "х": "x", "Х": "X",
    "у": "y", "У": "Y",
    "і": "i", "І": "I",
    "ј": "j", "Ј": "J",
    "ѕ": "s", "Ѕ": "S",
    "ԁ": "d", "Ԃ": "D",
    "ԛ": "q", "Ԛ": "Q",
    "ԝ": "w", "Ԝ": "W",
    # Greek
    "α": "a", "Α": "A",
    "ο": "o", "Ο": "O",
    "ρ": "p", "Ρ": "P",
    "τ": "t", "Τ": "T",
}


def sanitize_text(text: str) -> str:
    """Strip zero-width characters, normalize Unicode (NFKC), and replace homoglyphs."""
    if not text:
        return ""
    # 1. Normalize compatibility characters
    text = unicodedata.normalize("NFKC", text)
    # 2. Strip invisible formatting and zero-width characters
    text = INVISIBLE_CHARS.sub("", text)
    # 3. Replace known homoglyphs
    for char, replacement in HOMOGLYPH_MAP.items():
        if char in text:
            text = text.replace(char, replacement)
    return text
