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
import re
import ssl
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Optional

import citation_parser as cp
from authority_splitter import split_authorities
from docx_parser import extract_all
from fetchers import fetch_case, fetch_statute, fetch_article, fetch_book

HERE = os.path.dirname(os.path.abspath(__file__))
# Icons referenced by manifest.xml live in the Word add-in's asset folder.
ASSETS_DIR = os.path.normpath(os.path.join(HERE, "..", "taskpane", "assets"))


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
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html", "/taskpane.html"):
            self._serve_file(os.path.join(HERE, "index.html"), "text/html; charset=utf-8")
        elif path == "/health":
            self._json(200, {"status": "ok"})
        elif path.startswith("/assets/"):
            self._handle_asset(path)
        elif self.path.startswith("/fetch-source"):
            self._handle_fetch_source()
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/upload":
            self._handle_upload()
        elif self.path == "/check":
            self._handle_check()
        else:
            self._json(404, {"error": "not found"})

    # ── /assets/<icon> — icons referenced by the Word manifest ─────────────────

    def _handle_asset(self, path: str):
        name = os.path.basename(path)
        if not re.match(r"^[\w.-]+\.(png|ico|svg)$", name):
            self._json(404, {"error": "not found"})
            return
        fp = os.path.join(ASSETS_DIR, name)
        if not os.path.isfile(fp):
            self._json(404, {"error": "not found"})
            return
        ctype = ("image/png" if name.endswith(".png")
                 else "image/x-icon" if name.endswith(".ico")
                 else "image/svg+xml")
        self._serve_file(fp, ctype)

    # ── /check — accuracy check for footnotes read live from a Word document ────
    # The Word add-in reads footnotes via Office.js (no .docx upload), so this
    # endpoint takes footnote text as JSON and returns the same per-footnote
    # shape as /upload. Gemini accuracy checks still run in the browser.

    def _handle_check(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._json(400, {"error": "Invalid JSON body"})
            return

        filename = payload.get("filename") or "Word document"
        raw = payload.get("footnotes") or []
        items: list[dict] = []
        for i, fn in enumerate(raw):
            if not isinstance(fn, dict):
                continue
            text = (fn.get("text") or "").strip()
            if not text:
                continue
            try:
                number = int(fn.get("number"))
            except (TypeError, ValueError):
                number = i + 1
            items.append({
                "number":   number,
                "footnote": text,
                "sentence": (fn.get("sentence") or "").strip(),
            })

        if not items:
            self._json(200, {
                "filename": filename,
                "footnote_count": 0,
                "results": [],
                "message": "No footnotes found in this document.",
            })
            return

        note_index = _build_note_index(items)
        results: list[dict | None] = [None] * len(items)

        def worker(idx: int, item: dict):
            results[idx] = _process_one(item, note_index)

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

        filename = fields.get("_filename", "upload.docx")

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

        # Index every footnote's authorities up front so "supra note N" short
        # forms can be resolved back to the full citation they point to.
        note_index = _build_note_index(items)

        def worker(idx: int, item: dict):
            results[idx] = _process_one(item, note_index)

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

    # ── /fetch-source ─────────────────────────────────────────────────────────
    # Downloads a source document (typically a PDF on SSRN, ResearchGate,
    # CourtListener, etc.) server-side and hands the raw bytes to the browser,
    # which extracts text with pdf.js. Gemini's web-search tool can locate
    # these pages but cannot click through download walls or render PDF
    # binaries, so this gives the checker a way to actually read the source.

    _FETCH_MAX_BYTES = 30 * 1024 * 1024

    def _handle_fetch_source(self):
        qs  = urllib.parse.urlparse(self.path).query
        url = (urllib.parse.parse_qs(qs).get("url") or [None])[0]
        if not url or not re.match(r"^https?://", url, re.I):
            self._json(400, {"error": "Missing or invalid url parameter"})
            return

        req = urllib.request.Request(url, headers={
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/124.0 Safari/537.36"),
            "Accept": "application/pdf,text/html,*/*",
        })
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                content_type = resp.headers.get("Content-Type", "application/octet-stream")
                data = resp.read(self._FETCH_MAX_BYTES + 1)
        except urllib.error.HTTPError as exc:
            self._json(exc.code, {"error": f"Source returned HTTP {exc.code}"})
            return
        except Exception as exc:
            self._json(502, {"error": f"Could not fetch source: {exc}"})
            return

        if len(data) > self._FETCH_MAX_BYTES:
            self._json(413, {"error": "Source file too large"})
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(data)

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
        self.send_header("Cache-Control", "no-store")
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


# ── Per-footnote processing (source fetch only — Gemini runs in browser) ──────

def _process_one(item: dict, note_index: dict | None = None) -> dict:
    """
    Split footnote into individual authorities and fetch each source.
    Gemini accuracy checks are performed client-side using the user's key.
    """
    footnote_text = item["footnote"]
    sentence      = item["sentence"]
    number        = item["number"]

    authority_texts = split_authorities(footnote_text)
    auth_results: list[dict | None] = [None] * len(authority_texts)

    def fetch_authority(idx: int, auth_text: str):
        parsed      = cp.parse(auth_text)
        source_info = _fetch_source(parsed, note_index)
        auth_results[idx] = {
            "text":               auth_text,
            "citation_type":      parsed.citation_type,
            "bluebook_rule":      parsed.bluebook_rule,
            "bluebook_rule_desc": parsed.bluebook_rule_desc,
            "source_name":        source_info.get("source"),
            "source_url":         source_info.get("url"),
            "source_pdf_url":     source_info.get("pdf_url"),
            "source_note":        source_info.get("note"),
            "source_snippet":     source_info.get("snippet"),
            "source_full_text_available": bool(source_info.get("full_text_available")),
        }

    threads = [
        threading.Thread(target=fetch_authority, args=(i, t), daemon=True)
        for i, t in enumerate(authority_texts)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return {
        "number":      number,
        "footnote":    footnote_text,
        "sentence":    sentence,
        "authorities": auth_results,
    }


# ── Supra / cross-reference resolution ──────────────────────────────────────────

# Citation types that point to a real, fetchable external source.
_RESOLVABLE_TYPES = {
    cp.CitationType.CASE, cp.CitationType.SHORT_CASE, cp.CitationType.STATUTE,
    cp.CitationType.ARTICLE, cp.CitationType.BOOK, cp.CitationType.CONSTITUTION,
    cp.CitationType.RESTATEMENT, cp.CitationType.LEGISLATIVE,
    cp.CitationType.ADMINISTRATIVE,
}


def _build_note_index(items: list[dict]) -> dict[int, list[cp.ParsedCitation]]:
    """Map footnote number → parsed authorities, for resolving 'supra note N'."""
    index: dict[int, list[cp.ParsedCitation]] = {}
    for it in items:
        try:
            num = int(it.get("number"))
        except (TypeError, ValueError):
            continue
        parsed_list = []
        for atext in split_authorities(it.get("footnote", "")):
            try:
                parsed_list.append(cp.parse(atext))
            except Exception:
                continue
        index[num] = parsed_list
    return index


def _resolve_supra(parsed: cp.ParsedCitation,
                   note_index: dict | None) -> Optional[cp.ParsedCitation]:
    """Return the full citation a 'supra note N' short form refers to, or None."""
    if not note_index or not parsed.supra_note:
        return None
    try:
        note_num = int(parsed.supra_note)
    except (TypeError, ValueError):
        return None
    resolvable = [c for c in note_index.get(note_num, [])
                  if c.citation_type in _RESOLVABLE_TYPES]
    if not resolvable:
        return None
    author = (parsed.supra_author or "").strip()
    author_tokens = [t.lower() for t in re.findall(r"[A-Za-z]{3,}", author)]
    if author_tokens:
        for c in resolvable:
            rl = c.raw.lower()
            if any(t in rl for t in author_tokens):
                return c
    # No author given (or no match): unambiguous only if the note has one source.
    if len(resolvable) == 1:
        return resolvable[0]
    return None


# ── Source fetching ────────────────────────────────────────────────────────────

def _fetch_source(parsed: cp.ParsedCitation, note_index: dict | None = None) -> dict:
    try:
        # ── Non-citation prose — nothing to fetch or verify ────────────────
        if parsed.citation_type == cp.CitationType.NON_CITATION:
            return {
                "source": "non_citation",
                "url": None,
                "snippet": None,
                "full_text_available": False,
                "note": (
                    "This footnote text is the author's own analysis, calculation, "
                    "or editorial note — not a citation to an external source. "
                    "Skipped (no source to verify)."
                ),
            }

        # ── Types with external source lookup ──────────────────────────────
        if parsed.citation_type in (cp.CitationType.CASE, cp.CitationType.SHORT_CASE):
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

        # ── Types with well-known public URLs ──────────────────────────────
        if parsed.citation_type == cp.CitationType.CONSTITUTION:
            is_us = (parsed.title or "").upper().startswith("U.S")
            url = (
                "https://constitution.congress.gov/"
                if is_us else
                "https://www.law.cornell.edu/constitution"
            )
            return {
                "source": "constitution",
                "url": url,
                "snippet": None,
                "full_text_available": False,
                "note": (
                    "U.S. Constitution — full text at constitution.congress.gov. "
                    "Gemini will search for the specific provision."
                    if is_us else
                    f"{parsed.title} Constitution — Gemini will search for the full text."
                ),
            }

        if parsed.citation_type == cp.CitationType.LEGISLATIVE:
            return {
                "source": "legislative",
                "url": "https://www.congress.gov/",
                "snippet": None,
                "full_text_available": False,
                "note": (
                    "Legislative material (bill, report, or record). "
                    "Search congress.gov for the full text. "
                    "Gemini will attempt to locate the specific document."
                ),
            }

        # ── Short-form citations — accuracy depends on the cited prior source ──
        if parsed.citation_type == cp.CitationType.ID:
            pin = f" at {parsed.pincite}" if parsed.pincite else ""
            return {
                "source": "id_citation",
                "url": None,
                "snippet": None,
                "full_text_available": False,
                "note": (
                    f"Id.{pin} — short form referring to the immediately preceding authority "
                    "(Bluebook Rule 4.1). Accuracy depends on that prior source."
                ),
            }

        if parsed.citation_type == cp.CitationType.SUPRA:
            # Try to resolve the cross-reference to the full citation it points
            # to, then fetch that source so the short form can be verified.
            resolved = _resolve_supra(parsed, note_index)
            if resolved is not None:
                info = dict(_fetch_source(resolved, note_index))
                ref = f"supra note {parsed.supra_note}" if parsed.supra_note else "supra"
                info["note"] = (
                    f"Resolved “{parsed.raw}” → {resolved.raw[:90]} (via {ref}). "
                    + (info.get("note") or "")
                ).strip()
                info["resolved_from"] = resolved.raw
                return info

            ref = f"note {parsed.supra_note}" if parsed.supra_note else "a prior citation"
            who = f"{parsed.supra_author}, " if parsed.supra_author else ""
            return {
                "source": "supra_citation",
                "url": None,
                "snippet": None,
                "full_text_available": False,
                "note": (
                    f"{who}supra {ref} — cross-reference to an earlier citation "
                    "(Bluebook Rule 4.2). The referenced note could not be resolved "
                    "automatically; accuracy depends on the source cited there."
                ),
            }

        if parsed.citation_type == cp.CitationType.ADMINISTRATIVE:
            return {
                "source": "administrative",
                "url": "https://www.cftc.gov/LawRegulation/EnforcementActions/index.htm",
                "snippet": None,
                "full_text_available": False,
                "note": (
                    "Administrative agency order (Bluebook Rule 14.3). "
                    "Gemini will search for the specific docket or release number."
                ),
            }

        if parsed.citation_type == cp.CitationType.RESTATEMENT:
            return {
                "source": "restatement",
                "url": "https://www.ali.org/publications/",
                "snippet": None,
                "full_text_available": False,
                "note": (
                    "Restatement or Model Code (Bluebook Rule 12.9.4). "
                    "Full text available via Westlaw, LexisNexis, or the ALI website. "
                    "Gemini will search for the specific section."
                ),
            }

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
            "Citation format not matched to any Bluebook rule pattern. "
            "Gemini will use Google Search to find the source directly."
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

    default_certs = os.path.expanduser("~/.office-addin-dev-certs")
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--certfile", default=os.path.join(default_certs, "localhost.crt"),
                        help="TLS certificate (PEM). HTTPS is required by Word add-ins.")
    parser.add_argument("--keyfile", default=os.path.join(default_certs, "localhost.key"),
                        help="TLS private key (PEM).")
    parser.add_argument("--http", action="store_true",
                        help="Force plain HTTP even if a certificate is present.")
    args = parser.parse_args()

    use_https = (not args.http
                 and os.path.isfile(args.certfile)
                 and os.path.isfile(args.keyfile))

    try:
        server = HTTPServer(("0.0.0.0", args.port), Handler)
    except OSError as exc:
        if exc.errno in (48, 98):  # EADDRINUSE (macOS 48 / Linux 98)
            print(f"\n  Port {args.port} is already in use.")
            print(f"  The checker is probably already running — open "
                  f"https://localhost:{args.port} and switch to Word.")
            print(f"  To restart cleanly, free the port first:")
            print(f"      lsof -ti tcp:{args.port} | xargs kill\n")
            raise SystemExit(1)
        raise

    scheme = "http"
    if use_https:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=args.certfile, keyfile=args.keyfile)
        server.socket = ctx.wrap_socket(server.socket, server_side=True)
        scheme = "https"

    print(f"\n  Law Citation Checker")
    print(f"  Open → {scheme}://localhost:{args.port}")
    if use_https:
        print(f"  (HTTPS — Word add-in task pane will load from this address)")
    else:
        print(f"  (HTTP — run setup-mac.command first to enable HTTPS for the Word add-in)")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
