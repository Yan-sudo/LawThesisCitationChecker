import React, { useState } from "react";
import { applyFootnoteCorrection } from "../office/footnotes";

export interface CheckResult {
  footnote_number: number;
  raw: string;
  citation_type: string;
  bluebook_valid: boolean;
  bluebook_issues: string[];
  bluebook_suggested: string;
  source_name: string | null;
  source_url: string | null;
  source_snippet: string | null;
  full_text_available: boolean;
  source_note: string | null;
}

interface Props {
  result: CheckResult;
  loading?: boolean;
}

export default function CitationCard({ result, loading }: Props) {
  const [open, setOpen] = useState(false);
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);

  const typeLabel = {
    case: "Case",
    statute: "Statute",
    article: "Article",
    book: "Book",
    unknown: "?",
  }[result.citation_type] ?? result.citation_type;

  const sourceStatus = (() => {
    if (!result.source_name) return null;
    if (result.source_name === "paywalled") return "paywall";
    if (result.source_name === "not_found") return "warn";
    if (result.source_name === "error") return "warn";
    return result.full_text_available ? "ok" : "warn";
  })();

  async function handleApply() {
    if (applying || applied) return;
    setApplying(true);
    try {
      await applyFootnoteCorrection(
        result.footnote_number,
        result.raw,
        result.bluebook_suggested
      );
      setApplied(true);
    } catch (e) {
      console.error("Apply failed:", e);
      alert(`Could not apply correction: ${e}`);
    } finally {
      setApplying(false);
    }
  }

  return (
    <div className={`citation-card ${open ? "active" : ""}`}>
      <div className="citation-header" onClick={() => setOpen((o) => !o)}>
        <span className="footnote-num">{result.footnote_number}</span>
        <span className="citation-text">{result.raw || <em>Empty footnote</em>}</span>
        <span className="citation-badges">
          {loading ? (
            <span className="spinner" title="Checking…" />
          ) : (
            <>
              {result.citation_type !== "unknown" && (
                <span className="badge badge-type">{typeLabel}</span>
              )}
              {!result.bluebook_valid && (
                <span className="badge badge-warn">Style</span>
              )}
              {sourceStatus === "paywall" && (
                <span className="badge badge-paywall">Paywall</span>
              )}
              {sourceStatus === "warn" && (
                <span className="badge badge-error">Not found</span>
              )}
              {sourceStatus === "ok" && (
                <span className="badge badge-ok">✓ Found</span>
              )}
            </>
          )}
        </span>
      </div>

      {open && !loading && (
        <div className="citation-detail">
          {/* Bluebook section */}
          <div>
            <div className="section-label">Bluebook (Rule {typeRuleNumber(result.citation_type)})</div>
            {result.bluebook_valid ? (
              <div style={{ fontSize: 12, color: "#107c10" }}>✓ Citation style looks correct.</div>
            ) : (
              <>
                <ul className="issues-list">
                  {result.bluebook_issues.map((issue, i) => (
                    <li key={i}>{issue}</li>
                  ))}
                </ul>
                <div className="suggested-form" style={{ marginTop: 6 }}>
                  {result.bluebook_suggested}
                </div>
                {!applied ? (
                  <div className="apply-row" style={{ marginTop: 6 }}>
                    <button
                      className="btn btn-apply"
                      onClick={handleApply}
                      disabled={applying}
                    >
                      {applying ? "Applying…" : "Apply correction"}
                    </button>
                  </div>
                ) : (
                  <div style={{ fontSize: 12, color: "#107c10", marginTop: 6, textAlign: "right" }}>
                    ✓ Applied to document
                  </div>
                )}
              </>
            )}
          </div>

          {/* Source section */}
          <div>
            <div className="section-label">Source</div>
            {result.source_name === "unknown_type" || result.citation_type === "unknown" ? (
              <div className="note-box">Citation type unrecognised — source lookup skipped.</div>
            ) : (
              <>
                <div className="source-box">
                  {result.source_url ? (
                    <>
                      <strong>{sourceLabel(result.source_name)}</strong>{" "}
                      <a href={result.source_url} target="_blank" rel="noreferrer">
                        Open source ↗
                      </a>
                    </>
                  ) : (
                    <strong>{sourceLabel(result.source_name)}</strong>
                  )}
                </div>
                {result.source_note && (
                  <div className="note-box" style={{ marginTop: 6 }}>
                    {result.source_note}
                  </div>
                )}
                {result.source_snippet && (
                  <>
                    <div className="section-label" style={{ marginTop: 8 }}>
                      Relevant text from source
                    </div>
                    <div className="snippet-box">{result.source_snippet}</div>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function typeRuleNumber(type: string): string {
  return { case: "10", statute: "12", book: "15", article: "16" }[type] ?? "—";
}

function sourceLabel(name: string | null): string {
  return (
    {
      courtlistener: "CourtListener",
      uscode_house: "U.S. House USCODE",
      ecfr: "eCFR",
      crossref: "CrossRef",
      openalex: "OpenAlex",
      google_books: "Google Books",
      not_found: "Not found",
      paywalled: "Paywalled source",
      error: "Lookup error",
    }[name ?? ""] ?? name ?? "Unknown"
  );
}
