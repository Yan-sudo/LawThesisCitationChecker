"""
Offline tests for fetcher modules — uses unittest.mock to patch network calls.
Run with: cd backend && python test_fetchers.py
"""

import sys
import unittest
from unittest.mock import patch, MagicMock


def check(condition, msg):
    if condition:
        print(f"  PASS  {msg}")
    else:
        print(f"  FAIL  {msg}")
        sys.exit(1)


# ── cases.py helper tests (no network) ──────────────────────────────────────

print("\n── cases.py helpers ──────────────────────────────")

from fetchers.cases import _extract_pincite_window, _strip_html

# Pincite with * marker
text = "A" * 1000 + "\n*445\n" + "B" * 1000
result = _extract_pincite_window(text, "445")
check(result is not None, "Pincite *445 found")
check("445" in result, "Pincite text included")

# Pincite with ** marker
text = "A" * 500 + "\n**495\n" + "B" * 500
result = _extract_pincite_window(text, "495")
check(result is not None, "Pincite **495 found")

# Pincite with [bracket] marker
text = "A" * 500 + "\n[436]\n" + "B" * 500
result = _extract_pincite_window(text, "436")
check(result is not None, "Pincite [436] found")

# Pincite not found
text = "No page markers here at all"
result = _extract_pincite_window(text, "999")
check(result is None, "Pincite not found → None")

# _strip_html
html = "<p>Hello <b>world</b></p><div>test</div>"
clean = _strip_html(html)
check("Hello" in clean and "world" in clean and "test" in clean, f"HTML stripped: '{clean}'")
check("<" not in clean, "No HTML tags remain")


# ── cases.py fetch_case with mocked network ─────────────────────────────────

print("\n── cases.py fetch_case (mocked) ────────────────")

from fetchers.cases import fetch_case

# Mock: citation search returns a hit
mock_search_result = {
    "results": [{
        "id": 12345,
        "caseName": "Miranda v. Arizona",
        "absolute_url": "/opinion/12345/miranda-v-arizona/",
    }]
}

mock_opinion_result = {
    "plain_text": "The person has the right to remain silent. *436 This is a fundamental right. " * 50,
}

def mock_get_citation_search(url, params=None):
    if "search" in url:
        return mock_search_result
    if "opinions" in url:
        return mock_opinion_result
    return {}

with patch("fetchers.cases._get", side_effect=mock_get_citation_search):
    r = fetch_case(
        parties="Miranda v. Arizona", volume="384", reporter="U.S.", page="436",
        year="1966"
    )
    check(r["source"] == "courtlistener", f"Source=courtlistener: {r['source']}")
    check(r["url"] is not None, f"URL present: {r['url']}")
    check(r["snippet"] is not None, "Snippet present")
    check(r["full_text_available"] is True, "Full text available")

# Mock: no results found
def mock_get_no_results(url, params=None):
    return {"results": []}

with patch("fetchers.cases._get", side_effect=mock_get_no_results):
    r = fetch_case(
        parties="Unknown v. Nobody", volume="999", reporter="F.3d", page="1",
    )
    check(r["source"] == "not_found", f"Source=not_found: {r['source']}")
    check(r["url"] is None, "No URL")
    check(r["full_text_available"] is False, "No full text")

# Mock: network error
def mock_get_error(url, params=None):
    raise ConnectionError("Connection refused")

with patch("fetchers.cases._get", side_effect=mock_get_error):
    r = fetch_case(
        parties="Error v. Case", volume="1", reporter="F.3d", page="1",
    )
    check(r["source"] == "not_found", f"Network error → not_found: {r['source']}")


# ── statutes.py helper tests ────────────────────────────────────────────────

print("\n── statutes.py helpers ───────────────────────────")

from fetchers.statutes import _extract_snippet

# Snippet with § marker
html = """
<html><body>
<div>§ 1983. Civil action for deprivation of rights. Every person who, under color
of any statute, ordinance, regulation, custom, or usage, of any State or Territory,
subjects any citizen to the deprivation of any rights secured by the Constitution
shall be liable to the party injured.</div>
<div>§ 1984. Something else entirely.</div>
</body></html>
"""
snippet = _extract_snippet(html, "1983")
check("1983" in snippet, f"§ 1983 found in snippet")
check("deprivation" in snippet, "Statute text present")

# No matching section
snippet2 = _extract_snippet("<html><body>Nothing here</body></html>", "9999")
check(len(snippet2) < 200 or snippet2 == "", f"No match → short/empty: len={len(snippet2)}")


# ── statutes.py fetch_statute with mocked network ───────────────────────────

print("\n── statutes.py fetch_statute (mocked) ───────────")

