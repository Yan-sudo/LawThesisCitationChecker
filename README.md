# Law Thesis Citation Checker

A Microsoft Word add-in that checks Bluebook citation accuracy for every footnote in a law review paper. For each citation it:

- Detects the citation type (case, statute, journal article, or book)
- Validates Bluebook format (rules 10, 12, 15, 16)
- Fetches the original source from free public databases
- Shows relevant source text for manual accuracy comparison
- Flags sources only available behind paywalls (HeinOnline, Westlaw, LexisNexis)
- Lets you apply a corrected Bluebook form with one click

---

## Architecture

```
manifest.xml          ← Word add-in manifest (points to localhost:3000)
taskpane/             ← Frontend: TypeScript + React (Office.js)
backend/              ← Backend: Python FastAPI
```

**Free data sources used:**

| Source type | API |
|---|---|
| Court cases | [CourtListener](https://www.courtlistener.com/api/) |
| Federal statutes (USC) | [U.S. House USCODE](https://uscode.house.gov/) |
| Federal regulations (CFR) | [eCFR](https://www.ecfr.gov/) |
| Journal articles (metadata) | [CrossRef](https://api.crossref.org/) + [OpenAlex](https://openalex.org/) |
| Books | [Google Books](https://books.google.com/) |

When a source is only available on HeinOnline, Westlaw, or LexisNexis, the plugin displays a clear notice so you can look it up yourself.

---

## Prerequisites

- Node.js 18+
- Python 3.10+ (use `python3` on Mac/Linux)
- Microsoft Word (Desktop — Windows or Mac). Word on the Web also works.
- A self-signed SSL certificate for localhost (see step 2 below)

---

## Setup

### 0 — Clone the repo

```bash
git clone https://github.com/yan-sudo/lawthesiscitationchecker.git
cd lawthesiscitationchecker
git checkout claude/word-citation-checker-EU0X5
```

### 1 — Backend

The backend uses only Python's standard library plus `requests` (usually pre-installed on Mac). No virtual environment is strictly required.

```bash
cd backend

# Install the one dependency if not already present
pip3 install requests

# Start the server
python3 main.py
```

The API will be available at `http://localhost:8000`.

To use a different port:
```bash
python3 main.py --port 9000
```

### 2 — Frontend (Word add-in task pane)

```bash
cd taskpane
npm install

# Install the Office Add-in dev certificate (one-time, requires admin/sudo)
npx office-addin-dev-certs install

npm run dev
```

The task pane is served at `https://localhost:3000/taskpane.html`.

### 3 — Sideload the add-in into Word

#### Windows (Desktop)
1. Copy the full path to `manifest.xml`.
2. In Word: **File → Options → Trust Center → Trust Center Settings → Trusted Add-in Catalogs**.
3. Add a catalog URL of `file:///C:/path/to/LawThesisCitationChecker` and check **Show in Menu**.
4. Restart Word, then **Insert → My Add-ins → Shared Folder** → select **Citation Checker**.

#### Mac (Desktop)
```bash
# Copy manifest to the Word add-ins folder
cp manifest.xml ~/Library/Containers/com.microsoft.Word/Data/Documents/wef/
```
Then in Word: **Insert → My Add-ins** → the add-in should appear.

#### Word on the Web
1. Go to **Insert → Add-ins → Upload My Add-in**.
2. Browse to `manifest.xml` and click **Upload**.

---

## Usage

1. Open a law review paper (`.docx`) in Word.
2. Click **Home → Check Citations** to open the task pane.
3. Click **Scan footnotes** — every footnote is read and checked simultaneously.
4. Each footnote card shows:
   - Detected citation type badge
   - Bluebook issues (if any) with a corrected form
   - Source status: ✓ Found / Paywall / Not found
   - Relevant text from the source (where available)
5. Click **Apply correction** to replace the citation text in the document.

---

## Supported citation patterns

### Cases — Bluebook Rule 10
```
Miranda v. Arizona, 384 U.S. 436 (1966)
Brown v. Bd. of Educ., 347 U.S. 483, 495 (1954)      ← with pincite
Chevron U.S.A. Inc. v. NRDC, 467 U.S. 837 (1984)
Palsgraf v. Long Island R.R., 248 N.Y. 339 (1928)
```

### Statutes — Bluebook Rule 12
```
42 U.S.C. § 1983 (2018)
15 U.S.C. §§ 1–7 (2018)
29 C.F.R. § 541.100 (2023)
```

### Journal articles — Bluebook Rule 16
```
Katharine T. Bartlett, Feminist Legal Methods, 103 Harv. L. Rev. 829 (1990)
Richard A. Posner, The Law and Economics of Contract Interpretation, 83 Tex. L. Rev. 1581, 1600 (2005)
```

### Books — Bluebook Rule 15
```
William L. Prosser, Handbook of the Law of Torts 23 (4th ed. 1971)
Laurence H. Tribe, American Constitutional Law 567 (2d ed. 1988)
```

---

## Extending

- **Add a reporter**: update `REPORTERS` list in `backend/citation_parser.py`.
- **Add a journal pattern**: extend `JOURNAL_WORDS` regex in `citation_parser.py`.
- **Deploy backend**: replace `http://localhost:8000` in `taskpane/src/App.tsx` with your hosted URL, then rebuild (`npm run build`) and update `manifest.xml` with the production task pane URL.

---

## Limitations

- Full text is not always available for law review articles — CrossRef and OpenAlex return metadata and open-access links only; most older law review articles are on HeinOnline.
- Google Books page-level snippet retrieval requires a paid API key; the free tier returns descriptions only.
- The Bluebook parser uses regex and covers the most common patterns. Unusual citation forms (id., supra, hereinafter, string citations) are not yet handled.
