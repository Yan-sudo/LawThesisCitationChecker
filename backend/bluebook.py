"""
Bluebook validation and formatting for the four supported citation types.
Implements rules 10 (cases), 12 (statutes), 15 (books), 16 (periodicals).
"""

import re
from typing import Optional
from citation_parser import ParsedCitation, CitationType


# ── Reporter normalization map (common mis-spellings / expansions) ────────────
REPORTER_NORMALIZE = {
    "US": "U.S.",
    "U.S": "U.S.",
    "S.Ct.": "S. Ct.",
    "SCt": "S. Ct.",
    "L.Ed.": "L. Ed.",
    "L.Ed.2d": "L. Ed. 2d",
    "F2d": "F.2d",
    "F3d": "F.3d",
    "F4th": "F.4th",
    "FSup": "F. Supp.",
    "FSupp": "F. Supp.",
    "FSupp2d": "F. Supp. 2d",
    "FSupp3d": "F. Supp. 3d",
}

# Courts whose decisions cite to a specific reporter — used to infer missing court
REPORTER_COURT_MAP = {
    "U.S.": "U.S. Supreme Court",
    "S. Ct.": "U.S. Supreme Court",
    "L. Ed.": "U.S. Supreme Court",
    "L. Ed. 2d": "U.S. Supreme Court",
}

# Official USC code abbreviation
USC_VARIANTS = {"usc", "u.s.c.", "u.s.c.a.", "u.s.c.s.", "cfr", "c.f.r."}


def validate_and_format(citation: ParsedCitation) -> dict:
    """
    Returns a dict with:
      - is_valid: bool
      - issues: list[str]  — human-readable problems found
      - suggested: str     — corrected Bluebook string
    """
    if citation.citation_type == CitationType.CASE:
        return _check_case(citation)
    if citation.citation_type == CitationType.STATUTE:
        return _check_statute(citation)
    if citation.citation_type == CitationType.ARTICLE:
        return _check_article(citation)
    if citation.citation_type == CitationType.BOOK:
        return _check_book(citation)
    return {"is_valid": False, "issues": ["Could not identify citation type."], "suggested": citation.raw}


# ── Cases (Rule 10) ──────────────────────────────────────────────────────────

def _check_case(c: ParsedCitation) -> dict:
    issues = []

    # Parties: both sides must be present, separated by "v."
    if c.parties:
        if " v. " not in c.parties and " v " not in c.parties:
            issues.append("Case name should use 'v.' between parties (e.g., Miranda v. Arizona).")
        # Italicize reminder (can't enforce in plain text, flag it)
        if c.parties == c.parties.upper():
            issues.append("Case name should not be all-caps; use title case.")
    else:
        issues.append("Case name is missing.")

    # Reporter normalization
    reporter = c.reporter or ""
    normalized_reporter = REPORTER_NORMALIZE.get(reporter.replace(" ", ""), reporter)

    # Year
    if not c.year:
        issues.append("Year is missing from the parenthetical.")

    # Court in parenthetical: omit for U.S. Supreme Court cases in U.S. reporter
    court_needed = normalized_reporter not in ("U.S.", "S. Ct.", "L. Ed.", "L. Ed. 2d")
    if court_needed and not c.court:
        issues.append("Court abbreviation is required in the parenthetical for non-SCOTUS reporters.")
    if not court_needed and c.court:
        issues.append(
            f"Court name ('{c.court}') is not needed in the parenthetical when citing to the U.S. reporter."
        )

    # Build suggested form
    court_part = ""
    if court_needed and c.court:
        court_part = f"{c.court} "
    year_part = c.year or "YEAR"
    pincite_part = f", {c.pincite}" if c.pincite else ""
    parties = c.parties or "Plaintiff v. Defendant"
    suggested = (
        f"{parties}, {c.volume or 'VOL'} {normalized_reporter} "
        f"{c.page or 'PAGE'}{pincite_part} ({court_part}{year_part})"
    )

    return {"is_valid": len(issues) == 0, "issues": issues, "suggested": suggested}


# ── Statutes (Rule 12) ───────────────────────────────────────────────────────

def _check_statute(c: ParsedCitation) -> dict:
    issues = []

    if not c.title:
        issues.append("Title number is missing (e.g., '42' in '42 U.S.C.').")
    if not c.section:
        issues.append("Section number is missing.")

    # Normalize code abbreviation
    code_raw = (c.code or "").strip().rstrip(".")
    code_normalized = "U.S.C."  # default; expand if CFR support added
    if "cfr" in code_raw.lower() or "c.f.r" in code_raw.lower():
        code_normalized = "C.F.R."

    # Section symbol
    section = c.section or "§"
    multi = "§§" if re.search(r"[-–]|et seq\.", section, re.IGNORECASE) else "§"

    # Year: Bluebook requires the year of the code edition in the parenthetical
    year_part = f" ({c.year})" if c.year else " (YEAR)"

    suggested = f"{c.title or 'TITLE'} {code_normalized} {multi} {section}{year_part}"

    return {"is_valid": len(issues) == 0, "issues": issues, "suggested": suggested}


# ── Journal articles (Rule 16) ───────────────────────────────────────────────

def _check_article(c: ParsedCitation) -> dict:
    issues = []

    if not c.authors:
        issues.append("Author name is missing.")
    if not c.article_title:
        issues.append("Article title is missing.")
    if not c.volume:
        issues.append("Volume number is missing.")
    if not c.journal:
        issues.append("Journal name is missing.")
    if not c.page:
        issues.append("First page number is missing.")
    if not c.year:
        issues.append("Year is missing.")

    # Author format: Last name only for single author per Bluebook (first cite uses full name)
    # We'll just keep whatever was given and flag if it looks odd
    authors = c.authors or "Author"
    title = c.article_title or "Title"
    journal = c.journal or "Journal"
    pincite_part = f", {c.pincite}" if c.pincite else ""

    suggested = (
        f"{authors}, {title}, "
        f"{c.volume or 'VOL'} {journal} {c.page or 'PAGE'}{pincite_part} ({c.year or 'YEAR'})"
    )

    return {"is_valid": len(issues) == 0, "issues": issues, "suggested": suggested}


# ── Books (Rule 15) ──────────────────────────────────────────────────────────

def _check_book(c: ParsedCitation) -> dict:
    issues = []

    if not c.authors:
        issues.append("Author name is missing.")
    if not c.book_title:
        issues.append("Book title is missing.")
    if not c.year:
        issues.append("Year is missing.")

    authors = c.authors or "Author"
    title = c.book_title or "Title"
    page_part = f" {c.page}" if c.page else ""
    edition_part = f"{c.edition} " if c.edition else ""
    year = c.year or "YEAR"

    suggested = f"{authors}, {title}{page_part} ({edition_part}{year})"

    return {"is_valid": len(issues) == 0, "issues": issues, "suggested": suggested}