from fetchers.statutes import fetch_statute

mock_usc_html = """
<html><body>
<div class="section">§ 1983. Civil action for deprivation of rights
Every person who, under color of any statute, shall be liable.</div>
</body></html>
"""

with patch("fetchers.statutes._get_html", return_value=mock_usc_html):
    r = fetch_statute(title="42", code="U.S.C.", section="1983", year="2018")
    check(r["source"] == "uscode_house", f"Source=uscode_house: {r['source']}")
    check(r["url"] is not None, f"URL present: {r['url']}")
    check("1983" in r["snippet"], "Snippet contains section text")

# CFR dispatch
with patch("fetchers.statutes._get_html", return_value="<html><body>§ 541.100 Salary test</body></html>"):
    r = fetch_statute(title="29", code="C.F.R.", section="541.100")
    check(r["source"] == "ecfr", f"CFR → eCFR source: {r['source']}")

# Network error
with patch("fetchers.statutes._get_html", side_effect=TimeoutError("timeout")):
    r = fetch_statute(title="42", code="U.S.C.", section="99999")
    check(r["source"] == "error", f"Network error → error: {r['source']}")
    check("error" in r["note"].lower(), f"Error note: {r['note'][:80]}")


# ── articles.py helper tests ────────────────────────────────────────────────

print("\n── articles.py helpers ───────────────────────────")

from fetchers.articles import _reconstruct_abstract, _best_by_title, _word_overlap

# _reconstruct_abstract
inverted = {
    "The": [0],
    "Constitution": [1],
    "protects": [2],
    "privacy": [3],
    "rights": [4],
}
abstract = _reconstruct_abstract(inverted)
check(abstract == "The Constitution protects privacy rights", f"Abstract: '{abstract}'")

# Empty / None
check(_reconstruct_abstract(None) == "", "None → empty string")
check(_reconstruct_abstract({}) == "", "Empty dict → empty string")

# _word_overlap
check(_word_overlap("hello world", "hello world") == 1.0, "Identical → 1.0")
check(_word_overlap("hello world", "hello earth") == 0.5, "50% overlap → 0.5")
check(_word_overlap("a b c", "d e f") == 0.0, "No overlap → 0.0")
check(_word_overlap("", "") == 0.0, "Empty strings → 0.0")

# _best_by_title
items = [
    {"title": "Feminist Legal Methods"},
    {"title": "Completely Different Paper"},
    {"title": "Feminist Legal Theory Methods"},
]
best = _best_by_title(items, "Feminist Legal Methods", key=lambda x: x["title"])
check(best is not None, "Best match found")
check(best["title"] == "Feminist Legal Methods", f"Best match: {best['title']}")

# No good match
items2 = [{"title": "Something Completely Unrelated To The Target"}]
best2 = _best_by_title(items2, "Feminist Legal Methods", key=lambda x: x["title"])
check(best2 is None, "No good match → None")


# ── articles.py fetch_article with mocked network ───────────────────────────

print("\n── articles.py fetch_article (mocked) ───────────")

from fetchers.articles import fetch_article

mock_crossref = {
    "message": {
        "items": [{
            "DOI": "10.2307/1234567",
            "title": ["Feminist Legal Methods"],
            "author": [{"given": "Katharine", "family": "Bartlett"}],
            "container-title": ["Harvard Law Review"],
            "abstract": "<p>This article examines feminist approaches to legal analysis.</p>",
            "URL": "https://doi.org/10.2307/1234567",
        }]
    }
}

def mock_get_json_crossref(url, params=None):
    return mock_crossref

with patch("fetchers.articles._get_json", side_effect=mock_get_json_crossref):
    r = fetch_article(
        authors="Katharine T. Bartlett", title="Feminist Legal Methods",
        volume="103", journal="Harv. L. Rev.", page="829", year="1990",
    )
    check(r["source"] == "crossref", f"Source=crossref: {r['source']}")
    check(r["url"] is not None, f"DOI URL present: {r['url']}")
    check(r["snippet"] is not None, "Abstract snippet present")

# Mock: all sources return nothing
def mock_get_json_empty(url, params=None):
    if "crossref" in url:
        return {"message": {"items": []}}
    if "openalex" in url:
        return {"results": []}
    if "semanticscholar" in url:
        return {"data": []}
    return {}

with patch("fetchers.articles._get_json", side_effect=mock_get_json_empty):
    r = fetch_article(
        authors="Nobody", title="Nonexistent Paper",
        volume="1", journal="No Journal", page="1",
    )
    check(r["source"] == "paywalled", f"All empty → paywalled: {r['source']}")
    check("HeinOnline" in r["note"], f"Note mentions HeinOnline: {r['note'][:60]}")


