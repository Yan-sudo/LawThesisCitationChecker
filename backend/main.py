"""
Law Citation Checker — local web server.

Usage:
    python3 main.py              # http://localhost:8000
    python3 main.py --port 9000

Open http://localhost:8000, enter your Gemini API key, upload a .docx,
and the tool will check every footnote for citation accuracy.
"""

from __future__ import annotations

import email.parser
import email.policy
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import citation_parser as cp
from docx_parser import extract_all
from fetchers import fetch_case, fetch_statute, fetch_article, fetch_book
from gemini import check_citation

HERE = os.path.dirname(os.path.abspath(__file__))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._serve_file(os.path.join(HERE, "index.html"), "text/html; charset=utf-8")
        elif self.path == "/health":
            self._json(200, {"status": "ok"})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/upload":
            self._handle_upload()
        else:
            self._json(404, {"error": "not found"})

    # ── /upload ───────────────────────────────────────────────────────────────

    def _handle_upload(self):
        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype:
            self._json(400, {"error": "Expected multipart/form-data"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        fields = _parse_multipart(ctype, body)

        docx_bytes = fields.get("file")
        if not docx_bytes:
            self._json(400, {"error": "No file field found in upload"})
            return

        filename  = fields.get("_filename", "upload.docx")
        api_key   = fields.get("api_key", b"").decode(errors="replace").strip() \
                    if isinstance(fields.get("api_key"), bytes) else fields.get("api_key", "")

        try:
            items = extract_all(docx_bytes)
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
            return

        if not items:
            self._json(200, {
                "filename": filename,
                "footnote_count": 0,
                "results": [],
                "message": "No footnotes found in this document.",
            })
            return

        results: list[dict | None] = [None] * len(items)

        def worker(idx: int, item: dict):
            results[idx] = _process_one(item, api_key)

        threads = [
            threading.Thread(target=worker, args=(i, it), daemon=True)
            for i, it in enumerate(items)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self._json(200, {
            "filename": filename,
            "footnote_count": len(items),
            "results": results,
        })

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _serve_file(self, path: str, content_type: str):
        try:
            with open(path, "rb") as f:
                data = f.read()
        except FileNotFoundError:
            self._json(404, {"error": f"not found: {path}"})
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _json(self, status: int, data: Any):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)


# ── Per-citation processing ────────────────────────────────────────────────────

def _process_one(item: dict, api_key: str) -> dict:
    footnote_text = item["footnote"]
    sentence      = item["sentence"]
    number        = item["number"]

    # Fetch source
    parsed      = cp.parse(footnote_text)
    source_info = _fetch_source(parsed)

    source_text = source_info.get("snippet")
    source_name = source_info.get("source")
    source_url  = source_info.get("url")
    source_note = source_info.get("note")

    # Gemini accuracy check
    llm = check_citation(
        api_key      = api_key,
        main_sentence= sentence,
        footnote_text= footnote_text,
        source_text  = source_text,
        source_name  = source_name,
    )

    return {
        "number":        number,
        "footnote":      footnote_text,
        "sentence":      sentence,
        "citation_type": parsed.citation_type,
        "source_name":   source_name,
        "source_url":    source_url,
        "source_note":   source_note,
        "source_snippet":source_text,
        "llm":           llm,
    }


# ── Source fetching ────────────────────────────────────────────────────────────

def _fetch_source(parsed: cp.ParsedCitation) -> dict:
    try:
        if parsed.citation_type == cp.CitationType.CASE:
            return fetch_case(
                parties  = parsed.parties or "",
                volume   = parsed.volume or "",
                reporter = parsed.reporter or "",
                page     = parsed.page or "",
                year     = parsed.year,
                pincite  = parsed.pincite,
            )
        if parsed.citation_type == cp.CitationType.STATUTE:
            return fetch_statute(
                title   = parsed.title or "",
                code    = parsed.code or "U.S.C.",
                section = parsed.section or "",
                year    = parsed.year,
            )
        if parsed.citation_type == cp.CitationType.ARTICLE:
            return fetch_article(
                authors = parsed.authors or "",
                title   = parsed.article_title or "",
                volume  = parsed.volume or "",
                journal = parsed.journal or "",
                page    = parsed.page or "",
                pincite = parsed.pincite,
                year    = parsed.year,
            )
        if parsed.citation_type == cp.CitationType.BOOK:
            return fetch_book(
                authors = parsed.authors or "",
                title   = parsed.book_title or "",
                page    = parsed.page,
                year    = parsed.year,
                edition = parsed.edition,
            )
    except Exception as exc:
        return {
            "source": "error", "url": None, "snippet": None,
            "full_text_available": False,
            "note": f"Source lookup error: {exc}",
        }

    return {
        "source": "unrecognised", "url": None, "snippet": None,
        "full_text_available": False,
        "note": (
            "Citation format not automatically recognised. "
            "Gemini will still evaluate accuracy based on the footnote text alone, "
            "but cannot compare against a retrieved source."
        ),
    }


# ── Multipart parser ───────────────────────────────────────────────────────────

def _parse_multipart(content_type: str, body: bytes) -> dict[str, Any]:
    """Parse multipart/form-data. Returns dict of field_name → bytes (or str for text fields)."""
    raw = f"Content-Type: {content_type}\r\n\r\n".encode() + body
    msg = email.parser.BytesParser(policy=email.policy.compat32).parsebytes(raw)
    fields: dict[str, Any] = {}

    for part in msg.get_payload():
        disposition = part.get("Content-Disposition", "")
        name = ""
        filename = ""
        for token in disposition.split(";"):
            token = token.strip()
            if token.lower().startswith("name="):
                name = token.split("=", 1)[-1].strip().strip('"')
            elif token.lower().startswith("filename="):
                filename = token.split("=", 1)[-1].strip().strip('"')

        if not name:
            continue
        payload = part.get_payload(decode=True)
        if filename:
            fields["_filename"] = filename
        fields[name] = payload

    return fields


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), Handler)
    print(f"\n  Law Citation Checker")
    print(f"  Open → http://localhost:{args.port}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
