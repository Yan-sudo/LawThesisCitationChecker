"""
Law Citation Checker — local web server.

Usage:
    python3 main.py              # http://localhost:8000
    python3 main.py --port 9000

Open http://localhost:8000 in your browser, upload a .docx file,
and review Bluebook citation results for every footnote.
"""

from __future__ import annotations

import cgi
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import citation_parser as cp
import bluebook
from docx_parser import extract_footnotes
from fetchers import fetch_case, fetch_statute, fetch_article, fetch_book

HERE = os.path.dirname(os.path.abspath(__file__))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress per-request noise; errors still print via log_error

    # ── CORS ──────────────────────────────────────────────────────────────────

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── GET ───────────────────────────────────────────────────────────────────

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._serve_file(os.path.join(HERE, "index.html"), "text/html; charset=utf-8")
        elif self.path == "/health":
            self._json(200, {"status": "ok"})
        else:
            self._json(404, {"error": "not found"})

    # ── POST ──────────────────────────────────────────────────────────────────

    def do_POST(self):
        if self.path == "/upload":
            self._handle_upload()
        elif self.path == "/check":
            self._handle_check()
        else:
            self._json(404, {"error": "not found"})

    # ── /upload — parse .docx and check all footnotes ─────────────────────────

    def _handle_upload(self):
        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype:
            self._json(400, {"error": "Expected multipart/form-data"})
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": ctype,
            },
        )

        file_item = form.get("file")
        if file_item is None or not hasattr(file_item, "file"):
            self._json(400, {"error": "No file field in upload"})
            return

        docx_bytes = file_item.file.read()
        filename   = getattr(file_item, "filename", "upload.docx") or "upload.docx"

        try:
            footnotes = extract_footnotes(docx_bytes)
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
            return

        if not footnotes:
            self._json(200, {
                "filename": filename,
                "footnote_count": 0,
                "results": [],
                "message": "No footnotes found in this document.",
            })
            return

        # Check all footnotes in parallel
        results: list[dict | None] = [None] * len(footnotes)

        def worker(idx: int, fn: dict):
            results[idx] = _check_one(fn["text"], fn["number"])

        threads = [
            threading.Thread(target=worker, args=(i, fn), daemon=True)
            for i, fn in enumerate(footnotes)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self._json(200, {
            "filename": filename,
            "footnote_count": len(footnotes),
            "results": results,
        })

    # ── /check — single citation (kept for API use) ────────────────────────────

    def _handle_check(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            self._json(400, {"error": f"bad JSON: {exc}"})
            return
        result = _check_one(payload.get("text", ""), payload.get("footnote_number"))
        self._json(200, result)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _serve_file(self, path: str, content_type: str):
        try:
            with open(path, "rb") as f:
                data = f.read()
        except FileNotFoundError:
            self._json(404, {"error": f"file not found: {path}"})
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


# ── Citation check logic ──────────────────────────────────────────────────────

def _check_one(text: str, footnote_number: Any) -> dict:
    parsed      = cp.parse(text)
    bb          = bluebook.validate_and_format(parsed)
    source_info = _fetch_source(parsed)

    return {
        "footnote_number": footnote_number,
        "raw":             text,
        "citation_type":   parsed.citation_type,
        "bluebook_valid":  bb["is_valid"],
        "bluebook_issues": bb["issues"],
        "bluebook_suggested": bb["suggested"],
        "source_name":     source_info.get("source"),
        "source_url":      source_info.get("url"),
        "source_snippet":  source_info.get("snippet"),
        "full_text_available": source_info.get("full_text_available", False),
        "source_note":     source_info.get("note"),
    }


def _fetch_source(parsed: cp.ParsedCitation) -> dict:
    try:
        if parsed.citation_type == cp.CitationType.CASE:
            return fetch_case(
                parties=parsed.parties or "",
                volume=parsed.volume or "",
                reporter=parsed.reporter or "",
                page=parsed.page or "",
                year=parsed.year,
                pincite=parsed.pincite,
            )
        if parsed.citation_type == cp.CitationType.STATUTE:
            return fetch_statute(
                title=parsed.title or "",
                code=parsed.code or "U.S.C.",
                section=parsed.section or "",
                year=parsed.year,
            )
        if parsed.citation_type == cp.CitationType.ARTICLE:
            return fetch_article(
                authors=parsed.authors or "",
                title=parsed.article_title or "",
                volume=parsed.volume or "",
                journal=parsed.journal or "",
                page=parsed.page or "",
                pincite=parsed.pincite,
                year=parsed.year,
            )
        if parsed.citation_type == cp.CitationType.BOOK:
            return fetch_book(
                authors=parsed.authors or "",
                title=parsed.book_title or "",
                page=parsed.page,
                year=parsed.year,
                edition=parsed.edition,
            )
    except Exception as exc:
        return {
            "source": "error", "url": None, "snippet": None,
            "full_text_available": False,
            "note": f"Unexpected error fetching source: {exc}",
        }

    return {
        "source": "unknown_type", "url": None, "snippet": None,
        "full_text_available": False,
        "note": "Citation type could not be identified — Bluebook check only.",
    }


# ── Entry point ───────────────────────────────────────────────────────────────

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