# ── books.py helper tests ───────────────────────────────────────────────────

print("\n── books.py helpers ──────────────────────────────")

from fetchers.books import _last_name, _overlap

check(_last_name("William L. Prosser") == "Prosser", f"Last name: {_last_name('William L. Prosser')}")
check(_last_name("Smith & Jones") == "Smith", f"First author last: {_last_name('Smith & Jones')}")
check(_last_name("Posner, Richard") == "Posner", f"Comma-separated: {_last_name('Posner, Richard')}")

check(_overlap("the law of torts", "the law of torts") == 1.0, "Identical → 1.0")
check(_overlap("torts law", "contracts law") > 0, f"Partial overlap: {_overlap('torts law', 'contracts law')}")
check(_overlap("abc", "xyz") == 0.0, "No overlap → 0.0")


# ── books.py fetch_book with mocked network ─────────────────────────────────

print("\n── books.py fetch_book (mocked) ─────────────────")

from fetchers.books import fetch_book

mock_books = {
    "items": [{
        "volumeInfo": {
            "title": "Handbook of the Law of Torts",
            "authors": ["William L. Prosser"],
            "publishedDate": "1971",
            "previewLink": "https://books.google.com/books?id=abc123",
            "description": "A comprehensive treatise on tort law.",
        },
        "accessInfo": {
            "viewability": "PARTIAL",
        },
    }]
}

with patch("fetchers.books._get_json", return_value=mock_books):
    r = fetch_book(authors="William L. Prosser", title="Handbook of the Law of Torts", page="23", year="1971")
    check(r["source"] == "google_books", f"Source=google_books: {r['source']}")
    check(r["url"] is not None, f"Preview URL: {r['url']}")
    check(r["full_text_available"] is True, "Partial preview available")
    check(r["snippet"] is not None, "Description present")

# Mock: no results
with patch("fetchers.books._get_json", return_value={"items": []}):
    r = fetch_book(authors="Nobody", title="Nonexistent Book")
    check(r["source"] == "not_found", f"No results → not_found: {r['source']}")
    check("WorldCat" in r["note"], f"Note mentions WorldCat: {r['note'][:60]}")

# Mock: network error
with patch("fetchers.books._get_json", side_effect=Exception("Network unreachable")):
    r = fetch_book(authors="Error", title="Error Book")
    check(r["source"] == "error", f"Network error → error: {r['source']}")


# ── main.py _fetch_source dispatch test ─────────────────────────────────────

print("\n── main.py _fetch_source dispatch (mocked) ──────")

import citation_parser as cp
from main import _fetch_source

# Case dispatch
with patch("fetchers.cases._get", side_effect=mock_get_no_results):
    parsed = cp.parse("Miranda v. Arizona, 384 U.S. 436 (1966)")
    r = _fetch_source(parsed)
    check(r["source"] == "not_found", f"CASE dispatch works: {r['source']}")

# Constitution dispatch (no network needed)
parsed = cp.parse("U.S. Const. amend. XIV, § 1")
r = _fetch_source(parsed)
check(r["source"] == "constitution", f"CONSTITUTION dispatch: {r['source']}")
check(r["url"] is not None, "Constitution has URL")

# Id. dispatch
parsed = cp.parse("Id. at 445")
r = _fetch_source(parsed)
check(r["source"] == "id_citation", f"ID dispatch: {r['source']}")

# Supra dispatch
parsed = cp.parse("Smith, supra note 5, at 42")
r = _fetch_source(parsed)
check(r["source"] == "supra_citation", f"SUPRA dispatch: {r['source']}")

# Legislative dispatch
parsed = cp.parse("H.R. 1234, 117th Cong. § 2 (2021)")
r = _fetch_source(parsed)
check(r["source"] == "legislative", f"LEGISLATIVE dispatch: {r['source']}")

# Restatement dispatch
parsed = cp.parse("Restatement (Second) of Contracts § 71 (1981)")
r = _fetch_source(parsed)
check(r["source"] == "restatement", f"RESTATEMENT dispatch: {r['source']}")

# Administrative dispatch
parsed = cp.parse("In re Blockratize, Inc. d/b/a Polymarket, CFTC Docket No. 22-09 (Jan. 3, 2022)")
r = _fetch_source(parsed)
check(r["source"] == "administrative", f"ADMINISTRATIVE dispatch: {r['source']}")

# UNKNOWN dispatch
parsed = cp.parse("not a citation at all")
r = _fetch_source(parsed)
check(r["source"] == "unrecognised", f"UNKNOWN dispatch: {r['source']}")


print("\nAll fetcher tests passed.\n")
