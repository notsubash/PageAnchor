# Retrieve-only diagnostic

No generator. Rank is the 1-based position of gold `(doc_id, page)` in the top-20 hits. `rrf3` is Reciprocal Rank Fusion of text + visual + BM25 lists (not wired into `search_hybrid` yet).

| mode | Recall@5 | Recall@10 | Recall@20 |
| --- | ---: | ---: | ---: |
| text | 0.417 | 0.750 | 0.917 |
| visual | 0.583 | 0.667 | 1.000 |
| hybrid | 0.583 | 0.750 | 1.000 |
| bm25 | 0.833 | 0.833 | 0.833 |
| rrf3 | 0.667 | 0.833 | 0.917 |

| id | gold | text | visual | hybrid | bm25 | rrf3 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| h001 | arxiv-2407-colpali p.3 | 14 | 15 | 14 | miss | 14 |
| h002 | arxiv-2407-colpali p.3 | 5 | 4 | 4 | 3 | 4 |
| h003 | arxiv-2407-colpali p.3 | 6 | 14 | 10 | 3 | 4 |
| h004 | arxiv-2407-colpali p.3 | 13 | 14 | 13 | 1 | 8 |
| h005 | arxiv-1804-glue p.2 | 8 | 1 | 3 | 3 | 2 |
| h006 | cdc-mmwr-7331a1 p.3 | 4 | 5 | 5 | 3 | 4 |
| h007 | arxiv-2407-colpali p.7 | 6 | 9 | 8 | 3 | 6 |
| h008 | nasa-roman-slides p.1 | miss | 12 | 20 | miss | miss |
| h009 | arxiv-2204-layoutlmv3 p.1 | 8 | 1 | 4 | 1 | 2 |
| h010 | arxiv-1412-adam p.2 | 5 | 1 | 2 | 1 | 1 |
| h011 | bls-cpi-20250115 p.1 | 1 | 1 | 1 | 1 | 1 |
| h012 | bls-cpi-20250115 p.1 | 1 | 1 | 1 | 2 | 1 |

Gold page in hybrid@20: 12/12
Gold page in BM25@20: 10/12
Gold page in 3-way RRF@20: 11/12

Gate: gold pages are usually inside current hybrid@20. Phase 1 is rerank + wider `select_evidence` pool, plus same-doc fill / query cues for the remaining @5 misses.

Torch 2.11.0+cu128 on NVIDIA GeForce RTX 4070 Ti SUPER.


Operator notes:

- text / visual / hybrid via `POST /v1/search` on the running API; BM25 in-process. Avoids a second ColQwen2 load.
- `search_hybrid` fuses 60-length lists. h008 is visual rank 12 and hybrid rank 20, but missing from `rrf3` of the k=20 lists because BM25/text overlap crowds the fused 20.
- hybrid@5 is 7/12 (0.583), matching `eval/results/2026-09-11-hard`. `rrf3`@5 is 8/12 by moving h003 from hybrid rank 10 to 4.
- Remaining hybrid@5 misses: h001 (14), h003 (10), h004 (13), h007 (8), h008 (20). Phase 1 should put those in `hits[:5]` with 3-way RRF, same-doc fill, and query cues.
