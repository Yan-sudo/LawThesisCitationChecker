# LexCheck — Law Citation Accuracy Checker

A local web app that checks whether every cited authority in a law review paper actually supports the proposition it is cited for. Upload a `.docx`, enter your Gemini API key, and LexCheck checks each footnote — splitting multi-authority footnotes into individual citations, fetching sources, and using Gemini with Google Search grounding to evaluate accuracy.

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
  main.py               ← stdlib HTTP server (no dependencies beyond Python)
  docx_parser.py        ← extracts footnotes + body sentences from .docx
  citation_parser.py    ← Bluebook citation type detection (Rules 4, 10–16)
  authority_splitter.py ← splits multi-authority footnotes; handles Compare/with
  fetchers/             ← CourtListener, USCODE, eCFR, CrossRef, OpenAlex, Google Books
  index.html            ← single-file UI served by the server
```

**Gemini runs entirely in the browser.** Your API key is never sent to the local Python server — it goes directly from your browser to Google's API.

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
- A `.docx` file with footnotes

---

## Setup

### 1 — Clone the repo

```bash
git clone https://github.com/yan-sudo/lawthesiscitationchecker.git
cd lawthesiscitationchecker
git checkout claude/word-citation-checker-EU0X5
```

### 2 — Start the server

```bash
cd backend
python3 main.py
```

The app is now available at **http://localhost:8000**.

To use a different port:

```bash
python3 main.py --port 9000
```

### 3 — Open the app

Open **http://localhost:8000** in your browser.

1. Paste your Gemini API key into the **Step 1** field (tick *Remember key* to save it in your browser's local storage).
2. Drop or select your `.docx` file in the **Step 2** field.
3. Click **Check Citations**.

That's it — no Node.js, no npm, no Word sideloading, no certificates.

---

## Usage

After clicking **Check Citations**:

1. The server extracts all footnotes and the main-body sentence each footnote is attached to.
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
- **Run tests**: `cd backend && python3 test_core.py` (36 tests, no network calls).

---

## Privacy

- Your `.docx` is processed on your local machine by the Python server and is never uploaded to any external service.
- Footnote text and pre-fetched source snippets are sent to Google's Gemini API as part of the accuracy-checking prompt.
- Your Gemini API key is stored only in your browser's `localStorage` if you tick *Remember key*; it is never sent to the local server.
