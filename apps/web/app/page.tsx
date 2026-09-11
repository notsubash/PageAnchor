"use client";

import { FormEvent, SVGProps, useRef, useState } from "react";

import {
  Citation,
  GroundedAnswer,
  RetrievalMode,
  pagePngUrl,
  postAnswer,
  postReceipt,
} from "@/lib/api";

const MODES: RetrievalMode[] = ["text", "visual", "hybrid"];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<RetrievalMode>("hybrid");
  const [strict, setStrict] = useState(true);
  const [compare, setCompare] = useState(false);
  const [view, setView] = useState<"text" | "hybrid">("hybrid");
  const [pair, setPair] = useState<{
    text: GroundedAnswer;
    hybrid: GroundedAnswer;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GroundedAnswer | null>(null);
  const [selected, setSelected] = useState<Citation | null>(null);
  const askGen = useRef(0);

  const shown = pair ? pair[view] : result;

  async function ask(asked: string) {
    const gen = ++askGen.current;
    setLoading(true);
    setError(null);
    setPair(null);
    try {
      if (compare) {
        const [hybridAns, textAns] = await Promise.all([
          postAnswer({ question: asked, mode: "hybrid", strict }),
          postAnswer({ question: asked, mode: "text", strict }),
        ]);
        if (gen !== askGen.current) {
          return;
        }
        setPair({ text: textAns, hybrid: hybridAns });
        setView("hybrid");
        setResult(hybridAns);
        setSelected(hybridAns.citations[0] ?? null);
      } else {
        const primary = await postAnswer({ question: asked, mode, strict });
        if (gen !== askGen.current) {
          return;
        }
        setResult(primary);
        setSelected(primary.citations[0] ?? null);
      }
    } catch (err) {
      if (gen !== askGen.current) {
        return;
      }
      setResult(null);
      setSelected(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      if (gen === askGen.current) {
        setLoading(false);
      }
    }
  }

  function onAsk(event: FormEvent) {
    event.preventDefault();
    const asked = question.trim();
    if (!asked) {
      return;
    }
    void ask(asked);
  }

  function onCompareView(next: "text" | "hybrid") {
    setView(next);
    if (pair) {
      setSelected(pair[next].citations[0] ?? null);
    }
  }

  async function onReceipt() {
    if (!shown) {
      return;
    }
    setError(null);
    try {
      const receipt = await postReceipt(shown);
      const blob = new Blob([JSON.stringify(receipt, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `receipt-${receipt.trace_id}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  const pageLabel = selected ? `p.\u00a0${selected.page}` : "No page";
  const abstainBanner =
    shown?.abstain_reason === "unsupported"
      ? "The quote is on the page but does not contain the answer."
      : shown?.abstain
        ? `Abstained: ${shown.abstain_reason ?? "abstain"}.`
        : null;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="mark" aria-hidden="true">
            <IconMark />
          </span>
          <h1 className="wordmark">PageAnchor</h1>
        </div>
        <p className="thesis">Every answer cites a verifiable region, or it refuses.</p>
        <div className="utilities">
          <div className="page-readout" aria-live="polite">
            {pageLabel}
          </div>
          <button type="button" className="ghost" disabled={!shown} onClick={() => void onReceipt()}>
            <IconReceipt />
            Receipt
          </button>
        </div>
      </header>

      <div className="shell">
        <section className="ask" aria-label="Ask">
          <h2 className="panel-head">
            <IconAsk />
            Ask
          </h2>
          <div className="ask-body">
            <form className="form" onSubmit={onAsk}>
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask the frozen corpus"
                required
              />
              <div className="modes" role="group" aria-label="Retrieval mode">
                {MODES.map((item) => (
                  <button
                    key={item}
                    type="button"
                    className="mode"
                    aria-pressed={compare ? item !== "visual" : mode === item}
                    disabled={compare}
                    onClick={() => setMode(item)}
                  >
                    {item}
                  </button>
                ))}
              </div>
              <div className="latches">
                <label className="latch">
                  Strict
                  <input
                    className="switch"
                    type="checkbox"
                    role="switch"
                    checked={strict}
                    onChange={(event) => setStrict(event.target.checked)}
                  />
                </label>
                <label className="latch">
                  Compare TEXT
                  <input
                    className="switch"
                    type="checkbox"
                    role="switch"
                    checked={compare}
                    onChange={(event) => {
                      const on = event.target.checked;
                      setCompare(on);
                      if (on && mode === "visual") {
                        setMode("hybrid");
                      }
                    }}
                  />
                </label>
              </div>
              <button className="submit" type="submit" disabled={loading} aria-busy={loading}>
                {loading ? "Asking" : "Ask"}
                <IconArrow />
              </button>
            </form>
            {pair ? (
              <div className="modes compare-modes" role="group" aria-label="Compare retrieve">
                <button
                  type="button"
                  className="mode"
                  aria-pressed={view === "text"}
                  onClick={() => onCompareView("text")}
                >
                  TEXT
                </button>
                <button
                  type="button"
                  className="mode"
                  aria-pressed={view === "hybrid"}
                  onClick={() => onCompareView("hybrid")}
                >
                  HYBRID
                </button>
              </div>
            ) : null}
            {error ? (
              <div className="banner fault">
                <p>{faultSummary(error)}</p>
                {faultSummary(error) !== error ? (
                  <details>
                    <summary>Details</summary>
                    {error}
                  </details>
                ) : null}
              </div>
            ) : null}
            {shown?.abstain ? <p className="banner abstain">{abstainBanner}</p> : null}
            {shown && !shown.abstain && shown.answer ? (
              <div className="answer-block">
                <p className="answer">{shown.answer}</p>
              </div>
            ) : null}
            {shown && shown.citations.length > 0 ? (
              <>
                <h3 className="subhead">
                  Citations
                  <span className="panel-count">{shown.citations.length}</span>
                </h3>
                <ul className="citations">
                  {shown.citations.map((citation, index) => (
                    <li key={`${citation.region_id ?? citation.quote}-${index}`}>
                      <button
                        type="button"
                        aria-current={
                          selected?.region_id === citation.region_id &&
                          selected?.quote === citation.quote
                        }
                        onClick={() => setSelected(citation)}
                      >
                        <span className="cite-index">{index + 1}</span>
                        <div className="cite-body">
                          <p className={citation.verified ? "cite-status ok" : "cite-status bad"}>
                            {citation.verified ? (
                              <>
                                <IconCheck />
                                Verified
                              </>
                            ) : (
                              <>
                                Unverified
                                {citation.quote_in_region && !citation.answer_in_quote
                                  ? " unsupported"
                                  : ""}
                              </>
                            )}
                          </p>
                          <p className="quote">{citation.quote}</p>
                        </div>
                        <span className="cite-page">p. {citation.page}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </>
            ) : null}
          </div>
        </section>

        <section className="document" aria-label="Page">
          <div className="document-head">
            <h2 className="panel-head">
              <IconDocument />
              Document
            </h2>
            <span className="doc-id">{selected ? selected.doc_id : "No page selected"}</span>
          </div>
          <div className={`canvas${loading ? " busy" : ""}`}>
            {selected ? (
              <div className="stage">
                <img
                  alt={`Page ${selected.page} of ${selected.doc_id}`}
                  src={pagePngUrl(selected.doc_id, selected.page)}
                />
                <div
                  className="bbox"
                  style={{
                    left: `${selected.bbox[0] * 100}%`,
                    top: `${selected.bbox[1] * 100}%`,
                    width: `${(selected.bbox[2] - selected.bbox[0]) * 100}%`,
                    height: `${(selected.bbox[3] - selected.bbox[1]) * 100}%`,
                  }}
                />
              </div>
            ) : shown?.abstain ? (
              <div className="empty-canvas">
                <strong>No verified region</strong>
                <p>
                  Abstained ({shown.abstain_reason}). Citations stay in Ask if
                  present.
                </p>
              </div>
            ) : (
              <div className="empty-canvas">
                <strong>Ask the corpus</strong>
                <p>A cited page opens here, with the verified region boxed.</p>
              </div>
            )}
          </div>
        </section>

        <section className="trace" aria-label="Debug">
          <h2 className="panel-head">
            <IconTrace />
            Trace
          </h2>
          <div className="trace-body">
            {shown ? (
              <>
                <p className="trace-id">trace {shown.trace_id}</p>
                <div className="card">
                  <h3>Run</h3>
                  <table className="kv">
                    <tbody>
                      <tr>
                        <th>Mode</th>
                        <td>{shown.trace.retrieval_mode}</td>
                      </tr>
                      <tr>
                        <th>Abstain</th>
                        <td>{shown.abstain ? shown.abstain_reason ?? "yes" : "no"}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div className="card">
                  <table className="grid">
                    <caption>Hits</caption>
                    <thead>
                      <tr>
                        <th>Doc</th>
                        <th>Pg</th>
                        <th>Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {shown.trace.hits.map((hit) => (
                        <tr key={`${hit.doc_id}-${hit.page}-${hit.source}`}>
                          <td>{hit.doc_id}</td>
                          <td>{hit.page}</td>
                          <td>{hit.score.toFixed(3)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="card">
                  <table className="grid">
                    <caption>Verify</caption>
                    <thead>
                      <tr>
                        <th>Ok</th>
                        <th>Region</th>
                      </tr>
                    </thead>
                    <tbody>
                      {shown.trace.verify.length === 0 ? (
                        <tr>
                          <td colSpan={2}>none</td>
                        </tr>
                      ) : (
                        shown.trace.verify.map((row) => (
                          <tr key={`${row.region_id}-${row.quote}`}>
                            <td>{row.ok ? "yes" : "no"}</td>
                            <td>{row.region_id}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
                <div className="card">
                  <table className="grid">
                    <caption>Timings ms</caption>
                    <tbody>
                      {Object.entries(shown.trace.timings_ms).map(([name, value]) => (
                        <tr key={name}>
                          <td>{name}</td>
                          <td>{value.toFixed(0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <details>
                  <summary>Trace JSON</summary>
                  <pre>{JSON.stringify(shown.trace, null, 2)}</pre>
                </details>
              </>
            ) : (
              <p className="empty">Trace prints after /v1/answer returns.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

function faultSummary(error: string): string {
  const head = error.split("|")[0]?.trim() ?? error;
  if (head.length <= 120) {
    return head.replace(/\.$/, "");
  }
  return "The API could not answer this question.";
}

function IconMark(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" {...props}>
      <rect x="1.2" y="1.2" width="9.6" height="9.6" rx="1.4" stroke="currentColor" strokeWidth="1.4" />
      <rect x="3.2" y="3.6" width="5.6" height="2.4" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

function IconAsk(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" {...props}>
      <path d="M3 3.2h10v7.2H6.6L3 13.2V3.2Z" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

function IconDocument(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" {...props}>
      <path d="M4 2.5h5.2L12.5 6v7.5H4V2.5Z" stroke="currentColor" strokeWidth="1.4" />
      <path d="M9.1 2.6V6h3.3" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

function IconTrace(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" {...props}>
      <circle cx="4" cy="8" r="1.6" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="12" cy="4.2" r="1.6" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="12" cy="11.8" r="1.6" stroke="currentColor" strokeWidth="1.4" />
      <path d="M5.5 7.3 10.4 4.9M5.5 8.7 10.4 11.1" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

function IconReceipt(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" {...props}>
      <path d="M4 2.5h8v11l-1.2-.8-1.2.8-1.2-.8-1.2.8-1.2-.8-1.2.8v-11Z" stroke="currentColor" strokeWidth="1.4" />
      <path d="M6 5.5h4M6 8h4M6 10.4h2.4" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

function IconArrow(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" {...props}>
      <path d="M3 8h9.2M8.8 4.4 12.4 8 8.8 11.6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
    </svg>
  );
}

function IconCheck(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true" {...props}>
      <path d="M2.2 6.1 4.7 8.6 9.8 3.4" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}
