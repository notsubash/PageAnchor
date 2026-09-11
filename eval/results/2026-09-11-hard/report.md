# Retrieval ablation

A/B/C keep the generator answer even when a citation quote fails verify. D / D-lite abstain on any failed quote. Verify pass rate is computed on citations attached to kept (non-abstain) answers.

| system | recall@5 | citation page hit | verify pass | abstain P | abstain R | p50 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A text | 0.417 | 0.333 | 1.000 | 0.400 | 0.500 | 2043 |
| B visual | 0.583 | 0.375 | 1.000 | 0.333 | 0.500 | 2315 |
| C hybrid | 0.583 | 0.375 | 1.000 | 0.333 | 0.500 | 2416 |
| D hybrid+verify | 0.583 | 0.375 | 1.000 | 0.333 | 0.500 | 2416 |

| system | region hit | answer match | quote support |
| --- | ---: | ---: | ---: |
| A text | 0.417 | 0.667 | 1.000 |
| B visual | 0.417 | 0.750 | 1.000 |
| C hybrid | 0.417 | 0.750 | 1.000 |
| D hybrid+verify | 0.417 | 0.750 | 1.000 |

Abstain counts by gold slice and reason:

| system | slice | unanswerable | verify_failed | unsupported | generator_invalid | no_hits |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| A text | answerable | 3 | 0 | 0 | 0 | 0 |
| A text | unanswerable | 2 | 0 | 0 | 0 | 0 |
| B visual | answerable | 4 | 0 | 0 | 0 | 0 |
| B visual | unanswerable | 2 | 0 | 0 | 0 | 0 |
| C hybrid | answerable | 4 | 0 | 0 | 0 | 0 |
| C hybrid | unanswerable | 2 | 0 | 0 | 0 | 0 |
| D hybrid+verify | answerable | 4 | 0 | 0 | 0 | 0 |
| D hybrid+verify | unanswerable | 2 | 0 | 0 | 0 | 0 |


Recall@5 on answerable gold by type:

| type | n | text | visual | hybrid |
| --- | ---: | ---: | ---: | ---: |
| layout | 3 | 0.667 | 0.667 | 0.667 |


Answerable questions whose citations missed the gold page (mode `text`):

| id | type | cited | gold |
| --- | --- | --- | --- |
| h001 | lexical_gap | arxiv-2407-colpali p.6 | arxiv-2407-colpali p.3 |
| h003 | lexical_gap | arxiv-2407-colpali p.7 | arxiv-2407-colpali p.3 |
| h004 | layout | arxiv-2407-colpali p.7 | arxiv-2407-colpali p.3 |
| h006 | table_cell | cdc-mmwr-7331a1 p.1 | cdc-mmwr-7331a1 p.3 |
| h007 | table_cell | arxiv-2407-colpali p.10 | arxiv-2407-colpali p.7 |
| h009 | figure_only | arxiv-2204-layoutlmv3 p.4 | arxiv-2204-layoutlmv3 p.1 |

Answerable questions whose citations missed the gold page (mode `visual`):

| id | type | cited | gold |
| --- | --- | --- | --- |
| h001 | lexical_gap | arxiv-2407-colpali p.6 | arxiv-2407-colpali p.3 |
| h003 | lexical_gap | arxiv-2407-colpali p.7 | arxiv-2407-colpali p.3 |
| h004 | layout | arxiv-2407-colpali p.7 | arxiv-2407-colpali p.3 |
| h006 | table_cell | cdc-mmwr-7331a1 p.1 | cdc-mmwr-7331a1 p.3 |
| h007 | table_cell | arxiv-2407-colpali p.21 | arxiv-2407-colpali p.7 |

Answerable questions whose citations missed the gold page (mode `hybrid`):

| id | type | cited | gold |
| --- | --- | --- | --- |
| h001 | lexical_gap | arxiv-2407-colpali p.6 | arxiv-2407-colpali p.3 |
| h003 | lexical_gap | arxiv-2407-colpali p.7 | arxiv-2407-colpali p.3 |
| h004 | layout | arxiv-2407-colpali p.7 | arxiv-2407-colpali p.3 |
| h006 | table_cell | cdc-mmwr-7331a1 p.1 | cdc-mmwr-7331a1 p.3 |
| h007 | table_cell | arxiv-2407-colpali p.21 | arxiv-2407-colpali p.7 |

Example: `h001` (lexical_gap) answered 'Paligemma-3B' citing arxiv-2407-colpali p.6; gold is arxiv-2407-colpali p.3.
Nested verify checks quote-in-region and answer-in-quote. A matching string on the wrong page is still a citation-page miss.


Torch 2.11.0+cu128 on NVIDIA GeForce RTX 4070 Ti SUPER.
