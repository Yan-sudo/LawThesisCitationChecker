"""
Fetches case text from CourtListener (free, no auth required).
API docs: https://www.courtlistener.com/api/rest/v4/
"""

import re
import requests

COURTLISTENER_SEARCH  = "https://www.courtlistener.com/api/rest/v4/search/"
COURTLISTENER_OPINION = "https://www.courtlistener.com/api/rest/v4/opinions/{id}/"

HEADERS = {"User-Agent": "LawCitationChecker/1.0 (academic research)"}
TIMEOUT = 15


def fetch_case(parties: str, volume: str, reporter: str, page: str,
               year: str = None, pincite: str = None) -> dict:
    """Returns source info dict for the given case citation."""
    query = f"{parties} {volume} {reporter} {page}"
    params = {
        "q": query,
        "type": "o",
        "order_by": "score desc",
        "stat_Precedential": "on",
    }

    try:
        resp = requests.get(COURTLISTENER_SEARCH, params=params,
                            headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
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

    hit = results[0]
    opinion_id = hit.get("id")
    case_name  = hit.get("caseName", parties)
    cl_url     = f"https://www.courtlistener.com{hit.get('absolute_url', '')}"

    snippet = _get_snippet(opinion_id, pincite) if opinion_id else None

    return {
        "source": "courtlistener",
        "url": cl_url,
        "case_name_found": case_name,
        "snippet": snippet,
        "full_text_available": snippet is not None,
        "note": None if snippet else "Full text not available in CourtListener for this opinion.",
    }


def _get_snippet(opinion_id: int, pincite: str = None) -> str | None:
    try:
        resp = requests.get(
            COURTLISTENER_OPINION.format(id=opinion_id),
            headers=HEADERS, timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
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
