import { GroundedAnswer } from "@/lib/api";

export const SEEDS = [
  {
    id: "table",
    label: "Table",
    question: "What is the title of Table A in the January 2025 CPI release?",
  },
  {
    id: "slide",
    label: "Slide",
    question: "What is the title on the first slide of the Roman Space Telescope deck?",
  },
  {
    id: "unanswerable",
    label: "Refuse",
    question: "How many parameters does GPT-5 have?",
  },
] as const;

const GLUE_HEADING_BBOX: [number, number, number, number] = [
  0.4424869312959559, 0.14049286312527126, 0.55751421560649, 0.15105927592576152,
];

export const Q011_EXHIBIT: GroundedAnswer = {
  question: "How many CoLA training examples does the GLUE table list?",
  answer: null,
  abstain: true,
  abstain_reason: "unsupported",
  citations: [
    {
      doc_id: "arxiv-1804-glue",
      page: 8,
      region_id: "arxiv-1804-glue:p8:r2",
      bbox: GLUE_HEADING_BBOX,
      quote: "Single-Task Training",
      verified: false,
      quote_in_region: true,
      answer_in_quote: false,
    },
  ],
  trace_id: "exhibit-q011-unsupported",
  trace: {
    trace_id: "exhibit-q011-unsupported",
    retrieval_mode: "text",
    hits: [],
    regions: [],
    verify: [
      {
        ok: false,
        quote: "Single-Task Training",
        matched_text: "Single-Task Training",
        doc_id: "arxiv-1804-glue",
        page: 8,
        region_id: "arxiv-1804-glue:p8:r2",
      },
    ],
    timings_ms: {},
  },
};
