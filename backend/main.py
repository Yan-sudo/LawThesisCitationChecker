"""
Standalone HTTP server for the Law Citation Checker.
Uses Python's built-in http.server — no external web framework required.

Usage:
    python main.py            # runs on http://localhost:8000
    python main.py --port 9000
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import citation_parser as cp
import bluebook
from fetchers import fetch_case, fetch_statute, fetch_article, fetch_book

# ── Routing table ─────────────────────────────────────────────────────────────

ROUTES: dict[tuple[str, str], Any] = {}


def route(method: str, path: str):
    def decorator(fn):
        ROUTES[(method.upper(), path)] = fn
        return fn
    return decorator


# ── Handler ───────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Keep output clean — only log errors
        pass

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        fn = ROUTES.get(("GET", self.path))
        if fn is None:
            self._send(404, {"error": "not found"})
            return
        result = fn()
        self._send(200, result)

    def do_POST(self):
        fn = ROUTES.get(("POST", self.path))
        if fn is None:
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            self._send(400, {"error": f"bad JSON: {exc}"})
            return
        result = fn(payload)
        self._send(200, result)

    def _send(self, status: int, data: Any):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@route("GET", "/health")
def health():
    return {"status": "ok"}


@route("POST", "/check")
def check(payload: dict) -> dict:
    text   = payload.get("text", "")
    fn_num = payload.get("footnote_number")
    return _check_one(text, fn_num)


@route("POST", "/check-batch")
def check_batch(payload: dict) -> list:
    citations = payload.get("citations", [])
    results = []
    threads = []
    bucket: list[dict | None] = [None] * len(citations)

    def worker(idx: int, item: dict):
        bucket[idx] = _check_one(item.get("text", ""), item.get("footnote_number"))

    for i, item in enumerate(citations):
        t = threading.Thread(target=worker, args=(i, item), daemon=True)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    return bucket  # type: ignore[return-value]


# ── Core check logic ──────────────────────────────────────────────────────────

def _check_one(text: str, footnote_number) -> dict:
    parsed      = cp.parse(text)
    bb          = bluebook.validate_and_format(parsed)
    source_info = _fetch_source(parsed)

    return {
        "footnote_number": footnote_number,
        "raw": text,
        "citation_type": parsed.citation_type,
        "bluebook_valid": bb["is_valid"],
        "bluebook_issues": bb["issues"],
        "bluebook_suggested": bb["suggested"],
        "source_name": source_info.get("source"),
        "source_url": source_info.get("url"),
        "source_snippet": source_info.get("snippet"),
        "full_text_available": source_info.get("full_text_available", False),
        "source_note": source_info.get("note"),
        "parsed": _serialise(parsed),
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
            "source": "error",
            "url": None,
            "snippet": None,
            "full_text_available": False,
            "note": f"Unexpected error fetching source: {exc}",
        }

    return {
        "source": "unknown_type",
        "url": None,
        "snippet": None,
        "full_text_available": False,
        "note": "Citation type could not be identified — Bluebook check only.",
    }


def _serialise(p: cp.ParsedCitation) -> dict:
    return {
        k: v for k, v in p.__dict__.items()
        if v is not None and k not in ("raw", "errors")
    }


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), Handler)
    print(f"Citation Checker backend running on http://localhost:{args.port}")
    print("  GET  /health")
    print("  POST /check")
    print("  POST /check-batch")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
