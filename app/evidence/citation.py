import re

LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}


def normalize(text: str) -> str:
    for a, b in LIGATURES.items():
        text = text.replace(a, b)
    return re.sub(r"[^a-z0-9]", "", text.lower())


def quote_found(quote: str, source: str) -> bool:
    if not quote.strip():
        return False
    return normalize(quote) in normalize(source)
