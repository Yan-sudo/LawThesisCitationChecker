"""
End-to-end test for the backend pipeline.
Creates a minimal .docx in memory, runs it through the full pipeline
(extract -> split -> parse -> fetch), and verifies the output structure.

This test does NOT require a Gemini API Key because the LLM calls
are performed client-side in the browser (index.html).

Run with: cd backend && python test_e2e.py
"""

import sys
import io
import zipfile
import xml.etree.ElementTree as ET
from unittest.mock import patch

from docx_parser import extract_all
from authority_splitter import split_authorities
import citation_parser as cp
from main import _process_one


def check(condition, msg):
    if condition:
        print(f"  PASS  {msg}")
    else:
        print(f"  FAIL  {msg}")
        sys.exit(1)


# ── Helper: Build a minimal .docx in memory ─────────────────────────────────

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _build_docx(footnotes: list[tuple[int, str, str]]) -> bytes:
    """
    Build a minimal valid .docx with the given footnotes.
    footnotes: list of (id, footnote_text, body_sentence)
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. [Content_Types].xml
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
            "</Types>",
        )

        # 2. word/document.xml
        doc_xml = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document xmlns:w="{W}">'
            f"<w:body>"
        )
        for fn_id, _, sentence in footnotes:
            doc_xml += (
                f"<w:p>"
                f"<w:r><w:t>{sentence} </w:t></w:r>"
                f'<w:r><w:footnoteReference w:id="{fn_id}"/></w:r>'
                f"</w:p>"
            )
        doc_xml += "</w:body></w:document>"
        zf.writestr("word/document.xml", doc_xml)

        # 3. word/footnotes.xml
        fn_xml = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:footnotes xmlns:w="{W}">'
        )
        for fn_id, fn_text, _ in footnotes:
            fn_xml += (
                f'<w:footnote w:id="{fn_id}">'
                f"<w:p><w:r><w:t>{fn_text}</w:t></w:r></w:p>"
                f"</w:footnote>"
            )
        fn_xml += "</w:footnotes>"
        zf.writestr("word/footnotes.xml", fn_xml)

    return buf.getvalue()


# ── Test 1: docx_parser extracts footnotes correctly ────────────────────────

print("\n── Test 1: docx_parser extraction ────────────────")

docx_bytes = _build_docx([
    (1, "Miranda v. Arizona, 384 U.S. 436 (1966).", "The police must inform suspects of their rights."),
    (2, "42 U.S.C. § 1983 (2018); see also Brown v. Board, 347 U.S. 483 (1954).", "Federal law provides a remedy for civil rights violations."),
])

items = extract_all(docx_bytes)
check(len(items) == 2, f"Extracted 2 footnotes (got {len(items)})")

fn1 = next(i for i in items if i["number"] == 1)
check("Miranda" in fn1["footnote"], f"FN1 text: {fn1['footnote'][:40]}")
check("police" in fn1["sentence"], f"FN1 sentence: {fn1['sentence'][:40]}")

fn2 = next(i for i in items if i["number"] == 2)
check("1983" in fn2["footnote"], f"FN2 text: {fn2['footnote'][:40]}")
check("civil rights" in fn2["sentence"], f"FN2 sentence: {fn2['sentence'][:40]}")


# ── Test 2: authority_splitter splits multi-citation footnotes ──────────────

print("\n── Test 2: authority_splitter ────────────────────")

auths1 = split_authorities(fn1["footnote"])
check(len(auths1) == 1, f"FN1: 1 authority (got {len(auths1)})")

auths2 = split_authorities(fn2["footnote"])
check(len(auths2) == 2, f"FN2: 2 authorities (got {len(auths2)})")
check("1983" in auths2[0], f"FN2 auth1: {auths2[0][:30]}")
check("Brown" in auths2[1], f"FN2 auth2: {auths2[1][:30]}")


# ── Test 3: citation_parser identifies types ────────────────────────────────

print("\n── Test 3: citation_parser ───────────────────────")

p1 = cp.parse(auths1[0])
check(p1.citation_type == cp.CitationType.CASE, f"FN1: CASE (got {p1.citation_type})")

p2a = cp.parse(auths2[0])
check(p2a.citation_type == cp.CitationType.STATUTE, f"FN2 auth1: STATUTE (got {p2a.citation_type})")

p2b = cp.parse(auths2[1])
check(p2b.citation_type == cp.CitationType.CASE, f"FN2 auth2: CASE (got {p2b.citation_type})")


# ── Test 4: _process_one runs the full pipeline (with mocked fetchers) ──────

print("\n── Test 4: _process_one full pipeline (mocked) ───")


def mock_fetch_case(**kwargs):
    return {
        "source": "courtlistener",
        "url": "https://www.courtlistener.com/opinion/12345/",
        "snippet": "The right to remain silent is fundamental.",
        "full_text_available": True,
        "note": None,
    }


def mock_fetch_statute(**kwargs):
    return {
        "source": "uscode_house",
        "url": "https://www.law.cornell.edu/uscode/text/42/1983",
        "snippet": "Every person who, under color of any statute...",
        "full_text_available": True,
        "note": None,
    }


with patch("main.fetch_case", side_effect=mock_fetch_case), \
     patch("main.fetch_statute", side_effect=mock_fetch_statute):

    # Process FN1 (single case)
    result1 = _process_one(fn1)
    check(result1["number"] == 1, "FN1 result number is 1")
    check(len(result1["authorities"]) == 1, f"FN1: 1 authority in result (got {len(result1['authorities'])})")
    auth = result1["authorities"][0]
    check(auth["citation_type"] == "case", f"FN1 auth type: {auth['citation_type']}")
    check(auth["source_name"] == "courtlistener", f"FN1 source: {auth['source_name']}")
    check(auth["source_url"] is not None, "FN1 has source_url")

    # Process FN2 (statute + case)
    result2 = _process_one(fn2)
    check(result2["number"] == 2, "FN2 result number is 2")
    check(len(result2["authorities"]) == 2, f"FN2: 2 authorities in result (got {len(result2['authorities'])})")

    auth2a = result2["authorities"][0]
    check(auth2a["citation_type"] == "statute", f"FN2 auth1 type: {auth2a['citation_type']}")
    check(auth2a["source_name"] == "uscode_house", f"FN2 auth1 source: {auth2a['source_name']}")

    auth2b = result2["authorities"][1]
    check(auth2b["citation_type"] == "case", f"FN2 auth2 type: {auth2b['citation_type']}")
    check(auth2b["source_name"] == "courtlistener", f"FN2 auth2 source: {auth2b['source_name']}")


# ── Test 5: Edge cases ──────────────────────────────────────────────────────

print("\n── Test 5: Edge cases ────────────────────────────")

# Empty docx (no footnotes)
empty_docx = _build_docx([])
items_empty = extract_all(empty_docx)
check(len(items_empty) == 0, "Empty docx → 0 footnotes")

# Bad docx (not a ZIP)
try:
    extract_all(b"not a docx file")
    check(False, "Bad docx should raise ValueError")
except ValueError as e:
    check("bad" in str(e).lower() and "zip" in str(e).lower(), f"Bad docx raises ValueError: {e}")


print("\nAll E2E tests passed.\n")
