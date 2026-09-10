"use client";

import { FormEvent, useState } from "react";

import {
  Citation,
  GroundedAnswer,
  RetrievalMode,
  pagePngUrl,
  postAnswer,
} from "@/lib/api";
import { Q011_EXHIBIT, SEEDS } from "@/lib/exhibits";

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

  const shown = pair ? pair[view] : result;

  async function ask(asked: string) {
    setLoading(true);
    setError(null);
    setPair(null);
    try {
      if (compare) {
        const [hybridAns, textAns] = await Promise.all([
          postAnswer({ question: asked, mode: "hybrid", strict }),
          postAnswer({ question: asked, mode: "text", strict }),
        ]);
        setPair({ text: textAns, hybrid: hybridAns });
        setView("hybrid");
        setResult(hybridAns);
        setSelected(hybridAns.citations[0] ?? null);
      } else {
        const primary = await postAnswer({ question: asked, mode, strict });
        setResult(primary);
        setSelected(primary.citations[0] ?? null);
      }
    } catch (err) {
      setResult(null);
      setSelected(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
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

  function onSeed(seedQuestion: string) {
    setQuestion(seedQuestion);
    void ask(seedQuestion);
  }

  function onExhibit() {
    setQuestion(Q011_EXHIBIT.question);
    setError(null);
    setPair(null);
    setResult(Q011_EXHIBIT);
    setSelected(Q011_EXHIBIT.citations[0] ?? null);
  }

  function onCompareView(next: "text" | "hybrid") {
    setView(next);
    if (pair) {
      setSelected(pair[next].citations[0] ?? null);
    }
  }

  const frame = selected?.page;
  const frameLabel =
    frame != null ? `FRAME ${String(frame).padStart(3, "0")}` : "FRAME ---";
  const abstainBanner =
    shown?.abstain_reason === "unsupported"
      ? "The quote is on the page but does not contain the answer."
      : shown?.abstain
        ? `Abstained: ${shown.abstain_reason ?? "abstain"}. The answer well stays empty.`
        : null;

  return (
    <div className="reader">
      <header className="bezel-top">
        <h1 className="wordmark">PageAnchor</h1>
        <p className="thesis">Every answer cites a verifiable region, or it refuses.</p>
        <div className="frame-readout" aria-live="polite">
          {frameLabel}
        </div>
      </header>
      <div className="deck">
        <section className="catalog" aria-label="Ask">
          <h2 className="vh">Ask</h2>
          <form className="ask" onSubmit={onAsk}>
            <div className="modes" role="group" aria-label="Retrieval mode">
              {MODES.map((item) => (
                <button
                  key={item}
                  type="button"
                  className="mode"
                  aria-pressed={mode === item}
                  onClick={() => setMode(item)}
                >
                  {item}
                </button>
              ))}
            </div>
            <label className="latch">
              <input
                type="checkbox"
                checked={strict}
                onChange={(event) => setStrict(event.target.checked)}
              />
              Strict
            </label>
            <label className="latch">
              <input
                type="checkbox"
                checked={compare}
                onChange={(event) => setCompare(event.target.checked)}
              />
              Compare TEXT
            </label>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask the frozen corpus"
              required
            />
            <div className="modes" role="group" aria-label="Seed questions">
              {SEEDS.map((seed) => (
                <button
                  key={seed.id}
                  type="button"
                  className="mode"
                  onClick={() => onSeed(seed.question)}
                >
                  {seed.label}
                </button>
              ))}
            </div>
            <button type="button" className="mode" onClick={onExhibit}>
              Exhibit
            </button>
            <button className="load" type="submit" disabled={loading} aria-busy={loading}>
              {loading ? "Advancing" : "Load frame"}
            </button>
          </form>
          {pair ? (
            <div className="modes" role="group" aria-label="Compare retrieve">
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
          {error ? <p className="banner fault">{error}</p> : null}
          {shown?.abstain ? <p className="banner abstain">{abstainBanner}</p> : null}
          {shown && !shown.abstain && shown.answer ? (
            <div className="well-plate">
              <p className="plate-label">Answer</p>
              <p className="answer">{shown.answer}</p>
            </div>
          ) : null}
          {shown && shown.citations.length > 0 ? (
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
                    <div className="cite-meta">
                      <span>
                        {citation.doc_id} p.{citation.page}
                      </span>
                      {citation.verified ? (
                        <img
                          className="stamp"
                          src="/stamps/verified-stamp.png"
                          alt="verified"
                        />
                      ) : (
                        <span className="bad">
                          unverified
                          {citation.quote_in_region && !citation.answer_in_quote
                            ? " unsupported"
                            : ""}
                        </span>
                      )}
                    </div>
                    <p className="quote">{citation.quote}</p>
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </section>

        <section className="gate" aria-label="Page">
          <div className="hood">
            <div className="sprocket" aria-hidden="true" />
            <div className={`well${loading ? " busy" : ""}`}>
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
                <div className="leader">
                  <img src="/stamps/no-frame-stamp.png" alt="" />
                  <p>
                    Abstained ({shown.abstain_reason}). Citations stay on the left bezel if
                    present.
                  </p>
                </div>
              ) : null}
            </div>
            <div className="sprocket" aria-hidden="true" />
          </div>
          <p className="gate-meta">
            {selected ? selected.doc_id : "Gate idle"}
            <span className="odometer">{frameLabel}</span>
          </p>
        </section>

        <section className="index" aria-label="Debug">
          <h2 className="panel-title">Trace</h2>
          {shown ? (
            <>
              <p className="debug-id">trace {shown.trace_id}</p>
              <table className="telemetry">
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
              <table className="telemetry">
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
              <table className="telemetry">
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
              <details>
                <summary>Trace JSON</summary>
                <pre>{JSON.stringify(shown.trace, null, 2)}</pre>
              </details>
            </>
          ) : (
            <p className="empty">The TRACE strip prints after /v1/answer returns.</p>
          )}
        </section>
      </div>
    </div>
  );
}
