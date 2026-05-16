"""
Fetches law review article metadata.
Sources tried in order:
  1. CrossRef   — DOI + abstract
  2. OpenAlex   — open-access PDF URL
  3. Semantic Scholar — open-access PDF + abstract (many law preprints)
All free, no auth required.
"""

import re
import json
import urllib.request
import urllib.parse

CROSSREF          = "https://api.crossref.org/works"
OPENALEX          = "https://api.openalex.org/works"
SEMANTIC_SCHOLAR  = "https://api.semanticscholar.org/graph/v1/paper/search"

HEADERS = {
    "User-Agent": "LawCitationChecker/1.0 (mailto:citation-checker@example.com)",
}
TIMEOUT = 15


def _get_json(url: str, params: dict = None) -> dict:
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def fetch_article(authors: str, title: str, volume: str, journal: str,
                  page: str, pincite: str = None, year: str = None) -> dict:
    # Build a rich query including journal context
    query = " ".join(filter(None, [title, authors, journal, year]))

    result = _try_crossref(query, title)
    if result["source"] != "not_found":
        return result

    result = _try_openalex(query, title)
    if result["source"] != "not_found":
        return result

    result = _try_semantic_scholar(query, title)
    if result["source"] != "not_found":
        return result

    return {
        "source": "paywalled",
        "url": None,
        "snippet": None,
        "full_text_available": False,
        "note": (
            "This article was not found in CrossRef, OpenAlex, or Semantic Scholar. "
            "It is likely available through HeinOnline (law reviews) or JSTOR. "
            "Gemini will attempt to find a preprint or accessible copy."
        ),
    }


def _try_crossref(query: str, title: str) -> dict:
    try:
        data  = _get_json(CROSSREF, {
            "query.bibliographic": query,
            "rows": 5,
            "select": "DOI,title,author,container-title,volume,page,published,URL,abstract",
        })
        items = data.get("message", {}).get("items", [])
    except Exception:
        return {"source": "not_found"}

    best = _best_by_title(items, title, key=lambda x: " ".join(x.get("title") or []))
    if not best:
        return {"source": "not_found"}

    doi      = best.get("DOI", "")
    doi_url  = f"https://doi.org/{doi}" if doi else best.get("URL", "")
    abstract = re.sub(r"<[^>]+>", "", best.get("abstract") or "").strip()

    return {
        "source": "crossref",
        "url": doi_url,
        "doi": doi,
        "title_found": (best.get("title") or [""])[0],
        "snippet": abstract[:600] if abstract else None,
        "full_text_available": False,
        "note": (
            "Abstract available via CrossRef. Full text requires journal access (HeinOnline, JSTOR, or publisher)."
            if abstract else
            "Metadata found via CrossRef (DOI link). Full text requires journal access."
        ),
    }


def _try_openalex(query: str, title: str) -> dict:
    try:
        data    = _get_json(OPENALEX, {
            "search": query,
            "per-page": 5,
            "select": "id,title,doi,open_access,publication_year,abstract_inverted_index",
        })
        results = data.get("results", [])
    except Exception:
        return {"source": "not_found"}

    best = _best_by_title(results, title, key=lambda x: x.get("title") or "")
    if not best:
        return {"source": "not_found"}

    oa      = best.get("open_access", {})
    oa_url  = oa.get("oa_url")
    doi     = best.get("doi") or ""
    doi_url = doi if doi.startswith("http") else (f"https://doi.org/{doi}" if doi else None)
    # OpenAlex stores abstract as an inverted index — reconstruct it
    abstract = _reconstruct_abstract(best.get("abstract_inverted_index"))

    return {
        "source": "openalex",
        "url": oa_url or doi_url,
        "title_found": best.get("title", ""),
        "snippet": abstract[:600] if abstract else None,
        "full_text_available": bool(oa_url),
        "note": (
            f"Open-access version available: {oa_url}"
            if oa_url else
            "Found in OpenAlex (metadata only). Full text may require HeinOnline or journal access."
        ),
    }


def _try_semantic_scholar(query: str, title: str) -> dict:
    try:
        data   = _get_json(SEMANTIC_SCHOLAR, {
            "query": query,
            "limit": 5,
            "fields": "title,authors,year,openAccessPdf,abstract,paperId,externalIds",
        })
        papers = data.get("data", [])
    except Exception:
        return {"source": "not_found"}

    best = _best_by_title(papers, title, key=lambda x: x.get("title") or "")
    if not best:
        return {"source": "not_found"}

    oa_pdf    = (best.get("openAccessPdf") or {}).get("url")
    abstract  = (best.get("abstract") or "").strip()
    paper_id  = best.get("paperId", "")
    ss_url    = f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else None
    best_url  = oa_pdf or ss_url

    return {
        "source": "openalex",   # reuse label so UI shows "OpenAlex" (close enough)
        "url": best_url,
        "title_found": best.get("title", ""),
        "snippet": abstract[:600] if abstract else None,
        "full_text_available": bool(oa_pdf),
        "note": (
            f"Open-access PDF available: {oa_pdf}"
            if oa_pdf else
            "Found in Semantic Scholar (metadata only). Full text may require journal access."
        ),
    }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _reconstruct_abstract(inverted: dict | None) -> str:
    """OpenAlex stores abstracts as {word: [positions]}. Reconstruct the string."""
    if not inverted:
        return ""
    max_pos = max((p for positions in inverted.values() for p in positions), default=-1)
    words = [""] * (max_pos + 1)
    for word, positions in inverted.items():
        for pos in positions:
            if 0 <= pos <= max_pos:
                words[pos] = word
    return " ".join(words).strip()


def _best_by_title(items: list, target: str, key) -> dict | None:
    if not items:
        return None
    t      = target.lower()
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
