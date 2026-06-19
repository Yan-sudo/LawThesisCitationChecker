# Using Citation Checker as a Word add-in (macOS)

Yes — this runs as a real Word task pane add-in. It reads the footnotes from
the document you have open, checks each citation against its source, and shows
the results in a side panel inside Word.

## Why you couldn't import it before

Word for **Mac has no "Import add-in" button**. Unlike Windows and Word on the
web, on Mac you install a developer add-in by putting its `manifest.xml` into a
specific hidden folder, then restarting Word. That folder is:

```
~/Library/Containers/com.microsoft.Word/Data/Documents/wef
```

The `setup-mac.command` script below does this for you, plus the other thing
Word requires: serving the add-in over **trusted HTTPS**.

---

## One-time setup

You need **Python 3** (check with `python3 --version`; if missing, get it from
<https://www.python.org/downloads/>).

1. Download/clone this project somewhere stable, e.g. your Documents folder.
2. In **Finder**, open the project folder and **double-click `setup-mac.command`**.
   - If macOS blocks it ("unidentified developer"), right-click → **Open** → **Open**.
   - It creates a trusted `https://localhost:8000` certificate and installs the
     add-in into Word. You may be asked for your Mac password once (to trust the
     certificate) — that's expected.

That's it. You only do this once.

> Prefer the terminal? `bash setup-mac.command` does the same thing.

---

## Every time you want to check a document

1. **Start the checker:** double-click **`run.command`** (a Terminal window
   opens and stays open — leave it running). It serves `https://localhost:8000`.
2. **Open your document in Word.** Quit and reopen Word the first time after setup.
3. On the **Home** tab of the ribbon, click **Citation Checker**. A panel opens
   on the right.
4. Paste your **Gemini API key** (free from
   <https://aistudio.google.com/app/apikey>), then click
   **Scan & check this document**.

When you're done, close the Terminal window (or press `Ctrl+C` in it) to stop
the server.

---

## How it works

- The task pane is the same checker UI as the browser app, served by the local
  Python server over HTTPS.
- Inside Word it reads footnotes directly with Office.js (no `.docx` upload),
  sends the footnote text to the local server to identify sources and Bluebook
  rules, then runs **Gemini in the task pane** (your key goes straight to Google,
  never to the local server) to judge whether each citation supports its point.
- The same project still works as a plain browser app — just run the server and
  open `https://localhost:8000`, where you upload a `.docx` instead.

---

## Troubleshooting

**The button isn't on the Home tab.**
Fully quit Word (`Cmd+Q`) and reopen it. Confirm the manifest was copied:
`ls ~/Library/Containers/com.microsoft.Word/Data/Documents/wef`

**The pane opens but is blank or shows a security/certificate warning.**
The server isn't running, or the certificate isn't trusted yet.
- Make sure `run.command` is running and you can open `https://localhost:8000`
  in Safari without a warning.
- If Safari warns, open **Keychain Access**, search **localhost**, double-click
  it, expand **Trust**, set **When using this certificate: Always Trust**, close
  (enter your password), then reopen Word.

**"No footnotes found."**
The add-in reads real Word footnotes (Insert → Footnote). Endnotes and
manually typed numbers aren't detected. Reading footnotes needs a reasonably
recent Word (Microsoft 365 / Word 2021+).

**Re-running setup.** Safe to run `setup-mac.command` again anytime; it skips
the certificate if it already exists and just refreshes the installed manifest.
