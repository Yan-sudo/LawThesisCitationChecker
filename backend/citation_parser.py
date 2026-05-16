"""
Identifies and parses Bluebook citations from raw footnote text.

All rule numbers refer to The Bluebook: A Uniform System of Citation (21st ed. 2020).

Supported types:
  CASE         → Rule 10       (cases — full citation)
  SHORT_CASE   → Rule 10       (short form: Smith, 123 U.S. at 456)
  STATUTE      → Rule 12       (U.S.C., C.F.R., U.S.C.A., U.S.C.S.)
  CONSTITUTION → Rule 11       (U.S. Const., state constitutions)
  RESTATEMENT  → Rule 12.9.4   (Restatements, Model Codes, UCC)
  LEGISLATIVE  → Rule 13       (bills, reports, hearings, executive orders)
  ARTICLE      → Rule 16       (law review and journal articles)
  BOOK         → Rule 15       (books, treatises, nonperiodic materials)
  ID           → Rule 4.1      (id. short form — same source)
  SUPRA        → Rule 4.2      (supra/infra cross-references)
  UNKNOWN      → (not matched by any rule above)
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CitationType(str, Enum):
    CASE         = "case"
    SHORT_CASE   = "short_case"
    STATUTE      = "statute"
    CONSTITUTION = "constitution"
    RESTATEMENT  = "restatement"
    LEGISLATIVE  = "legislative"
    ARTICLE      = "article"
    BOOK         = "book"
    ID           = "id"
    SUPRA        = "supra"
    UNKNOWN      = "unknown"


# Maps each type to (rule_label, rule_description) for display in the UI.
# Rule numbers are from Bluebook 21st edition (2020).
BLUEBOOK_RULES: dict[CitationType, tuple[str, str]] = {
    CitationType.CASE:         ("Rule 10",     "Cases — full citation"),
    CitationType.SHORT_CASE:   ("Rule 10",     "Cases — short form"),
    CitationType.STATUTE:      ("Rule 12",     "Statutory codes (U.S.C., C.F.R.)"),
    CitationType.CONSTITUTION: ("Rule 11",     "Constitutions"),
    CitationType.RESTATEMENT:  ("Rule 12.9.4", "Restatements & model codes"),
    CitationType.LEGISLATIVE:  ("Rule 13",     "Legislative & executive materials"),
    CitationType.ARTICLE:      ("Rule 16",     "Periodical materials (journal articles)"),
    CitationType.BOOK:         ("Rule 15",     "Books & nonperiodic materials"),
    CitationType.ID:           ("Rule 4.1",    "Short form: Id."),
    CitationType.SUPRA:        ("Rule 4.2",    "Short form: Supra / Infra"),
    CitationType.UNKNOWN:      (None,          "Format not recognised"),
}


@dataclass
class ParsedCitation:
    raw: str
    citation_type: CitationType
    bluebook_rule: Optional[str] = None       # e.g. "Rule 10"
    bluebook_rule_desc: Optional[str] = None  # e.g. "Cases — full citation"
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
    # Supra/infra-specific
    supra_note: Optional[str] = None
    supra_author: Optional[str] = None
    # Extra
    search_query: Optional[str] = None
    errors: list = field(default_factory=list)


def parse(raw: str) -> ParsedCitation:
    """Return a ParsedCitation for the given raw footnote/authority text."""
    text = raw.strip()

    result = (
        _try_id(text)
        or _try_supra(text)
        or _try_constitution(text)
        or _try_restatement(text)
        or _try_legislative(text)
        or _try_statute(text)
        or _try_article(text)
        or _try_case(text)
        or _try_short_case(text)
        or _try_book(text)
        or ParsedCitation(raw=text, citation_type=CitationType.UNKNOWN)
    )
    result.raw = text
    # Attach rule labels
    rule, desc = BLUEBOOK_RULES[result.citation_type]
    result.bluebook_rule = rule
    result.bluebook_rule_desc = desc
    return result


# ── Rule 4.1 — Id. ───────────────────────────────────────────────────────────
# Covers: Id., Id. at 42, id. at § 101(a), Id. at *5

_ID_RE = re.compile(
    r"^[Ii]d\."
    r"(?:\s+at\s+(?P<pincite>[\d\*§][^\s,;\.]*))?"
    r"[\.,;]?$",
)


def _try_id(text: str) -> Optional[ParsedCitation]:
    m = _ID_RE.match(text.strip().rstrip(".").rstrip() + ".")
    if not m:
        # Also catch "Id." anywhere if the text is just "Id." with trailing punct
        if not re.match(r"^[Ii]d\.[\s,;]?$", text.strip()):
            return None
    c = ParsedCitation(raw=text, citation_type=CitationType.ID)
    if m and m.group("pincite"):
        c.pincite = m.group("pincite")
    return c


# ── Rule 4.2 — Supra / Infra ─────────────────────────────────────────────────
# Covers: Author, supra note 5; Author, supra note 5, at 42; supra note 5; infra note 10

_SUPRA_RE = re.compile(
    r"(?:(?P<author>[A-Z][A-Za-z\s\.\,\&]+?),\s*)?"
    r"(?P<direction>supra|infra)"
    r"(?:\s+note\s+(?P<note>\d+))?"
    r"(?:,\s*at\s+(?P<pincite>[\d\*§][^\s,;]*))?",
    re.IGNORECASE,
)


def _try_supra(text: str) -> Optional[ParsedCitation]:
    if not re.search(r"\b(?:supra|infra)\b", text, re.IGNORECASE):
        return None
    m = _SUPRA_RE.search(text)
    if not m:
        return None
    c = ParsedCitation(raw=text, citation_type=CitationType.SUPRA)
    c.supra_author = (m.group("author") or "").strip() or None
    c.supra_note = m.group("note")
    c.pincite = m.group("pincite")
    return c


# ── Rule 11 — Constitutions ──────────────────────────────────────────────────
# Covers: U.S. Const. art. I, § 8, cl. 3
#         U.S. Const. amend. XIV, § 1
#         U.S. Const. amend. I
#         Cal. Const. art. I, § 7
#         N.Y. Const. art. IV, § 3
# Rule: abbreviated jurisdiction + "Const." + article/amendment + optional section/clause

_CONST_RE = re.compile(
    r"(?P<jurisdiction>[A-Z][A-Za-z\.]+)\s+Const\."
    r"(?:\s+(?P<provision>(?:art|amend|§|cl)\..*?))?",
    re.IGNORECASE,
)


def _try_constitution(text: str) -> Optional[ParsedCitation]:
    if "Const." not in text:
        return None
    m = _CONST_RE.search(text)
    if not m:
        return None
    c = ParsedCitation(raw=text, citation_type=CitationType.CONSTITUTION)
    c.title = m.group("jurisdiction")
    c.section = (m.group("provision") or "").strip() or None
    return c


# ── Rule 12.9.4 — Restatements & Model Codes ─────────────────────────────────
# Covers: Restatement (Second) of Contracts § 71 (1981)
#         Restatement (Third) of Torts: Liability for Physical and Emotional Harm § 1
#         Model Penal Code § 2.02 (Official Draft 1962)
#         Uniform Commercial Code § 2-207

_RESTATEMENT_RE = re.compile(
    r"(?:"
    r"Restatement\s+\([^\)]+\)\s+of\s+[^§\d]+"   # Restatement (Second) of Contracts
    r"|Model\s+\w+\s+Code"                           # Model Penal Code, Model Rules, etc.
    r"|Uniform\s+[A-Za-z\s]+Code"                   # Uniform Commercial Code
    r"|U\.C\.C\."                                    # UCC abbreviation
    r"|Restatement\s+of\s+[A-Za-z\s]+"              # Restatement of Restitution (no edition)
    r")"
    r"(?:\s*§§?\s*(?P<section>[\d\w\.\-–]+))?",
    re.IGNORECASE,
)


def _try_restatement(text: str) -> Optional[ParsedCitation]:
    m = _RESTATEMENT_RE.search(text)
    if not m:
        return None
    c = ParsedCitation(raw=text, citation_type=CitationType.RESTATEMENT)
    c.section = (m.group("section") or "").strip() or None
    year_m = re.search(r"\((\d{4})\)", text)
    c.year = year_m.group(1) if year_m else None
    c.search_query = text[:60]
    return c


# ── Rule 13 — Legislative & Executive Materials ───────────────────────────────
# Covers:
#   Bills:    H.R. 1234, 117th Cong. § 2 (2021)
#             S. 456, 115th Cong. (2017)
#   Reports:  H.R. Rep. No. 104-369, at 5 (1995)
#             S. Rep. No. 103-7, at 10 (1993)
#             H. Conf. Rep. No. 108-391
#   Hearings: Hearing on S. 123 Before the S. Comm. on the Judiciary, 116th Cong. (2019)
#   Records:  148 Cong. Rec. S1234 (daily ed. Feb. 14, 2002)
#   Exec. Orders: Exec. Order No. 13,228, 66 Fed. Reg. 51,812 (Oct. 9, 2001)

_LEGISLATIVE_RE = re.compile(
    r"(?:"
    # Bills — H.R. is distinctive; S. must NOT be preceded by another letter or period
    # (to avoid matching "U.S." in case citations)
    r"\bH\.R\.\s*\d+"                                          # House bills: H.R. 1234
    r"|(?<![A-Za-z\.])S\.\s+\d+\s*,\s*\d+(?:st|nd|rd|th)\s+Cong\."  # Senate bills: S. 456, 117th Cong.
    r"|\bH\.J\.Res\.\s*\d+|\bS\.J\.Res\.\s*\d+"               # Joint resolutions
    r"|\bH\.Con\.Res\.\s*\d+|\bS\.Con\.Res\.\s*\d+"           # Concurrent resolutions
    r"|\bH\.Res\.\s*\d+"                                       # Simple resolutions
    r"|\bH\.R\.(?:\s+Conf\.)?\s+Rep\.\s+No\."                 # House reports
    r"|(?<![A-Za-z\.])S\.\s+Rep\.\s+No\."                     # Senate reports
    r"|\bCong\.\s+Rec\.\b"                                     # Congressional Record
    r"|Exec(?:utive)?\.?\s+Order\s+No\."                       # Executive Orders
    r"|\d+\s+Cong\.\s+Rec\."                                   # Cong. Rec. with volume number
    r"|\bHearing\s+(?:on\s+)?\bH\.R\.\s*\d+"                  # Hearings on bills
    r")",
    re.IGNORECASE,
)


def _try_legislative(text: str) -> Optional[ParsedCitation]:
    if not _LEGISLATIVE_RE.search(text):
        return None
    c = ParsedCitation(raw=text, citation_type=CitationType.LEGISLATIVE)
    year_m = re.search(r"\((\d{4})\)", text)
    c.year = year_m.group(1) if year_m else None
    c.search_query = text[:80]
    return c


# ── Rule 12 — Statutory codes ────────────────────────────────────────────────
# Covers: 42 U.S.C. § 1983 (2018)
#         29 C.F.R. § 1910.146 (2022)
#         26 U.S.C.A. § 501(c)(3)

_CODE_PAT = r"(?:U\.S\.C\.(?:A\.|S\.)?|C\.F\.R\.)"

_STATUTE_RE = re.compile(
    r"(?P<title>\d+)\s+"
    r"(?P<code>" + _CODE_PAT + r")\s+"
    r"§§?\s*(?P<section>[\d\w\(\)\-–\.]+(?:\s*(?:et\s+seq\.|through|to|–|-)\s*[\d\w\-\.]+)?)"
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


# ── Rule 16 — Journal articles ───────────────────────────────────────────────
# Format: Author(s), Title, Volume Journal Page (Year)
# One or more authors separated by & or ,; title in mixed case; volume numeric.

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

_ARTICLE_RE = re.compile(
    r"(?P<authors>[A-Z][A-Za-z\s\.\,\&]+?),\s+"
    r"(?P<title>[A-Z][^,]{5,180}),\s+"
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


# ── Rule 10 — Cases (full citation) ─────────────────────────────────────────
# Format: Parties v. Party, Volume Reporter Page[, Pincite] (Court Year)
# Parentheticals after the year are allowed: "(holding that…)"

REPORTERS = [
    r"U\.S\.", r"S\.Ct\.", r"S\.\s*Ct\.", r"L\.Ed\.(?:2d)?", r"L\.\s*Ed\.(?:\s*2d)?",
    r"F\.\d*d?", r"F\.\s*(?:Supp|App)\.(?:\s*\d+d)?",
    r"[A-Z][a-z]*\.\s*(?:\d+[a-z]+\s+)?(?:L\.\s*Rev\.|J\.)",
    r"[A-Z][a-z]+\.\s*\d*[a-z]*",
]
_REPORTER_PAT = "|".join(REPORTERS)

_CASE_RE = re.compile(
    r"(?P<parties>[A-Z][A-Za-z\s\.\,\&\'\-]+?\s+v\.\s+[A-Za-z\s\.\,\&\'\-]+?)\s*,\s*"
    r"(?P<volume>\d+)\s+"
    r"(?P<reporter>" + _REPORTER_PAT + r")\s+"
    r"(?P<page>\d+)"
    r"(?:,\s*(?P<pincite>[\d\-–]+))?"
    r"\s*\((?P<court_year>[^\)]+)\)",
    re.VERBOSE,
)

_CASE_SIMPLE_RE = re.compile(
    r"(?P<parties>[A-Z][A-Za-z\s\.\,\&\'\-]+?\s+v\.\s+[A-Za-z\s\.\,\&\'\-]+?)\s*,\s*"
    r"(?P<volume>\d+)\s+"
    r"(?P<reporter>[A-Z][A-Za-z\d\.\s]{1,20})\s+"
    r"(?P<page>\d+)"
    r"(?:,\s*(?P<pincite>[\d\-–]+))?"
    r"\s*\((?P<court_year>[^\)]+)\)",
)


def _try_case(text: str) -> Optional[ParsedCitation]:
    m = _CASE_RE.search(text) or _CASE_SIMPLE_RE.search(text)
    if not m:
        return None
    court_year = m.group("court_year").strip()
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


# ── Rule 10 (Short form) — Cases ──────────────────────────────────────────────
# Format: [One party name], Volume Reporter at Pincite
# Example: Miranda, 384 U.S. at 444
#          Smith, 32 F.3d at 890-91

_SHORT_CASE_RE = re.compile(
    r"(?P<party>[A-Z][A-Za-z\s\.\'\-]{2,40}?),\s*"
    r"(?P<volume>\d+)\s+"
    r"(?P<reporter>(?:" + _REPORTER_PAT + r"|[A-Z][A-Za-z\d\.\s]{1,20}))\s+"
    r"at\s+"
    r"(?P<pincite>[\d\-–]+)",
)


def _try_short_case(text: str) -> Optional[ParsedCitation]:
    if " at " not in text:
        return None
    m = _SHORT_CASE_RE.search(text)
    if not m:
        return None
    c = ParsedCitation(raw=text, citation_type=CitationType.SHORT_CASE)
    c.parties = m.group("party").strip()
    c.volume = m.group("volume")
    c.reporter = m.group("reporter").strip()
    c.pincite = m.group("pincite")
    c.search_query = f"{c.parties} {c.volume} {c.reporter}"
    return c


# ── Rule 15 — Books ───────────────────────────────────────────────────────────
# Format: Author(s), Title page (ed. Year)  — page is a standalone integer before the paren
# Example: William L. Prosser, Handbook of the Law of Torts 23 (4th ed. 1971)

_BOOK_RE = re.compile(
    r"(?P<authors>[A-Z][A-Za-z\s\.\,\&]+?),\s+"
    r"(?P<title>[A-Z][^§\d]+?)\s+"
    r"(?P<page>\d+)\s*"
    r"\((?:(?P<edition>[^)]*?\bed\.\s*))?(?P<year>\d{4})\)",
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
