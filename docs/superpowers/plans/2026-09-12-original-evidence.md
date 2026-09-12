# Original Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) and ponytail skill. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rank the original table, slide, or methods page over later restatements, put that span in the five-region prompt, and keep nested verify strict.

**Architecture:** One ask path still. Retrieve a 20-page pool, 3-way RRF (text + visual + BM25) plus cheap page rerank, then `select_evidence` over the full pool. Default hybrid/visual crop scoring on a shortlist. After generate, re-anchor a verified quote to a better region in that pool when the answer string lives there. Overlay modes stay `text` / `visual` / `hybrid`.

**Tech Stack:** Existing Qwen3-Embedding-0.6B, ColQwen2, LanceDB BM25 helper, DeepSeek V4, pytest, frozen gold `2026-09-08`, hard set `corpus/eval/hard_questions.jsonl`.

**Baseline (do not mix folders):** hard hybrid+verify in `eval/results/2026-09-11-hard/` is Recall@5 0.583, region hit 0.417, citation page hit 0.375, abstain recall 0.5, verify pass 1.0. Frozen hybrid in `eval/results/2026-09-10-gpu/` is Recall@5 0.875, citation page hit 0.846, abstain recall 1.0.

## Global Constraints

- Overlay retrieve keys remain exactly `text`, `visual`, `hybrid`. No GraphRAG, HyDE, extra mode buttons, or new embedder.
- Keep `corpus/eval/gold_questions.jsonl` freeze `2026-09-08`. Do not mix hard-set numbers into `eval/results/2026-09-10/`.
- Strict nested verify stays default. Do not loosen abstain to raise answer count. Do not add generator retry.
- `low_retrieval_score` stays unused. No global score cutoff.
- PyMuPDF remains default layout. All regions are `type="text"`. Do not require Docling labels. Do not freeze-bump gold quotes.
- `uv run pytest tests/` stays GPU-free. Mock retrieve, generate, and embed.
- Visual crop encode stays off in CI. Production hybrid/visual may turn it on; text mode stays dense-only.
- Headline eval is still D (`hybrid+verify`).

## File map

- Modify: `src/pageanchor/retrieve/hybrid.py` — 3-way RRF, `pool_k`
- Create: `src/pageanchor/retrieve/rerank.py` — query cues, same-doc fill, page rerank
- Modify: `src/pageanchor/ground/regions.py` — coverage union, two-pass slots, crop shortlist
- Modify: `src/pageanchor/ground/answer.py` — pass pool into select, default visual crops on hybrid/visual, canonical cite
- Create: `src/pageanchor/ground/canonical.py` — citation repair + question constraints
- Modify: `src/pageanchor/eval/report.py` — optional, only if a new miss table is needed
- Tests: `tests/test_hybrid.py`, `tests/test_rerank.py`, `tests/test_select_regions.py`, `tests/test_canonical.py`, `tests/test_answer_policy.py`
- Docs: this file; after the operator eval, a short paragraph in `docs/EVAL.md`

## Out of scope

New embedding model, ColPali fine-tune, Docling default, pixel OCR verify, score cutoff, user upload, overlay restyle.

---

### Task 0: Retrieve-only diagnostic (no generator)

**Files:**
- Create: `tests/test_rerank.py` (fixtures only; no live LanceDB in CI)
- Operator: retrieve-only loop against the existing indexes, write `eval/results/2026-09-12-retrieve/`

**Why:** Hard misses may already sit at rank 8–20. Do not invent page heuristics until Recall@20 is measured.

**Interfaces:**
- Consumes: `search_text`, `search_visual`, `search_hybrid`, `search_bm25` with `k=20`
- Produces: a markdown table of Recall@5 / @10 / @20 per mode on the 12 answerable hard rows, plus whether 3-way RRF or BM25 alone would have retrieved the gold page

- [x] **Step 1:** For each hard answerable id, record gold `(doc_id, page)` vs top-20 of text, visual, hybrid, bm25. No DeepSeek call.

- [x] **Step 2:** Commit only if you keep the table. CI does not run this.

**Gate:** If gold pages are usually inside RRF@20, Phase 1 is rerank + wider `select_evidence` pool. If they are missing at 20, Phase 1 must add same-doc fill and query cues, not just `k=20`.

---

### Task 1: Missed retrieve (Phase 1)

Put the original page in the pool and in `trace.hits[:5]`.

**Files:**
- Modify: `src/pageanchor/retrieve/hybrid.py`
- Create: `src/pageanchor/retrieve/rerank.py`
- Modify: `src/pageanchor/ground/answer.py` (`k=5` stays the metric slice; search uses `pool_k=20`)
- Test: `tests/test_hybrid.py`, `tests/test_rerank.py`, `tests/test_answer_policy.py`

**Interfaces:**
- Consumes: existing `PageHit` lists from text, visual, BM25
- Produces:

