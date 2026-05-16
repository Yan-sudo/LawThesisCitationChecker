"""
Fetches statute text from the U.S. House USCODE website (free, no auth).
For C.F.R. citations, uses eCFR.gov.
Uses only Python's built-in urllib — no third-party packages required.
"""

import re
import json
import urllib.request
import urllib.parse

# Cornell Law has stable, deep-linkable section URLs that work reliably
CORNELL_USC  = "https://www.law.cornell.edu/uscode/text/{title}/{section}"
ECFR_VIEW    = "https://www.ecfr.gov/current/title-{title}/section-{section}"

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
    # Cornell Law provides stable, directly linkable section pages
    view_url = CORNELL_USC.format(title=title, section=urllib.parse.quote(sec, safe=""))
    try:
        html = _get_html(view_url)
    except Exception as exc:
        return _error(str(exc), "Cornell Law USC")

    snippet = _extract_snippet(html, sec)
    if not snippet:
        return {
            "source": "not_found",
            "url": view_url,
            "snippet": None,
            "full_text_available": False,
            "note": (
                f"{title} U.S.C. § {sec} was not found at law.cornell.edu. "
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
    # Cornell Law wraps the statutory text in labelled sections — look for it broadly
    m = re.search(
        rf"§\s*{re.escape(section)}\b(.*?)(?=§\s*\d+[a-z\-]*\.?\s|\Z)",
        text, re.DOTALL | re.IGNORECASE
    )
    if m:
        return m.group(0).strip()[:3000]
    # Fallback: return first 2000 chars of readable text (after nav/header noise)
    clean = re.sub(r"\s{3,}", "\n", text).strip()
    return clean[:2000] if len(clean) > 200 else ""


def _error(msg: str, source: str) -> dict:
    return {
        "source": "error",
        "url": None,
        "snippet": None,
        "full_text_available": False,
        "note": f"Network error while contacting {source}: {msg}",
    }
