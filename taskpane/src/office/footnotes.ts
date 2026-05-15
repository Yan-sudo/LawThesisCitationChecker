/**
 * Reads all footnotes from the active Word document.
 * Returns an array of { number, text } objects.
 */

export interface Footnote {
  number: number;
  text: string;
}

export async function getAllFootnotes(): Promise<Footnote[]> {
  return Word.run(async (context) => {
    const body = context.document.body;
    // footnotes property is available in Word JS API 1.5+
    const footnotes = body.footnotes;
    footnotes.load("items");
    await context.sync();

    const results: Footnote[] = [];
    for (let i = 0; i < footnotes.items.length; i++) {
      const fn = footnotes.items[i];
      fn.body.load("text");
      await context.sync();
      results.push({ number: i + 1, text: fn.body.text.trim() });
    }
    return results;
  });
}

/**
 * Replaces the text of a specific footnote (identified by 1-based number)
 * with newText, used when the user clicks "Apply" on a Bluebook correction.
 */
export async function applyFootnoteCorrection(
  footnoteNumber: number,
  oldText: string,
  newText: string
): Promise<void> {
  return Word.run(async (context) => {
    const body = context.document.body;
    const footnotes = body.footnotes;
    footnotes.load("items");
    await context.sync();

    const fn = footnotes.items[footnoteNumber - 1];
    if (!fn) throw new Error(`Footnote ${footnoteNumber} not found.`);

    fn.body.load("text");
    await context.sync();

    // Search within the footnote body for the old citation and replace
    const results = fn.body.search(oldText, { matchCase: false, matchWholeWord: false });
    results.load("items");
    await context.sync();

    for (const range of results.items) {
      range.insertText(newText, "Replace");
    }
    await context.sync();
  });
}
