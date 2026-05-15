"""
Extracts footnote text from a .docx file without any third-party libraries.
A .docx is a ZIP archive; footnotes live in word/footnotes.xml.
"""

import io
import zipfile
import xml.etree.ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def extract_footnotes(docx_bytes: bytes) -> list[dict]:
    """
    Returns a list of {"number": int, "text": str} dicts, sorted by footnote number.
    Skips Word's internal separator pseudo-footnotes (ids -1 and 0).
    """
    try:
        with zipfile.ZipFile(io.BytesIO(docx_bytes)) as z:
            if "word/footnotes.xml" not in z.namelist():
                return []
            xml_data = z.read("word/footnotes.xml")
    except zipfile.BadZipFile:
        raise ValueError("File does not appear to be a valid .docx (bad ZIP).")

    root = ET.fromstring(xml_data)
    results = []

    for fn in root.findall(f"{{{W}}}footnote"):
        fn_type = fn.get(f"{{{W}}}type", "")
        fn_id   = fn.get(f"{{{W}}}id", "")

        # Skip Word's internal separator footnotes
        if fn_type in ("separator", "continuationSeparator", "continuationNotice"):
            continue
        try:
            fn_num = int(fn_id)
        except ValueError:
            continue
        if fn_num <= 0:
            continue

        # Concatenate all w:t text nodes, preserving spaces marked xml:space="preserve"
        parts = []
        for t in fn.iter(f"{{{W}}}t"):
            parts.append(t.text or "")
        text = "".join(parts).strip()

        if text:
            results.append({"number": fn_num, "text": text})

    results.sort(key=lambda x: x["number"])
    return results
