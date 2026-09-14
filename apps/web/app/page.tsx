"use client";

import { FormEvent, SVGProps, useEffect, useRef, useState } from "react";

import {
  BBox,
  Citation,
  CorpusDoc,
  GroundedAnswer,
  RetrievalMode,
  ScoredRegion,
  getCorpus,
  pagePngUrl,
  postAnswer,
  postReceipt,
} from "@/lib/api";

type PageView = {
  doc_id: string;
  page: number;
  bbox: BBox | null;
  region_id: string | null;
};

function citationView(citation: Citation): PageView {
  return {
    doc_id: citation.doc_id,
    page: citation.page,
    bbox: citation.bbox,
    region_id: citation.region_id,
  };
}

function regionView(region: ScoredRegion): PageView {
  return {
    doc_id: region.doc_id,
    page: region.page,
    bbox: region.bbox,
    region_id: region.region_id,
  };
}

function hitView(docId: string, page: number): PageView {
  return { doc_id: docId, page, bbox: null, region_id: null };
}

function defaultView(answer: GroundedAnswer): PageView | null {
  if (answer.citations[0]) {
    return citationView(answer.citations[0]);
  }
  if (answer.trace.regions[0]) {
    return regionView(answer.trace.regions[0]);
  }
  return null;
}

const MODES: RetrievalMode[] = ["text", "visual", "hybrid"];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<RetrievalMode>("hybrid");
  const [strict, setStrict] = useState(true);
  const [compare, setCompare] = useState(false);
  const [compareSide, setCompareSide] = useState<"text" | "hybrid">("hybrid");
  const [pair, setPair] = useState<{
    text: GroundedAnswer;
    hybrid: GroundedAnswer;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GroundedAnswer | null>(null);
  const [view, setView] = useState<PageView | null>(null);
  const [docs, setDocs] = useState<Record<string, CorpusDoc>>({});
  const lastGood = useRef<PageView | null>(null);
  const viewRef = useRef<PageView | null>(null);
  const askGen = useRef(0);
  viewRef.current = view;

  const shown = pair ? pair[compareSide] : result;

  useEffect(() => {
    void getCorpus()
      .then((rows) => {
        const next: Record<string, CorpusDoc> = {};
        for (const row of rows) {
          next[row.id] = row;
        }
        setDocs(next);
      })
      .catch(() => {
        /* titles fall back to doc_id */
      });
  }, []);

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
        setCompareSide("hybrid");
        setResult(hybridAns);
        setView(defaultView(hybridAns));
      } else {
        const primary = await postAnswer({ question: asked, mode, strict });
        if (gen !== askGen.current) {
          return;
        }
        setResult(primary);
        setView(defaultView(primary));
      }
    } catch (err) {
      if (gen !== askGen.current) {
        return;
      }
      setResult(null);
      setView(null);
      lastGood.current = null;
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
    setCompareSide(next);
    if (pair) {
      setView(defaultView(pair[next]));
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

  const pageLabel = view ? `p.\u00a0${view.page}` : "No page";
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
                  aria-pressed={compareSide === "text"}
                  onClick={() => onCompareView("text")}
                >
                  TEXT
                </button>
                <button
                  type="button"
                  className="mode"
                  aria-pressed={compareSide === "hybrid"}
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
                          view?.region_id === citation.region_id &&
                          view?.page === citation.page
                        }
                        onClick={() => setView(citationView(citation))}
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
            <div className="doc-meta">
              <span className="doc-title">
                {view
                  ? docs[view.doc_id]?.title || view.doc_id
                  : "No page selected"}
              </span>
              {view ? <span className="doc-id">{view.doc_id}</span> : null}
            </div>
            {view && docs[view.doc_id]?.pages ? (
              <div className="page-walk">
                <button
                  type="button"
                  className="ghost"
                  disabled={view.page <= 1}
                  onClick={() =>
                    setView({
                      doc_id: view.doc_id,
                      page: view.page - 1,
                      bbox: null,
                      region_id: null,
                    })
                  }
                >
                  Prev
                </button>
                <button
                  type="button"
                  className="ghost"
                  disabled={view.page >= (docs[view.doc_id]?.pages ?? view.page)}
                  onClick={() =>
                    setView({
                      doc_id: view.doc_id,
                      page: view.page + 1,
                      bbox: null,
                      region_id: null,
                    })
                  }
                >
                  Next
                </button>
              </div>
            ) : null}
          </div>
          <div className={`canvas${loading ? " busy" : ""}`}>
            {view ? (
              <div className="stage">
                <img
                  key={`${view.doc_id}-${view.page}`}
                  alt={`Page ${view.page} of ${view.doc_id}`}
                  src={pagePngUrl(view.doc_id, view.page)}
                  onLoad={() => {
                    const docId = view.doc_id;
                    const page = view.page;
                    const current = viewRef.current;
                    if (
                      current?.doc_id === docId &&
                      current.page === page
                    ) {
                      lastGood.current = { ...current };
                    }
                  }}
                  onError={() => {
                    setError("Page image missing.");
                    setView(lastGood.current);
                  }}
                />
                {view.bbox ? (
                  <div
                    className="bbox"
                    style={{
                      left: `${view.bbox[0] * 100}%`,
                      top: `${view.bbox[1] * 100}%`,
                      width: `${(view.bbox[2] - view.bbox[0]) * 100}%`,
                      height: `${(view.bbox[3] - view.bbox[1]) * 100}%`,
                    }}
                  />
                ) : null}
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
                          <td colSpan={3} style={{ padding: 0, border: 0 }}>
                            <button
                              type="button"
                              className="hit-row"
                              onClick={() => setView(hitView(hit.doc_id, hit.page))}
                            >
                              <span>{hit.doc_id}</span>
                              <span>{hit.page}</span>
                              <span>{hit.score.toFixed(3)}</span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="card">
                  <table className="grid">
                    <caption>Regions</caption>
                    <thead>
                      <tr>
                        <th>Doc</th>
                        <th>Pg</th>
                        <th>Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {shown.trace.regions.length === 0 ? (
                        <tr>
                          <td colSpan={3}>none</td>
                        </tr>
                      ) : (
                        shown.trace.regions.map((region) => (
                          <tr key={region.region_id}>
                            <td colSpan={3} style={{ padding: 0, border: 0 }}>
                              <button
                                type="button"
                                className="hit-row"
                                onClick={() => setView(regionView(region))}
                              >
                                <span>{region.doc_id}</span>
                                <span>{region.page}</span>
                                <span>{region.score.toFixed(3)}</span>
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
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
