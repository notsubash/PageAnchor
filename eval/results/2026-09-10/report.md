# Retrieval ablation

A/B/C keep the generator answer even when a citation quote fails verify. D / D-lite abstain on any failed quote. Verify pass rate is computed on citations attached to kept (non-abstain) answers.

| system | recall@5 | citation page hit | verify pass | abstain P | abstain R | p50 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A text | 0.708 | 0.917 | 0.917 | 0.333 | 1.000 | 1819 |
| B visual | 0.875 | 0.923 | 1.000 | 0.353 | 1.000 | 2104 |
| C hybrid | 0.875 | 0.923 | 1.000 | 0.353 | 1.000 | 2675 |
| D hybrid+verify | 0.875 | 0.923 | 1.000 | 0.353 | 1.000 | 2675 |
| D-lite text+verify | 0.708 | 0.917 | 1.000 | 0.316 | 1.000 | 1819 |

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
| q012 | table | arxiv-2407-colpali p.21 | arxiv-2407-colpali p.7 |

Answerable questions whose citations missed the gold page (mode `hybrid`):

| id | type | cited | gold |
| --- | --- | --- | --- |
| q012 | table | arxiv-2407-colpali p.4 | arxiv-2407-colpali p.7 |

Example: `q012` (table) answered 'nDCG@5' citing arxiv-2407-colpali p.21; gold is arxiv-2407-colpali p.7.
Verify only checks that the quote is a normalized substring of the cited region. It does not check that the quote entails the answer.

