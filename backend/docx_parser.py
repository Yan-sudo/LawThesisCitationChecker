"""
Extracts from a .docx file:
  1. Footnotes (id → text)
  2. The main-body sentence where each footnote marker appears

A .docx is a ZIP archive:
  word/document.xml  — body text with <w:footnoteReference> markers
  word/footnotes.xml — footnote content
"""

import io
import re
import zipfile
import xml.etree.ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def extract_all(docx_bytes: bytes) -> list[dict]:
    """
    Returns a list of dicts sorted by footnote number:
      {
        "number":   int,   # footnote number (1-based)
        "footnote": str,   # full footnote text
        "sentence": str,   # sentence in main body citing this footnote
      }
    Raises ValueError if the file is not a valid .docx.
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(docx_bytes))
    except zipfile.BadZipFile:
        raise ValueError("File does not appear to be a valid .docx (bad ZIP).")

    with zf:
        names = zf.namelist()
        doc_xml = zf.read("word/document.xml") if "word/document.xml" in names else None
        fn_xml  = zf.read("word/footnotes.xml") if "word/footnotes.xml" in names else None

    if fn_xml is None:
        return []

    footnotes  = _parse_footnotes(fn_xml)   # {id: text}
    sentences  = _parse_body_sentences(doc_xml) if doc_xml else {}  # {id: sentence}

    results = []
    for fn_id, fn_text in footnotes.items():
        if not fn_text:
            continue
        results.append({
            "number":   fn_id,
            "footnote": fn_text,
            "sentence": sentences.get(fn_id, ""),
        })

    results.sort(key=lambda x: x["number"])
    return results


# ── Footnotes ─────────────────────────────────────────────────────────────────

def _parse_footnotes(xml_data: bytes) -> dict[int, str]:
    root = ET.fromstring(xml_data)
    out  = {}
    for fn in root.findall(f"{{{W}}}footnote"):
        fn_type = fn.get(f"{{{W}}}type", "")
        if fn_type in ("separator", "continuationSeparator", "continuationNotice"):
            continue
        try:
            fn_id = int(fn.get(f"{{{W}}}id", ""))
        except ValueError:
            continue
        if fn_id <= 0:
            continue
        text = "".join(t.text or "" for t in fn.iter(f"{{{W}}}t")).strip()
        out[fn_id] = text
    return out


# ── Body sentence extraction ───────────────────────────────────────────────────

def _parse_body_sentences(xml_data: bytes) -> dict[int, str]:
    """
    Walk every paragraph in the document body.
    For each <w:footnoteReference>, record the sentence that contains it.
    """
    root = ET.fromstring(xml_data)
    body = root.find(f"{{{W}}}body")
    if body is None:
        return {}

    sentences = {}

    for para in body.iter(f"{{{W}}}p"):
        _extract_para_sentences(para, sentences)

    return sentences


def _extract_para_sentences(para: ET.Element, out: dict[int, str]):
    """
    Build a token stream for one paragraph:
      [("text", None), ("", footnote_id), ...]
    Then for each footnote marker, find the enclosing sentence.
    """
    tokens: list[tuple[str, int | None]] = []

    for elem in _walk_runs(para):
        tag = elem.tag
        if tag == f"{{{W}}}t":
            tokens.append((elem.text or "", None))
        elif tag == f"{{{W}}}footnoteReference":
            try:
                fn_id = int(elem.get(f"{{{W}}}id", ""))
                if fn_id > 0:
                    tokens.append(("", fn_id))
            except ValueError:
                pass
        elif tag == f"{{{W}}}br":           # line break → treat as space
            tokens.append((" ", None))
        elif tag == f"{{{W}}}tab":
            tokens.append((" ", None))

    if not tokens:
        return

    # Build full paragraph text and track marker positions
    full_text = ""
    marker_positions: list[tuple[int, int]] = []  # (char_pos, fn_id)
    for text, fn_id in tokens:
        if fn_id is not None:
            marker_positions.append((len(full_text), fn_id))
        full_text += text

    for char_pos, fn_id in marker_positions:
        if fn_id not in out:   # first occurrence wins
            out[fn_id] = _sentence_at(full_text, char_pos)


def _walk_runs(para: ET.Element):
    """Yield leaf elements inside a paragraph, skipping footnote body content."""
    for child in para:
        tag = child.tag
        # Skip footnote/endnote *content* elements (they appear in footnotes.xml, not here,
        # but be defensive)
        if tag in (f"{{{W}}}footnote", f"{{{W}}}endnote"):
            continue
        # Recurse into runs and hyperlinks
        if tag in (f"{{{W}}}r", f"{{{W}}}hyperlink", f"{{{W}}}ins", f"{{{W}}}del",
                   f"{{{W}}}smartTag", f"{{{W}}}sdt"):
            yield from _walk_runs(child)
        else:
            yield child


def _sentence_at(text: str, pos: int) -> str:
    """Return the complete sentence in `text` that contains character position `pos`."""
    sentence_end = re.compile(r'(?<=[.!?])\s')
    boundaries = [0] + [m.end() for m in sentence_end.finditer(text)] + [len(text)]

    for i in range(len(boundaries) - 1):
        start, end = boundaries[i], boundaries[i + 1]
        if start <= pos <= end:
            return text[start:end].strip()

    return text.strip()
