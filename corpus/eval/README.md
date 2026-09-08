# Gold questions

Thirty questions, frozen against the PyMuPDF region files produced by `pageanchor ingest`.

Distribution: 6 `plain_text`, 6 `table`, 6 `figure`, 6 `layout`, 6 `unanswerable`.

Answerable rows were written by reading `corpus/regions/{doc_id}.json` (and page PNGs when a caption or slide was sparse). `gold_quote` is a literal substring of some region on a `gold_pages` page after the same whitespace normalization used at verify time.

Unanswerable rows are things this corpus cannot answer (other products, other planets, future leaderboards), not merely hard questions.

Known weaknesses:

- Layout uses PyMuPDF text blocks, not Docling labels. Table and figure types in gold are about the PDF, not `Region.type`.
- Slide text from the Roman deck is fragmented ("What are dark energy and").
- Hyphenation from PDF extraction is kept when that is what the region stores (`anal- ysis`).
- One slide deck instead of two; a second short, clearly licensed deck was not added.

After `frozen_at` is set in `manifest.json`, fix page numbers only. New questions need a freeze bump.