```python
def rrf_fuse_many(
    hit_lists: list[list[PageHit]],
    k: int = 5,
    k_rrf: int = 60,
) -> list[PageHit]:
    ...

def search_hybrid(...) -> list[PageHit]:
    # 3-way RRF: text, visual, bm25. Keep rrf_fuse(text, visual) as a wrapper for old tests.

POOL_K = 20

def expand_same_doc(hits: list[PageHit], *, window: int = 2) -> list[PageHit]:
    # For each hit, add pages in [page-window, page+window] for that doc_id
    # if not already present. Score copies the parent hit so rerank can sort.
    # Dedup by (doc_id, page). Cap at POOL_K after rerank, not before.

def cue_boost(question: str, hit: PageHit, region_texts: list[str]) -> float:
    # +1 if question has "Table N" / "Algorithm N" and some region text contains that phrase.
    # +1 if question has "first slide" / "title on the first" and hit.page == 1.
    # 0 otherwise. No LLM.

def rerank_pages(
    question: str,
    hits: list[PageHit],
    *,
    page_text: dict[tuple[str, int], str] | None = None,
) -> list[PageHit]:
    # Stable sort: RRF/search score, then cue_boost, then earlier page as tie-break
    # (same doc only). Do not globally prefer page 1 across documents.
```

`grounded_answer` calls `search_fn(question, POOL_K)`, `expand_same_doc`, `rerank_pages`, then `select_evidence(question, hits)` on the full pool. `trace.hits` is that ranked pool (length ≤ 20). Recall@5 is still `hits[:5]`.

- [ ] **Step 1:** Tests: 3-way RRF prefers a page that BM25 ranks first when dense lists miss it; `expand_same_doc` injects p.3 when p.1 and p.5 are hits; `cue_boost` ranks `(doc, 1)` first for "title on the first slide"; `rerank_pages` prefers an earlier page in the same doc on a score tie.

- [ ] **Step 2:** Implement. Keep `rrf_fuse(text, visual, k=)` working.

- [ ] **Step 3:** `uv run pytest tests/test_hybrid.py tests/test_rerank.py tests/test_answer_policy.py tests/test_search_sparse.py -q`

**Hard-set targets after this phase (retrieve metrics, generator may still miss):** h001/h003/h004 gold p.3 in hits[:5], h007 p.7 in hits[:5], h008 p.1 in hits[:5]. Frozen Recall@5 must not drop below 20/24.

---

### Task 2: Over-abstain / region miss (Phase 2)

If the gold page is in the pool, the gold span must be in the five regions.

**Files:**
- Modify: `src/pageanchor/ground/regions.py`
- Modify: `src/pageanchor/ground/answer.py` (visual flag)
- Test: `tests/test_select_regions.py`, `tests/test_answer_policy.py`, `tests/test_visual_regions.py`

**Interfaces:**
- Consumes: `select_regions`, `dense_rerank`, optional `score_region_crops`
- Produces: same `select_evidence(...)` signature, new behavior:

1. Per hit page, union Jaccard top `pool_per_page` (20) with the longest region on that page (character length). PyMuPDF tables are usually one fat `type="text"` block; length is the proxy, not Docling `table`.
2. Dense rerank the union.
3. If `visual=True`, crop-score only `ranked[:24]`, then `blend_scores`. Do not encode 20×20 crops.
4. Two-pass slotting into `max_regions=5`: first pass one region per hit page in reranked page order, second pass fill with `per_page=2`. Existing cap test still holds when only two pages are in `hits`.

Visual default in `grounded_answer`:

```python
visual = mode in {"visual", "hybrid"} and os.getenv("PAGEANCHOR_VISUAL_REGIONS", "1") != "0"
```

Text mode: visual false. `PAGEANCHOR_VISUAL_REGIONS=0` disables crops when ColQwen2 is too slow. Update `test_select_evidence_visual_flag_follows_env` to match (hybrid default on, text off, env `0` forces off).

- [ ] **Step 1:** Test that a long table block with `CoLA 8.5k` beats a short heading that shares query words, even when Jaccard on the heading is higher.

- [ ] **Step 2:** Test two-pass: three hit pages, `max_regions=5`, `per_page=2` yields at least one region from each of the top three pages.

- [ ] **Step 3:** Test crop shortlist: fake `embed_crops` is called with ≤ 24 regions when the pool is 40.

- [ ] **Step 4:** `uv run pytest tests/test_select_regions.py tests/test_visual_regions.py tests/test_answer_policy.py -q`

**Hard-set targets:** region hit ≥ 8/12. Known rows: h005 CoLA cell, h006 CDC table (page already retrieved), h009 PubLayNet, h010 Adam algorithm. Frozen q011 (GLUE CoLA) should stop abstaining as `unanswerable` on hybrid if the cell is in `trace.regions`.

Do not add a second generator call.

---

