"""
Splits a footnote that may contain multiple citations into individual authority strings.
Handles parenthesis-aware splitting on semicolons and citation signals.
"""

import re

# Citation signals that introduce a new authority
_SIGNALS = re.compile(
    r"^(?:See\s+also|See\s+generally|See|But\s+see|Cf\.|E\.g\.,?\s*|"
    r"Compare|Accord|Contra|Also|And\s+see)\s+",
    re.IGNORECASE,
)


def split_authorities(footnote: str) -> list[str]:
    """
    Return a list of individual citation strings from a footnote.
    Splits on ';' that are not inside parentheses.
    Falls back to [footnote] if only one authority is found.
    """
    raw_parts = _split_on_semicolons(footnote)
    result = []
    for part in raw_parts:
        cleaned = _SIGNALS.sub("", part).strip().rstrip(".")
        if cleaned:
            result.append(cleaned)
    return result if result else [footnote.strip()]


def _split_on_semicolons(text: str) -> list[str]:
    """Split text on ';' while respecting parenthesis depth."""
    parts: list[str] = []
    depth   = 0
    current: list[str] = []

    for ch in text:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            current.append(ch)
        elif ch == ";" and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
        else:
            current.append(ch)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)

    return parts
