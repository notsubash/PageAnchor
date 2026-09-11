# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary visitors are mixed: a hiring-panel or portfolio reviewer who needs to see grounded citations in one sitting, and the same person (or a researcher) actually asking questions against the frozen corpus. Demo comes first; daily ask is second.

Assumption: they are technical enough to read a retrieval mode, a `trace_id`, and an abstain reason without a tutorial.

## Product Purpose

PageAnchor answers questions over a frozen local PDF corpus. Every answer cites a verifiable region on a page, or it refuses. Success is that the browser, CLI, and HTTP API show the same `GroundedAnswer`, and that a citation can be checked by eye on the page image.

## Positioning

The mechanism a neighboring chatbot cannot copy: quotes are verified as normalized substrings of the cited region text; failed verify sets `abstain=true` and clears the answer. Visual retrieve and hybrid RRF exist to find the page; layout regions plus the overlay exist to show where.

## Operating Context

- Frozen 8-PDF corpus on disk; no upload, login, or chat history.
- Operator runs ingest locally, then FastAPI on `:8000` and this Next.js overlay on `:3000`.
- Retrieval modes: `text`, `visual`, `hybrid` (default). `strict` verify is on by default.
- Pages are 1-based. BBoxes are normalized `[x0,y0,x1,y1]` on the ingested PNG.
- Debug `Trace` (hits, region scores, verify rows, timings, `trace_id`) is part of the product, not an afterthought.

## Capabilities and Constraints

- One overlay route. Talks to FastAPI only (`/v1/answer` plus page PNGs).
- PNG page viewer with citation bbox overlay. No PDF.js, no user corpus, no auth.
- Empty, error, and abstain states are first-class. Do not invent an answer when the system abstains.
- `pageanchor.core` must not be imported from the web app.
- Undecided: no formal accessibility audit bar was set. Keyboard and screen-reader use should still work.

## Brand Commitments

Name: PageAnchor. Thesis line in use: "Every answer cites a verifiable region, or it refuses." Code license Apache-2.0; per-document licenses live in `corpus/LICENSE.md`. Standing visual preference (2026-09-11): a dark platform workbench at Linear + Vercel dashboard craft. That replaces the microfilm-reader world.

## Evidence on Hand

- Real ingested page PNGs and region JSON under `corpus/` (gitignored pages).
- Gold questions in `corpus/eval/gold_questions.jsonl` (table, figure, layout, unanswerable).
- Live API returns `GroundedAnswer` + top-level `trace_id`.
- Do not fabricate eval scores, customers, or capabilities the CLI/API do not have.

## Product Principles

1. Evidence over fluency: a boxed region beats a confident paragraph.
2. Refusal is a feature: show `abstain_reason`, keep unverified citations visible for the trail.
3. One object everywhere: overlay JSON is the CLI JSON.
4. The page is the proof surface; chrome must not hide the bbox.
5. Modes and strict are operator controls, not marketing toggles.