### Task 3: Wrong-page restatements (Phase 3)

Verified substring on the wrong page is still a miss. Repair the box, or abstain when the question names the wrong year/doc.

**Files:**
- Create: `src/pageanchor/ground/canonical.py`
- Modify: `src/pageanchor/ground/answer.py` (`_apply_policy` after citations are built, before strict)
- Test: `tests/test_canonical.py`, `tests/test_answer_policy.py`

**Interfaces:**

```python
def canonical_region(
    answer: str | None,
    cited: ScoredRegion,
    candidates: list[ScoredRegion],
    question: str,
) -> ScoredRegion:
    # Candidates where verify_quote(answer, region.text).
    # Score: cue_boost(question, page) + token overlap(question, region.text).
    # Tie-break: lower page in the same doc_id as the cited region.
    # If nothing beats cited, return cited.
    # Never jump to another doc_id unless the cited doc fails question_constraints.

def question_constraints(question: str, *, corpus_titles: dict[str, str] | None = None) -> None | str:
    # If the question contains a four-digit year, that year must appear in the
    # cited region text or we abstain unanswerable (h015 December 2023 vs 2024).
    # If the question names a known corpus title token (adam, colpali, layoutlmv3,
    # glue, mmwr, cpi) and the cited doc_id does not match, abstain (h016).
    # Unknown questions: no constraint. Do not parse arbitrary English.

def apply_canonical(answer: GroundedAnswer, candidates: list[ScoredRegion]) -> GroundedAnswer:
    # Rewrite citation region_id/page/bbox/quote flags using canonical_region.
    # Re-run verify_quote / answer_in_quote. Nested policy unchanged.
```

Wire `apply_canonical` with the `select_evidence` pool (not only the five prompt regions) so a restatement quote can move to the original table if that page was retrieved.

Keep quote verbatim. If the canonical region does not contain the generator quote but does contain the answer, set `quote` to the shortest region substring that contains the answer (still `answer ⊆ quote ⊆ region`).

- [ ] **Step 1:** Test: answer `nDCG@5`, cited p.21 prose, candidate p.7 table text containing `Results are presented using nDCG@5 metrics` → citation page becomes 7.

- [ ] **Step 2:** Test: question `... December 2023 ...`, cited region only has `December 2024` → abstain `unanswerable`, citations kept.

- [ ] **Step 3:** Test: question names Adam, cited ColPali page → abstain `unanswerable`.

- [ ] **Step 4:** Test: frozen-style CPI question without a conflicting year still answers.

- [ ] **Step 5:** `uv run pytest tests/test_canonical.py tests/test_answer_policy.py tests/test_verify.py -q`

**Hard-set targets:** citation page hit ≥ 8/12. h001/h007 must not keep a later restatement when the gold page is in the pool. Abstain recall ≥ 3/4 on the four adversarial rows. Verify pass on kept answers stays 1.0.

---

### Task 4: Operator eval and docs

**Files:**
- Modify: `docs/EVAL.md` (hard-set section: link this plan, paste the new table)
- Create: `eval/results/YYYY-MM-DD-hard/` and optionally `eval/results/YYYY-MM-DD-gpu/`

```bash
uv run --no-sync pageanchor eval --gold corpus/eval/hard_questions.jsonl \
  --modes text,visual,hybrid,hybrid+verify \
  --out eval/results/$(date +%F)-hard

uv run --no-sync pageanchor eval --gold corpus/eval/gold_questions.jsonl \
  --modes text,visual,hybrid,hybrid+verify,text+verify \
  --out eval/results/$(date +%F)-gpu
```

- [ ] **Step 1:** Hard D (`hybrid+verify`) vs `2026-09-11-hard`: citation page hit and region hit up; abstain recall up; verify pass still 1.0.

- [ ] **Step 2:** Frozen D: Recall@5 ≥ 0.833 (20/24). Abstain recall on the six unanswerables stays 1.0. Citation page hit must not fall more than one extra miss vs `2026-09-10-gpu` hybrid (0.846).

- [ ] **Step 3:** If frozen q016 / hard h008 still miss, stop. Do not add a third retrieve model. Record the miss in `docs/EVAL.md` as remaining.

**Pass bar (hard hybrid+verify):**

| Metric | Now | Target |
| --- | ---: | ---: |
| Recall@5 | 0.583 | ≥ 0.75 (9/12) |
| Region hit | 0.417 | ≥ 0.67 (8/12) |
| Citation page hit | 0.375 | ≥ 0.67 (8/12) |
| Abstain recall | 0.50 | ≥ 0.75 (3/4) |
| Verify pass | 1.000 | 1.000 |

Ship Phase 1 even if Phase 3 is not done: empty answers are better than a verified wrong box, but the product headline is the wrong box. Implement in order 0 → 1 → 2 → 3 so canonical repair has the gold page in the candidate pool.
