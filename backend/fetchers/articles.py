"""
Fetches law review article metadata from CrossRef then OpenAlex (both free).
Full text is rarely available openly for law reviews — we flag paywalled sources.
"""

import re
import requests

CROSSREF = "https://api.crossref.org/works"
OPENALEX = "https://api.openalex.org/works"

HEADERS = {
    "User-Agent": "LawCitationChecker/1.0 (mailto:citation-checker@example.com)",
}
TIMEOUT = 15


def fetch_article(authors: str, title: str, volume: str, journal: str,
                  page: str, pincite: str = None, year: str = None) -> dict:
    query = f"{title} {authors}"

    result = _try_crossref(query, title)
    if result["source"] != "not_found":
        return result

    result = _try_openalex(query, title)
    if result["source"] != "not_found":
        return result

    return {
        "source": "paywalled",
        "url": None,
        "snippet": None,
        "full_text_available": False,
        "note": (
            "This article was not found in CrossRef or OpenAlex. "
            "It is likely available through HeinOnline (law reviews) or JSTOR. "
            "Please verify manually."
        ),
    }


def _try_crossref(query: str, title: str) -> dict:
    params = {
        "query.bibliographic": query,
        "rows": 5,
        "select": "DOI,title,author,container-title,volume,page,published,URL,abstract",
    }
    try:
        resp = requests.get(CROSSREF, params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        items = resp.json().get("message", {}).get("items", [])
    except Exception:
        return {"source": "not_found"}

    best = _best_by_title(items, title, key=lambda x: " ".join(x.get("title") or []))
    if not best:
        return {"source": "not_found"}

    doi = best.get("DOI", "")
    doi_url = f"https://doi.org/{doi}" if doi else best.get("URL", "")
    abstract = re.sub(r"<[^>]+>", "", best.get("abstract", "") or "").strip()

    return {
        "source": "crossref",
        "url": doi_url,
        "doi": doi,
        "title_found": (best.get("title") or [""])[0],
        "snippet": abstract or None,
        "full_text_available": False,
        "note": (
            "Abstract available via CrossRef. Full text requires journal access (HeinOnline, JSTOR, or publisher)."
            if abstract else
            "Metadata found via CrossRef (DOI link). Full text requires journal access."
        ),
    }


def _try_openalex(query: str, title: str) -> dict:
    params = {
        "search": query,
        "per-page": 5,
        "select": "id,title,doi,open_access,publication_year",
    }
    try:
        resp = requests.get(OPENALEX, params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except Exception:
        return {"source": "not_found"}

    best = _best_by_title(results, title, key=lambda x: x.get("title") or "")
    if not best:
        return {"source": "not_found"}

    oa = best.get("open_access", {})
    oa_url = oa.get("oa_url")
    doi = best.get("doi") or ""
    doi_url = doi if doi.startswith("http") else (f"https://doi.org/{doi}" if doi else None)

    return {
        "source": "openalex",
        "url": oa_url or doi_url,
        "title_found": best.get("title", ""),
        "snippet": None,
        "full_text_available": bool(oa_url),
        "note": (
            f"Open-access version available: {oa_url}"
            if oa_url else
            "Found in OpenAlex (metadata only). Full text may require HeinOnline or journal access."
        ),
    }


def _best_by_title(items: list, target: str, key) -> dict | None:
    if not items:
        return None
    t = target.lower()
    scored = [(item, _word_overlap(t, key(item).lower())) for item in items]
    scored.sort(key=lambda x: x[1], reverse=True)
    best_item, best_score = scored[0]
    return best_item if best_score > 0.4 else None


def _word_overlap(a: str, b: str) -> float:
    wa = set(re.findall(r"\w+", a))
    wb = set(re.findall(r"\w+", b))
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(len(wa), len(wb))
