"""
Splits a footnote that may contain multiple citations into individual authority strings.

Handles:
  - Semicolon-separated lists (most common): "Smith, 384 U.S. 436 (1966); Jones, 347 U.S. 483 (1954)"
  - Compare/with constructions (Bluebook Rule 1.2): "Compare X, with Y" → [X, Y]
  - Introductory signals (Rule 1.2) stripped from each authority
  - [Hereinafter ...] clauses stripped (Rule 4.2(b))
  - Id. and supra citations preserved as valid authorities (Rules 4.1, 4.2)
"""

import re

# Introductory signals — Rule 1.2
# These introduce an authority but are not part of the citation itself.
_SIGNALS = re.compile(
    r"^(?:"
    r"See\s+also"
    r"|See\s+generally"
    r"|See"
    r"|But\s+see"
    r"|But\s+cf\."
    r"|Cf\."
    r"|E\.g\.,?"
    r"|Accord"
    r"|Contra"
    r"|Also\s+see"
    r")\s+",
    re.IGNORECASE,
)

# [Hereinafter Short Name] — Rule 4.2(b)
_HEREINAFTER = re.compile(r"\s*\[hereinafter\s+[^\]]+\]", re.IGNORECASE)


def split_authorities(footnote: str) -> list[str]:
    """
    Return a list of individual citation strings from a footnote.

    1. Strip [hereinafter ...] annotations.
    2. If the text starts with "Compare", split on the first ", with " at depth 0.
    3. Otherwise split on ';' at depth 0.
    4. Strip introductory signals from each part.
    """
    text = _HEREINAFTER.sub("", footnote).strip()

    # Compare X, with Y (Rule 1.2) — must be handled before semicolon splitting
    # because the "with" clause may itself contain semicolons.
    if re.match(r"^compare\s+", text, re.IGNORECASE):
        parts = _split_compare(text)
    else:
        parts = _split_on_semicolons(text)

    result = []
    for part in parts:
        cleaned = _SIGNALS.sub("", part).strip().rstrip(".")
        if cleaned:
            result.append(cleaned)

    return result if result else [footnote.strip()]


def _split_compare(text: str) -> list[str]:
    """
    Split a 'Compare A, with B' construction into [A, B].
    Both A and B may themselves be semicolon-separated lists; we handle that
    recursively so Compare X; Y, with Z; W → [X, Y, Z, W].
    """
    # Drop the leading "Compare " signal
    rest = re.sub(r"^compare\s+", "", text, flags=re.IGNORECASE)

    # Find ", with " at parenthesis depth 0
    depth = 0
    with_pos = None
    i = 0
    while i < len(rest):
        ch = rest[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0 and rest[i:].lower().startswith(", with "):
            with_pos = i
            break
        i += 1

    if with_pos is None:
        # No "with" found — fall back to semicolon splitting
        return _split_on_semicolons(rest)

    before = rest[:with_pos].strip()
    after  = rest[with_pos + len(", with "):].strip()

    # Each side may itself be a semicolon list
    return _split_on_semicolons(before) + _split_on_semicolons(after)


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
