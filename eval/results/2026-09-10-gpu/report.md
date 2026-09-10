# Retrieval ablation

A/B/C keep the generator answer even when a citation quote fails verify. D / D-lite abstain on any failed quote. Verify pass rate is computed on citations attached to kept (non-abstain) answers.

| system | recall@5 | citation page hit | verify pass | abstain P | abstain R | p50 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A text | 0.708 | 0.909 | 1.000 | 0.316 | 1.000 | 1346 |
| B visual | 0.875 | 0.917 | 1.000 | 0.333 | 1.000 | 1503 |
| C hybrid | 0.875 | 0.846 | 1.000 | 0.353 | 1.000 | 1486 |
| D hybrid+verify | 0.875 | 0.846 | 1.000 | 0.353 | 1.000 | 1486 |
| D-lite text+verify | 0.708 | 0.909 | 1.000 | 0.316 | 1.000 | 1346 |

Recall@5 on answerable gold by type:

| type | n | text | visual | hybrid |
| --- | ---: | ---: | ---: | ---: |
| table | 6 | 0.667 | 0.833 | 0.833 |
| figure | 6 | 0.667 | 0.833 | 0.833 |
| layout | 6 | 0.833 | 0.833 | 0.833 |
| plain_text | 6 | 0.667 | 1.000 | 1.000 |


Answerable questions whose citations missed the gold page (mode `text`):

| id | type | cited | gold |
| --- | --- | --- | --- |
| q017 | figure | arxiv-2204-layoutlmv3 p.2 | arxiv-2204-layoutlmv3 p.1 |

Answerable questions whose citations missed the gold page (mode `visual`):

| id | type | cited | gold |
| --- | --- | --- | --- |
| q004 | plain_text | arxiv-2204-layoutlmv3 p.2 | arxiv-2204-layoutlmv3 p.1 |

Answerable questions whose citations missed the gold page (mode `hybrid`):

| id | type | cited | gold |
| --- | --- | --- | --- |
| q012 | table | arxiv-2407-colpali p.4 | arxiv-2407-colpali p.7 |
| q020 | layout | nasa-roman-slides p.32 | nasa-roman-slides p.2 |

Example: `q012` (table) answered 'nDCG@5' citing arxiv-2407-colpali p.4; gold is arxiv-2407-colpali p.7.
Verify only checks that the quote is a normalized substring of the cited region. It does not check that the quote entails the answer.


Torch 2.11.0+cu128 on NVIDIA GeForce RTX 4070 Ti SUPER.
