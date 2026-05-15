"""
Fetches case text from CourtListener (free, no auth required).
API docs: https://www.courtlistener.com/api/rest/v4/
Uses only Python's built-in urllib — no third-party packages required.
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


def _get(url: str, params: dict = None) -> dict:
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def fetch_case(parties: str, volume: str, reporter: str, page: str,
               year: Optional[str] = None, pincite: Optional[str] = None) -> dict:
    query = f"{parties} {volume} {reporter} {page}"
    try:
        data = _get(COURTLISTENER_SEARCH, {
            "q": query,
            "type": "o",
            "order_by": "score desc",
            "stat_Precedential": "on",
        })
    except Exception as exc:
        return _error(str(exc))

    results = data.get("results", [])
    if not results:
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

    hit        = results[0]
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


def _get_snippet(opinion_id: int, pincite: Optional[str]) -> Optional[str]:
    try:
        data = _get(COURTLISTENER_OPINION.format(opinion_id))
    except Exception:
        return None

    text = data.get("plain_text") or _strip_html(data.get("html_with_citations") or "")
    if not text:
        return None

    if pincite:
        m = re.search(rf"\*+\s*{re.escape(pincite)}\b", text)
        if m:
            start = max(0, m.start() - 200)
            end   = min(len(text), m.end() + 400)
            return text[start:end].strip()

    return text[:500].strip()


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
