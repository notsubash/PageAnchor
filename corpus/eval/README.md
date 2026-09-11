# Gold questions

Thirty questions, frozen `2026-09-08` against the PyMuPDF region files from `pageanchor ingest` (`manifest.ingest_version` `1`, `frozen_at` in `corpus/manifest.json`).

Distribution: 6 `plain_text`, 6 `table`, 6 `figure`, 6 `layout`, 6 `unanswerable`.

Answerable rows were written by reading `corpus/regions/{doc_id}.json` and page PNGs when a caption or slide was sparse. `gold_quote` is a literal substring of some region on a `gold_pages` page after the same whitespace normalization used at verify time (NFKC, collapsed whitespace, case preserved).

Unanswerable rows are things this corpus cannot answer (other products, other planets, future leaderboards), not merely hard questions. `gold_doc_id` is null; `gold_pages` and `gold_quote` are empty.

How to score: [docs/EVAL.md](../../docs/EVAL.md).

Known weaknesses:

- Layout uses PyMuPDF text blocks, not Docling labels. Table and figure types in gold describe the PDF, not `Region.type`.
- Slide text from the Roman deck is fragmented (`What are dark energy and`).
- Hyphenation from PDF extraction is kept when that is what the region stores (`anal- ysis`).
- One slide deck instead of two; a second short, clearly licensed deck was not added.
- Text retrieve often ranks a caption or a later restatement instead of the table cell. That is scored as a citation-page miss, not a verify miss.

After `frozen_at`, fix page numbers only. New questions need a freeze bump and a new `frozen_at`.

## Hard set

`corpus/eval/hard_questions.jsonl` is additive. The frozen 30 stay put. `hard_frozen_at=2026-09-11` against `eval/results/2026-09-11-hard/`.

Sixteen rows:

- `lexical_gap`: user wording is not the page wording (embedding model vs PaliGemma-3B).
- `table_cell`: a cell value, not a caption.
- `figure_only`: sparse slide or teaser text.
- `layout`: algorithm / fragmented slide text.
- `adversarial_unanswerable`: in-corpus words, wrong document or wrong year.

Answerable rows have `gold_answer` plus a `gold_quote` copied from `corpus/regions/{doc_id}.json` on a `gold_pages` page. Unanswerable rows keep `gold_doc_id` null and empty quote/pages.

Score it separately. Do not mix those metrics into `eval/results/2026-09-10/`.
