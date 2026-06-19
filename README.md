# LexCheck — Law Citation Accuracy Checker

A local tool that checks whether every cited authority in a law review paper actually supports the proposition it is cited for. It splits multi-authority footnotes into individual citations, fetches the underlying sources, and uses **Gemini with Google Search grounding** to judge each citation's accuracy.

The same code runs two ways:

- **Browser app** — start the local server, open it in your browser, and upload a `.docx`.
- **Word add-in (macOS)** — a task pane inside Word that reads footnotes straight from the open document, with no upload. See **[WORD-PLUGIN-SETUP.md](WORD-PLUGIN-SETUP.md)** for the one-step Mac installer.

---

## What it does

For each authority in each footnote it:

- Identifies the citation type and the Bluebook rule that applies
- Fetches the source from free public databases where possible
- Uses **Gemini with Google Search** to find and read the source online
- Reports what it actually compared against (original source / secondary source / footnote text only)
- Returns a verdict: **Supports** / **Does not support** / **Questionable** / **Cannot verify**
- Checks parenthetical accuracy and pincite accuracy
- Extracts a verbatim relevant passage from the source

---

## Architecture

```
backend/
  main.py               ← stdlib HTTP/HTTPS server. Serves the UI plus:
                            /upload (browser .docx), /check (Word footnotes),
                            /fetch-source (PDF proxy), /assets, /health
  docx_parser.py        ← extracts footnotes + body sentences from .docx (browser mode)
  citation_parser.py    ← Bluebook citation type detection (Rules 4, 10–16)
  authority_splitter.py ← splits multi-authority footnotes; handles Compare/with
  fetchers/             ← CourtListener, USCODE, eCFR, CrossRef, OpenAlex, Google Books
  index.html            ← single-file UI; Office-aware, so the same page works
                            in a browser and as a Word task pane

manifest.xml            ← Office add-in manifest (Word task pane + Home-ribbon button)
taskpane/assets/        ← icons referenced by the manifest
setup-mac.command       ← one-step macOS installer (HTTPS cert + sideload + cache clear)
run.command             ← double-click launcher for the local server (macOS)
```

**Gemini runs entirely in the front end** — in your browser, or in Word's task-pane webview. Your API key is never sent to the local Python server; it goes directly to Google's API. The server only identifies sources and fetches free public metadata.

**HTTPS:** Word add-ins must load over trusted HTTPS, so `main.py` serves HTTPS automatically when a certificate is present (`~/.office-addin-dev-certs/localhost.{crt,key}`, created by `setup-mac.command`) and falls back to plain HTTP otherwise. The browser app works fine over either.

**Free data sources:**

