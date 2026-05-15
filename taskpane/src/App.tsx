import React, { useState, useCallback } from "react";
import { getAllFootnotes, Footnote } from "./office/footnotes";
import CitationCard, { CheckResult } from "./components/CitationCard";

const BACKEND = "http://localhost:8000";

type Status = "idle" | "scanning" | "checking" | "done" | "error";

interface FootnoteState {
  footnote: Footnote;
  result: CheckResult | null;
  loading: boolean;
}

export default function App() {
  const [status, setStatus] = useState<Status>("idle");
  const [items, setItems] = useState<FootnoteState[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const scanAndCheck = useCallback(async () => {
    setStatus("scanning");
    setErrorMsg(null);
    setItems([]);

    let footnotes: Footnote[];
    try {
      footnotes = await getAllFootnotes();
    } catch (e: any) {
      setStatus("error");
      setErrorMsg(`Could not read footnotes: ${e.message ?? e}`);
      return;
    }

    if (footnotes.length === 0) {
      setStatus("done");
      setItems([]);
      return;
    }

    // Initialise all cards as loading
    const initial: FootnoteState[] = footnotes.map((fn) => ({
      footnote: fn,
      result: null,
      loading: true,
    }));
    setItems(initial);
    setStatus("checking");

    // Fire all checks in parallel against the backend
    await Promise.all(
      footnotes.map(async (fn, idx) => {
        try {
          const resp = await fetch(`${BACKEND}/check`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: fn.text, footnote_number: fn.number }),
          });
          if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
          const result: CheckResult = await resp.json();
          setItems((prev) => {
            const next = [...prev];
            next[idx] = { footnote: fn, result, loading: false };
            return next;
          });
        } catch (e: any) {
          // Show a degraded card rather than crashing everything
          const fallback: CheckResult = {
            footnote_number: fn.number,
            raw: fn.text,
            citation_type: "unknown",
            bluebook_valid: false,
            bluebook_issues: [`Backend error: ${e.message ?? e}`],
            bluebook_suggested: fn.text,
            source_name: "error",
            source_url: null,
            source_snippet: null,
            full_text_available: false,
            source_note: "Could not reach the citation checker backend.",
          };
          setItems((prev) => {
            const next = [...prev];
            next[idx] = { footnote: fn, result: fallback, loading: false };
            return next;
          });
        }
      })
    );

    setStatus("done");
  }, []);

  const pendingCount = items.filter((i) => i.loading).length;
  const doneCount = items.filter((i) => !i.loading).length;
  const warnCount = items.filter(
    (i) => i.result && (!i.result.bluebook_valid || i.result.source_name === "not_found" || i.result.source_name === "paywalled")
  ).length;

  return (
    <div className="app">
      <div className="header">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <rect width="20" height="20" rx="3" fill="white" fillOpacity="0.2" />
          <path d="M4 5h12M4 8h12M4 11h8M4 14h6" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <h1>Citation Checker</h1>
      </div>

      <div className="toolbar">
        <button
          className="btn btn-primary"
          onClick={scanAndCheck}
          disabled={status === "scanning" || status === "checking"}
        >
          {status === "scanning" || status === "checking" ? "Checking…" : "Scan footnotes"}
        </button>

        {status === "done" && items.length > 0 && (
          <span className="status-text">
            {doneCount} footnote{doneCount !== 1 ? "s" : ""}
            {warnCount > 0 ? ` · ${warnCount} need attention` : " · all clear"}
          </span>
        )}
      </div>

      <div className="content">
        {status === "idle" && (
          <div className="empty-state">
            <strong>Click "Scan footnotes"</strong>
            <p>The add-in will read every footnote in this document,<br />check each citation against its source, and verify Bluebook style.</p>
          </div>
        )}

        {status === "error" && (
          <div className="empty-state">
            <strong>Error</strong>
            <p style={{ color: "#a4262c" }}>{errorMsg}</p>
          </div>
        )}

        {(status === "checking" || status === "done") && items.length === 0 && (
          <div className="empty-state">
            <p>No footnotes found in this document.</p>
          </div>
        )}

        {status === "checking" && pendingCount > 0 && (
          <div style={{ fontSize: 12, color: "#605e5c", padding: "4px 8px", marginBottom: 4 }}>
            Checking {pendingCount} remaining…
          </div>
        )}

        {items.map((item, idx) => (
          <CitationCard
            key={idx}
            result={
              item.result ?? {
                footnote_number: item.footnote.number,
                raw: item.footnote.text,
                citation_type: "unknown",
                bluebook_valid: true,
                bluebook_issues: [],
                bluebook_suggested: item.footnote.text,
                source_name: null,
                source_url: null,
                source_snippet: null,
                full_text_available: false,
                source_note: null,
              }
            }
            loading={item.loading}
          />
        ))}
      </div>
    </div>
  );
}
