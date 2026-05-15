"""
Identifies and parses Bluebook citations from raw footnote text.
Handles cases, statutes, law review articles, and books.
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CitationType(str, Enum):
    CASE = "case"
    STATUTE = "statute"
    ARTICLE = "article"
    BOOK = "book"
    UNKNOWN = "unknown"


@dataclass
class ParsedCitation:
    raw: str
    citation_type: CitationType
    # Shared
    year: Optional[str] = None
    page: Optional[str] = None
    pincite: Optional[str] = None
    # Case-specific
    parties: Optional[str] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    court: Optional[str] = None
    # Statute-specific
    title: Optional[str] = None
    code: Optional[str] = None
    section: Optional[str] = None
    # Article-specific
    authors: Optional[str] = None
    article_title: Optional[str] = None
    journal: Optional[str] = None
    # Book-specific
    book_title: Optional[str] = None
    edition: Optional[str] = None
    # Extra fields for display
    search_query: Optional[str] = None
    errors: list = field(default_factory=list)


# ── Reporter abbreviations (U.S. courts, widely-cited) ──────────────────────
REPORTERS = [
    r"U\.S\.", r"S\.Ct\.", r"S\. Ct\.", r"L\.Ed\.", r"L\. Ed\.", r"L\.Ed\.2d",
    r"F\.\d*d?", r"F\.\s*(?:Supp|App)\.(?:\s*\d+d)?",
    r"[A-Z][a-z]*\.\s*(?:\d+[a-z]+\s+)?(?:L\.\s*Rev\.|J\.)",  # state reporters with L.Rev.
    r"[A-Z][a-z]+\.\s*\d*[a-z]*",  # generic state reporters
]
REPORTER_PAT = "|".join(REPORTERS)

# Federal code patterns
CODE_PAT = r"(?:U\.S\.C\.|C\.F\.R\.|U\.S\.C\.A\.|U\.S\.C\.S\.)"

# Common law journal abbreviations (enough to detect article citations)
JOURNAL_WORDS = (
    r"(?:L\.\s*Rev\.|Law\s+Rev(?:iew)?|L\.J\.|Law\s+Journal|J\.\s*Law|"
    r"Yale\s+L\.J\.|Harv\.\s*L\.\s*Rev\.|Stan\.\s*L\.\s*Rev\.|"
    r"Colum\.\s*L\.\s*Rev\.|Mich\.\s*L\.\s*Rev\.|Cornell\s+L\.\s*Rev\.|"
    r"N\.Y\.U\.\s*L\.\s*Rev\.|U\.\s*Chi\.\s*L\.\s*Rev\.|"
    r"Va\.\s*L\.\s*Rev\.|Tex\.\s*L\.\s*Rev\.|U\.\s*Pa\.\s*L\.\s*Rev\.|"
    r"Duke\s*L\.J\.|Geo\.\s*L\.J\.|Nw\.\s*U\.\s*L\.\s*Rev\.|"
    r"B\.U\.\s*L\.\s*Rev\.|Fordham\s*L\.\s*Rev\.|"
    r"[A-Z][A-Za-z\.]+\s+L(?:aw)?\.\s*(?:Rev\.|J\.))"
)


def parse(raw: str) -> ParsedCitation:
    """Return a ParsedCitation for the given raw footnote text."""
    text = raw.strip()

    # Try each type in order of specificity.
    # Article before case because article regex is more specific about the journal
    # abbreviation, whereas the case regex can match article-shaped text.
    result = (
        _try_statute(text)
        or _try_article(text)
        or _try_case(text)
        or _try_book(text)
        or ParsedCitation(raw=text, citation_type=CitationType.UNKNOWN)
    )
    result.raw = text
    return result


# ── Statute ──────────────────────────────────────────────────────────────────

_STATUTE_RE = re.compile(
    r"(?P<title>\d+)\s+"
    r"(?P<code>" + CODE_PAT + r")\s+"
    r"§§?\s*(?P<section>[\d\w\-–\.]+(?:\s*(?:et\s+seq\.|through|–|-)\s*[\d\w\-\.]+)?)"
    r"(?:\s*\((?P<year>\d{4})\))?",
    re.IGNORECASE,
)


def _try_statute(text: str) -> Optional[ParsedCitation]:
    m = _STATUTE_RE.search(text)
    if not m:
        return None
    c = ParsedCitation(raw=text, citation_type=CitationType.STATUTE)
    c.title = m.group("title")
    c.code = m.group("code")
    c.section = m.group("section").strip()
    c.year = m.group("year")
    c.search_query = f"{c.title} {c.code} section {c.section}"
    return c


# ── Case ─────────────────────────────────────────────────────────────────────

_CASE_RE = re.compile(
    r"(?P<parties>[A-Z][A-Za-z\s\.\,\&\'\-]+?\s+v\.\s+[A-Za-z\s\.\,\&\'\-]+?)\s*,\s*"
    r"(?P<volume>\d+)\s+"
    r"(?P<reporter>" + REPORTER_PAT + r")\s+"
    r"(?P<page>\d+)"
    r"(?:,\s*(?P<pincite>\d+))?"
    r"\s*\((?P<court_year>[^\)]+)\)",
    re.VERBOSE,
)

_CASE_SIMPLE_RE = re.compile(
    r"(?P<parties>[A-Z][A-Za-z\s\.\,\&\'\-]+?\s+v\.\s+[A-Za-z\s\.\,\&\'\-]+?)\s*,\s*"
    r"(?P<volume>\d+)\s+"
    r"(?P<reporter>[A-Z][A-Za-z\d\.\s]{1,20})\s+"
    r"(?P<page>\d+)"
    r"(?:,\s*(?P<pincite>\d+))?"
    r"\s*\((?P<court_year>[^\)]+)\)",
)


def _try_case(text: str) -> Optional[ParsedCitation]:
    m = _CASE_RE.search(text) or _CASE_SIMPLE_RE.search(text)
    if not m:
        return None
    court_year = m.group("court_year").strip()
    # Parse court and year from parenthetical like "9th Cir. 1999" or just "1999"
    year_m = re.search(r"(\d{4})", court_year)
    year = year_m.group(1) if year_m else None
    court = re.sub(r"\d{4}", "", court_year).strip().strip(",").strip() or None

    c = ParsedCitation(raw=text, citation_type=CitationType.CASE)
    c.parties = m.group("parties").strip().rstrip(",")
    c.volume = m.group("volume")
    c.reporter = m.group("reporter").strip()
    c.page = m.group("page")
    c.pincite = m.group("pincite") if "pincite" in m.groupdict() else None
    c.year = year
    c.court = court or None
    c.search_query = f"{c.parties} {c.volume} {c.reporter} {c.page}"
    return c


# ── Article ───────────────────────────────────────────────────────────────────

_ARTICLE_RE = re.compile(
    r"(?P<authors>[A-Z][A-Za-z\s\.\,\&]+?),\s+"
    r"(?P<title>[A-Z][^,]{5,120}),\s+"
    r"(?P<volume>\d+)\s+"
    r"(?P<journal>" + JOURNAL_WORDS + r")\s+"
    r"(?P<page>\d+)"
    r"(?:,\s*(?P<pincite>\d+))?"
    r"\s*\((?P<year>\d{4})\)",
    re.IGNORECASE,
)


def _try_article(text: str) -> Optional[ParsedCitation]:
    m = _ARTICLE_RE.search(text)
    if not m:
        return None
    c = ParsedCitation(raw=text, citation_type=CitationType.ARTICLE)
    c.authors = m.group("authors").strip()
    c.article_title = m.group("title").strip()
    c.volume = m.group("volume")
    c.journal = m.group("journal").strip()
    c.page = m.group("page")
    c.pincite = m.group("pincite") if "pincite" in m.groupdict() else None
    c.year = m.group("year")
    c.search_query = f"{c.article_title} {c.authors}"
    return c


# ── Book ─────────────────────────────────────────────────────────────────────

_BOOK_RE = re.compile(
    r"(?P<authors>[A-Z][A-Za-z\s\.\,\&]+?),\s+"
    r"(?P<title>[A-Z][^§\d]+?)\s+"
    r"(?P<page>\d+)\s*"
    r"\((?P<edition>[^)]*?\bed\.\s+)?(?P<year>\d{4})\)",
)


def _try_book(text: str) -> Optional[ParsedCitation]:
    m = _BOOK_RE.search(text)
    if not m:
        return None
    c = ParsedCitation(raw=text, citation_type=CitationType.BOOK)
    c.authors = m.group("authors").strip()
    c.book_title = m.group("title").strip().rstrip()
    c.page = m.group("page")
    c.edition = (m.group("edition") or "").strip() or None
    c.year = m.group("year")
    c.search_query = f"{c.book_title} {c.authors}"
    return c
