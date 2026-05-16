"""
Fetches case text from CourtListener (free, no auth required).
API docs: https://www.courtlistener.com/api/rest/v4/

Search strategy:
  1. Citation-exact search: citation:("volume reporter page") — most precise
  2. Party + citation fallback if no results
"""

import re
import json
import urllib.request
import urllib.parse
from typing import Optional

COURTLISTENER_SEARCH  = "https://www.courtlistener.com/api/rest/v4/search/"
COURTLISTENER_OPINION = "https://www.courtlistener.com/api/rest/v4/opinions/{}/"

HEADERS = {"User-Agent": "LawCitationChecker/1.0 (academic research)"}
TIMEOUT = 15

# Maximum characters of opinion text sent to Gemini
SNIPPET_CHARS = 8000
# Characters of context before a pincite page marker
PINCITE_PRE   = 500
# Characters of context after a pincite page marker
PINCITE_POST  = 5000


def _get(url: str, params: dict = None) -> dict:
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def fetch_case(parties: str, volume: str, reporter: str, page: str,
               year: Optional[str] = None, pincite: Optional[str] = None) -> dict:
    # 1. Try citation-exact search first — avoids wrong-case retrieval
    hit = _search_by_citation(volume, reporter, page)
    # 2. Fall back to party-name + citation search
    if not hit:
        hit = _search_by_parties(parties, volume, reporter, page)

    if not hit:
        return {
            "source": "not_found",
            "url": None,
            "snippet": None,
            "full_text_available": False,
            "note": (
                "Case not found in CourtListener. It may be available in "
                "Westlaw or LexisNexis. Try searching by reporter citation manually."
            ),
        }

    opinion_id = hit.get("id")
    case_name  = hit.get("caseName", parties)
    cl_url     = f"https://www.courtlistener.com{hit.get('absolute_url', '')}"
    snippet    = _get_snippet(opinion_id, pincite) if opinion_id else None

    return {
        "source": "courtlistener",
        "url": cl_url,
        "case_name_found": case_name,
        "snippet": snippet,
        "full_text_available": snippet is not None,
        "note": None if snippet else "Full text not available in CourtListener for this opinion.",
    }


# ── Search helpers ─────────────────────────────────────────────────────────────

def _search_by_citation(volume: str, reporter: str, page: str) -> Optional[dict]:
    """Precise citation-based search. Returns first hit or None."""
    if not (volume and reporter and page):
        return None
    citation = f"{volume} {reporter} {page}"
    try:
        data = _get(COURTLISTENER_SEARCH, {
            "q": f'citation:("{citation}")',
            "type": "o",
            "order_by": "score desc",
            "stat_Precedential": "on",
        })
        results = data.get("results", [])
        return results[0] if results else None
    except Exception:
        return None


def _search_by_parties(parties: str, volume: str, reporter: str, page: str) -> Optional[dict]:
    """Fallback: search by party names + citation string."""
    query = f"{parties} {volume} {reporter} {page}"
    try:
        data = _get(COURTLISTENER_SEARCH, {
            "q": query,
            "type": "o",
            "order_by": "score desc",
            "stat_Precedential": "on",
        })
        results = data.get("results", [])
        return results[0] if results else None
    except Exception:
        return None


# ── Snippet extraction ─────────────────────────────────────────────────────────

def _get_snippet(opinion_id: int, pincite: Optional[str]) -> Optional[str]:
    try:
        data = _get(COURTLISTENER_OPINION.format(opinion_id))
    except Exception:
        return None

    text = data.get("plain_text") or _strip_html(data.get("html_with_citations") or "")
    if not text:
        return None

    # Collapse excessive whitespace but preserve paragraph breaks
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    if pincite:
        snippet = _extract_pincite_window(text, pincite)
        if snippet:
            return snippet

    # No pincite or pincite not found: return a wide opening window
    # (holdings and syllabus usually appear in the first portion of opinions)
    return text[:SNIPPET_CHARS].strip()


def _extract_pincite_window(text: str, pincite: str) -> Optional[str]:
    """Return a window around the pincite page marker in the opinion text."""
    p = pincite.strip().lstrip("*").strip()
    # CourtListener marks page breaks as *444, **444, [444], or just a bare number
    patterns = [
        rf"\*+\s*{re.escape(p)}\b",          # *444 or **444
        rf"\[{re.escape(p)}\]",               # [444]
        rf"(?<!\d){re.escape(p)}(?!\d)",      # bare number (loose match)
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            start = max(0, m.start() - PINCITE_PRE)
            end   = min(len(text), m.end() + PINCITE_POST)
            return text[start:end].strip()
    return None


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def _error(msg: str) -> dict:
    return {
        "source": "error",
        "url": None,
        "snippet": None,
        "full_text_available": False,
        "note": f"Network error while contacting CourtListener: {msg}",
    }