| Citation type | Source |
|---|---|
| Court cases | [CourtListener](https://www.courtlistener.com/api/) (free, no key) |
| Federal statutes (U.S.C.) | [U.S. House USCODE](https://uscode.house.gov/) |
| Federal regulations (C.F.R.) | [eCFR](https://www.ecfr.gov/) |
| Journal articles | [CrossRef](https://api.crossref.org/) + [OpenAlex](https://openalex.org/) |
| Books | [Google Books](https://books.google.com/) |
| Everything else | Gemini Google Search grounding |

---

## Prerequisites

- **Python 3.10+** — uses only the standard library; no `pip install` needed
- A free **Gemini API key** — get one at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **Browser mode:** a `.docx` file with footnotes
- **Word add-in (macOS):** Microsoft Word (Microsoft 365 / 2021 or newer) — footnotes are read live via Office.js, so no upload is needed

---

## Setup

### Get the code

```bash
git clone https://github.com/yan-sudo/lawthesiscitationchecker.git
cd lawthesiscitationchecker
```

### Option A — Browser app

```bash
cd backend
python3 main.py
```

Open **http://localhost:8000** in your browser:

1. Paste your Gemini API key into the **Step 1** field (tick *Remember key* to save it in your browser's local storage).
2. Drop or select your `.docx` file in the **Step 2** field.
3. Click **Check Citations**.

For the browser app that's it — no Node.js, no npm, no Word sideloading, no certificates. To use a different port: `python3 main.py --port 9000`.

### Option B — Word add-in (macOS)

1. Double-click **`setup-mac.command`** once. It creates a trusted HTTPS certificate, installs the add-in into Word, and clears Word's cache. (You'll be asked for your Mac password to trust the certificate.)
2. Double-click **`run.command`** to start the local server — leave it running.
3. In Word, open the **Home** tab → **Citation Checker** → paste your key → **Scan & check this document**.

Full walkthrough and troubleshooting: **[WORD-PLUGIN-SETUP.md](WORD-PLUGIN-SETUP.md)**.

---

## Usage

After you start a check (**Check Citations** in the browser, or **Scan & check this document** in Word):

1. Footnotes are collected — extracted from the uploaded `.docx` in the browser, or read live from the open document via Office.js in Word.
2. Source metadata is fetched from free databases (CourtListener, USCODE, etc.).
3. Result cards appear immediately. Each footnote expands into authority sub-cards.
4. Gemini checks each authority in the background (up to 3 in parallel with automatic retry on rate limits).

Each authority card shows:

| Field | Meaning |
|---|---|
| **Bluebook rule badge** | Which rule was matched (e.g. *Rule 10 · Cases — full citation*) |
| **Compared against** | Green = original source read · Amber = secondary source · Red = source not found |
| **Supports proposition?** | Supports / Does not support / Questionable / Cannot verify |
| **Parenthetical accurate?** | Whether the parenthetical description matches the source |
| **Pincite accurate?** | Whether the page/section number points to the relevant passage |
| **Relevant passage** | Verbatim quote from what Gemini read |
| **Pages read by Gemini** | Clickable links to every page Gemini consulted via Google Search |

Use the **filter bar** to show only Issues, Questionable, Supported, or Unverified authorities. Use **Export** to save the full results as JSON.

---

## Supported citation patterns (Bluebook 21st ed.)

### Cases — Rule 10
```
Miranda v. Arizona, 384 U.S. 436 (1966)
Brown v. Bd. of Educ., 347 U.S. 483, 495 (1954)
Miranda, 384 U.S. at 444                              ← short form (Rule 10)
```

### Statutes — Rule 12
```
42 U.S.C. § 1983 (2018)
15 U.S.C. §§ 1–7 (2018)
29 C.F.R. § 541.100 (2023)
```

### Constitutions — Rule 11
```
U.S. Const. amend. XIV, § 1
U.S. Const. art. I, § 8, cl. 3
Cal. Const. art. I, § 7
```

### Restatements & Model Codes — Rule 12.9.4
```
Restatement (Second) of Contracts § 71 (1981)
Restatement (Third) of Torts § 1 (2010)
Model Penal Code § 2.02 (Official Draft 1962)
Uniform Commercial Code § 2-207
```

### Legislative & Executive Materials — Rule 13
```
H.R. 1234, 117th Cong. § 2 (2021)
S. Rep. No. 103-7, at 10 (1993)
H.R. Rep. No. 104-369, at 5 (1995)
Exec. Order No. 13,228, 66 Fed. Reg. 51,812 (Oct. 9, 2001)
148 Cong. Rec. S1234 (daily ed. Feb. 14, 2002)
```

### Journal articles — Rule 16
```
Katharine T. Bartlett, Feminist Legal Methods, 103 Harv. L. Rev. 829 (1990)
Richard A. Posner, The Law and Economics of Contract Interpretation, 83 Tex. L. Rev. 1581, 1600 (2005)
```

### Books — Rule 15
```
William L. Prosser, Handbook of the Law of Torts 23 (4th ed. 1971)
Laurence H. Tribe, American Constitutional Law 567 (2d ed. 1988)
```

### Short forms — Rules 4.1 & 4.2
```
Id.
Id. at 445
Smith, supra note 5, at 42
supra note 5
infra note 10
```

### Multi-authority footnotes (Rule 1.2 signals)
The splitter handles semicolon-separated lists and `Compare X, with Y` constructions. Introductory signals (`See`, `See also`, `But see`, `Cf.`, `E.g.,`, `Accord`, `Contra`) and `[hereinafter ...]` annotations are stripped automatically before each authority is parsed and checked individually.

---

## Extending

- **Add a reporter abbreviation**: update `REPORTERS` in `backend/citation_parser.py`.
- **Add a journal pattern**: extend `JOURNAL_WORDS` in `citation_parser.py`.
- **Change the port**: `python3 main.py --port 9000` (default: 8000).
- **Run tests**: `cd backend && python3 test_core.py` (also `test_authority_splitter.py`, `test_fetchers.py` — all offline, no network calls).

---

## Privacy

- Your document stays on your machine: the browser app processes the `.docx` locally, and the Word add-in reads footnotes via Office.js without uploading the file.
- Footnote text and pre-fetched source snippets are sent to Google's Gemini API as part of the accuracy-checking prompt.
- Your Gemini API key is stored only in `localStorage` (browser or Word task pane) if you tick *Remember key*; it is never sent to the local server.

---

## Development Workflow

This project follows a structured **Tech Lead ↔ PM** collaboration process powered by [Superpowers](https://github.com/obra/superpowers) skills and [Codegraph](https://github.com/colbymchenry/codegraph) code intelligence.

> Full workflow spec (中文): [`docs/DEVELOPMENT-WORKFLOW.md`](docs/DEVELOPMENT-WORKFLOW.md)
> Merge Note template: [`docs/MERGE-NOTE-TEMPLATE.md`](docs/MERGE-NOTE-TEMPLATE.md)
> PRD 需求拆解 & 进度追踪: [`docs/PRD-TRACKER.md`](docs/PRD-TRACKER.md)

### Roles

| Role | Responsibility | Tools |
|------|---------------|-------|
| **Tech Lead** | Implementation, code quality, architecture | Cursor + Codegraph + Superpowers |
| **PM** | Requirements, acceptance testing, user scenarios | Claude Code + Feedback-Log.md |

### Development Cycle

```
PM writes requirement         Tech Lead develops            PM accepts
(User Story + AC)    →    (Brainstorm → TDD → Commit)  →  (Test vs AC)
in Feedback-Log.md          + Codegraph impact analysis      via Merge Note
```

### Branch Strategy

- **`master`** — stable baseline, no direct pushes
- **`feature/<name>`** — one feature per branch (e.g. `feature/url-citation`)
- **`fix/<name>`** — bug fixes

### Handoff Process (every merge to master)

1. Tech Lead pushes feature branch and creates a **Merge Note** in `docs/merge-notes/`
2. Merge Note tells PM: what changed, how to test, expected results, known limitations
3. PM tests against Acceptance Criteria and records results in `Feedback-Log.md`
4. Pass → close requirement. Fail → feedback loop continues

### File Ownership

| Tech Lead owns | PM owns |
|---------------|---------|
| `backend/main.py` | `backend/citation_parser.py` |
| `backend/fetchers/*.py` | `backend/authority_splitter.py` |
| `backend/gemini.py` | `backend/bluebook.py` |
| `backend/index.html` | `Feedback-Log.md` |
| `taskpane/` | `citation-checker-prd.pdf` |
| `docs/merge-notes/` | |

### Tooling

- **[Codegraph](https://github.com/colbymchenry/codegraph)** — semantic code intelligence (MCP). Use `codegraph_explore` to understand architecture, `codegraph_impact` before refactoring.
- **[Superpowers](https://github.com/obra/superpowers)** — structured development skills (brainstorming, TDD, systematic debugging, verification before completion).

### Roadmap (from PRD)

| Priority | Feature | Milestone | Branch |
|----------|---------|-----------|--------|
| P0 | URL citation recognition + fetch + compare | M1 | `feature/url-citation` |
| P1 | PDF parsing (text layer) | M3 | `feature/pdf-parser` |
| P1 | PDF parsing (OCR fallback) | M3 | `feature/pdf-ocr` |
| P2 | Report export (PDF/CSV) | M4 | `feature/report-export` |
| P2 | Batch progress visualization | M4 | `feature/progress-bar` |
| P3 | Semantic comparison thresholds | — | `feature/threshold` |
| P3 | Source caching / mirroring | — | `feature/source-cache` |
