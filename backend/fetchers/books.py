"""
Fetches book metadata from Google Books API (free, no auth required for searches).
Uses only Python's built-in urllib — no third-party packages required.
"""

import re
import json
import urllib.request
import urllib.parse

GOOGLE_BOOKS = "https://www.googleapis.com/books/v1/volumes"
HEADERS = {"User-Agent": "LawCitationChecker/1.0 (academic research)"}
TIMEOUT = 15


def _get_json(url: str, params: dict = None) -> dict:
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def fetch_book(authors: str, title: str, page: str = None,
               year: str = None, edition: str = None) -> dict:
    last  = _last_name(authors)
    query = f'intitle:"{title}" inauthor:"{last}"'
    try:
        items = _get_json(GOOGLE_BOOKS, {"q": query, "maxResults": 5, "printType": "books"}).get("items", [])
    except Exception as exc:
        return _error(str(exc))

    best = _best_match(items, title, authors, year)
    if not best:
        return {
            "source": "not_found",
            "url": None,
            "snippet": None,
            "full_text_available": False,
            "note": (
                f'"{title}" by {authors} was not found in Google Books. '
                "Try WorldCat, HathiTrust, or a university library catalog."
            ),
        }

    info        = best.get("volumeInfo", {})
    access      = best.get("accessInfo", {})
    preview     = info.get("previewLink")
    viewability = access.get("viewability", "NO_PAGES")
    has_preview = viewability in ("ALL_PAGES", "PARTIAL")
    description = (info.get("description") or "")[:400] or None

    return {
        "source": "google_books",
        "url": preview,
        "title_found": info.get("title", ""),
        "authors_found": ", ".join(info.get("authors") or []),
        "published_year": (info.get("publishedDate") or "")[:4] or None,
        "snippet": description,
        "full_text_available": has_preview,
        "note": (
            None if has_preview else
            "Google Books has this title but no page preview is available. "
            "Full text may be available through HathiTrust, a library, or the publisher."
        ),
    }


def _best_match(items: list, title: str, authors: str, year: str) -> dict | None:
    if not items:
        return None
    t_lower = title.lower()
    last    = _last_name(authors).lower()
    for item in items:
        info       = item.get("volumeInfo", {})
        item_title = (info.get("title") or "").lower()
        item_auths = " ".join(info.get("authors") or []).lower()
        pub_year   = (info.get("publishedDate") or "")[:4]
        title_ok   = _overlap(t_lower, item_title) > 0.5
        author_ok  = last in item_auths
        year_ok    = (not year) or (not pub_year) or abs(int(pub_year) - int(year)) <= 2
        if title_ok and author_ok and year_ok:
            return item
    for item in items:
        if _overlap(t_lower, (item.get("volumeInfo", {}).get("title") or "").lower()) > 0.6:
            return item
    return None


def _last_name(authors: str) -> str:
    first = authors.split("&")[0].split(",")[0].strip()
    return first.split()[-1] if first else authors


def _overlap(a: str, b: str) -> float:
    wa = set(re.findall(r"\w+", a))
    wb = set(re.findall(r"\w+", b))
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(len(wa), len(wb))


def _error(msg: str) -> dict:
    return {
        "source": "error",
        "url": None,
        "snippet": None,
        "full_text_available": False,
        "note": f"Network error while contacting Google Books: {msg}",
    }
