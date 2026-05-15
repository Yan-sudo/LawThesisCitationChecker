"""
Fetches statute text from the U.S. House USCODE website (free, no auth).
For C.F.R. citations, uses eCFR.gov.
Uses only Python's built-in urllib — no third-party packages required.
"""

import re
import json
import urllib.request
import urllib.parse

USCODE_VIEW = "https://uscode.house.gov/view.xhtml"
ECFR_VIEW   = "https://www.ecfr.gov/current/title-{title}/section-{section}"

HEADERS = {"User-Agent": "LawCitationChecker/1.0 (academic research)"}
TIMEOUT = 15


def _get_html(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode(errors="replace")


def fetch_statute(title: str, code: str, section: str, year: str = None) -> dict:
    code_upper = (code or "").upper().replace(" ", "")
    if "CFR" in code_upper:
        return _fetch_ecfr(title, section)
    return _fetch_usc(title, section)


def _fetch_usc(title: str, section: str) -> dict:
    sec = section.lstrip("§").strip()
    view_url = f"{USCODE_VIEW}?{urllib.parse.urlencode({'req': f'{title} usc {sec}'})}"
    try:
        html = _get_html(view_url)
    except Exception as exc:
        return _error(str(exc), "U.S. House USCODE")

    snippet = _extract_snippet(html, sec)
    if not snippet:
        return {
            "source": "not_found",
            "url": view_url,
            "snippet": None,
            "full_text_available": False,
            "note": (
                f"{title} U.S.C. § {sec} was not found in the House USCODE database. "
                "Verify the title and section number, or check Westlaw / LexisNexis."
            ),
        }
    return {
        "source": "uscode_house",
        "url": view_url,
        "snippet": snippet,
        "full_text_available": True,
        "note": None,
    }


def _fetch_ecfr(title: str, section: str) -> dict:
    url = ECFR_VIEW.format(title=title, section=section)
    try:
        html = _get_html(url)
    except Exception as exc:
        return _error(str(exc), "eCFR")

    snippet = _extract_snippet(html, section)
    return {
        "source": "ecfr",
        "url": url,
        "snippet": snippet or None,
        "full_text_available": bool(snippet),
        "note": None if snippet else f"C.F.R. Title {title} § {section} not found in eCFR.",
    }


def _extract_snippet(html: str, section: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s{2,}", " ", text)
    # Capture from the section marker to the next section marker or end
    m = re.search(
        rf"§\s*{re.escape(section)}\b(.*?)(?=§\s*\d|\Z)",
        text, re.DOTALL
    )
    return m.group(0).strip() if m else ""


def _error(msg: str, source: str) -> dict:
    return {
        "source": "error",
        "url": None,
        "snippet": None,
        "full_text_available": False,
        "note": f"Network error while contacting {source}: {msg}",
    }
