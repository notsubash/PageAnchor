const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type RetrievalMode = "text" | "visual" | "hybrid";
export type BBox = [number, number, number, number];

export type PageHit = {
  doc_id: string;
  page: number;
  score: number;
  source: RetrievalMode;
};

export type ScoredRegion = {
  doc_id: string;
  page: number;
  region_id: string;
  type: string;
  bbox: BBox;
  text: string;
  score: number;
};

export type Citation = {
  doc_id: string;
  page: number;
  region_id: string | null;
  bbox: BBox;
  quote: string;
  verified: boolean;
  quote_in_region?: boolean;
  answer_in_quote?: boolean;
};

export type VerifyResult = {
  ok: boolean;
  quote: string;
  matched_text: string | null;
  doc_id: string;
  page: number;
  region_id: string;
};

export type Trace = {
  trace_id: string;
  retrieval_mode: RetrievalMode;
  hits: PageHit[];
  regions: ScoredRegion[];
  verify: VerifyResult[];
  timings_ms: Record<string, number>;
};

export type GroundedAnswer = {
  question: string;
  answer: string | null;
  abstain: boolean;
  abstain_reason: string | null;
  citations: Citation[];
  trace: Trace;
  trace_id: string;
};

export type ReceiptDocument = {
  id: string;
  sha256: string;
};

export type Receipt = {
  question: string;
  answer: string | null;
  abstain: boolean;
  abstain_reason: string | null;
  citations: Citation[];
  verify: VerifyResult[];
  documents: ReceiptDocument[];
  ingest_version: string;
  layout_engine: string;
  retrieval_mode: RetrievalMode;
  trace_id: string;
  generator_model: string;
};

export function pagePngUrl(docId: string, page: number): string {
  return `${API}/v1/docs/${encodeURIComponent(docId)}/pages/${page}`;
}

export async function postAnswer(body: {
  question: string;
  mode: RetrievalMode;
  strict: boolean;
}): Promise<GroundedAnswer> {
  const response = await fetch(`${API}/v1/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(_detail(text) || response.statusText);
  }
  return JSON.parse(text) as GroundedAnswer;
}

export async function postReceipt(answer: GroundedAnswer): Promise<Receipt> {
  const response = await fetch(`${API}/v1/receipt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(answer),
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(_detail(text) || response.statusText);
  }
  return JSON.parse(text) as Receipt;
}

function _detail(text: string): string {
  try {
    const payload = JSON.parse(text) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    /* raw */
  }
  return text;
}
