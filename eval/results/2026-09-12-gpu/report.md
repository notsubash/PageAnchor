# Retrieval ablation

A/B/C keep the generator answer even when a citation quote fails verify. D / D-lite abstain on any failed quote. Verify pass rate is computed on citations attached to kept (non-abstain) answers.

| system | recall@5 | citation page hit | verify pass | abstain P | abstain R | p50 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A text | 0.833 | 0.706 | 0.938 | 0.375 | 1.000 | 2831 |
| B visual | 0.958 | 0.684 | 0.944 | 0.429 | 1.000 | 5637 |
| C hybrid | 0.917 | 0.684 | 0.947 | 0.429 | 1.000 | 6180 |
| D hybrid+verify | 0.917 | 0.684 | 1.000 | 0.400 | 1.000 | 6180 |
| D-lite text+verify | 0.833 | 0.706 | 0.938 | 0.375 | 1.000 | 2831 |

| system | region hit | answer match | quote support |
| --- | ---: | ---: | ---: |
| A text | 0.458 | 0.000 | 0.938 |
| B visual | 0.500 | 0.000 | 1.000 |
| C hybrid | 0.542 | 0.000 | 1.000 |
| D hybrid+verify | 0.542 | 0.000 | 1.000 |
| D-lite text+verify | 0.458 | 0.000 | 0.938 |

Abstain counts by gold slice and reason:

| system | slice | unanswerable | verify_failed | unsupported | generator_invalid | no_hits |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| A text | answerable | 10 | 0 | 0 | 0 | 0 |
| A text | unanswerable | 6 | 0 | 0 | 0 | 0 |
| B visual | answerable | 8 | 0 | 0 | 0 | 0 |
| B visual | unanswerable | 6 | 0 | 0 | 0 | 0 |
| C hybrid | answerable | 8 | 0 | 0 | 0 | 0 |
| C hybrid | unanswerable | 6 | 0 | 0 | 0 | 0 |
| D hybrid+verify | answerable | 8 | 1 | 0 | 0 | 0 |
| D hybrid+verify | unanswerable | 6 | 0 | 0 | 0 | 0 |
| D-lite text+verify | answerable | 10 | 0 | 0 | 0 | 0 |
| D-lite text+verify | unanswerable | 6 | 0 | 0 | 0 | 0 |


Recall@5 on answerable gold by type:

| type | n | text | visual | hybrid |
| --- | ---: | ---: | ---: | ---: |
| table | 6 | 1.000 | 1.000 | 1.000 |
| figure | 6 | 0.833 | 0.833 | 1.000 |
| layout | 6 | 0.833 | 1.000 | 0.833 |
| plain_text | 6 | 0.667 | 1.000 | 0.833 |


Answerable questions whose citations missed the gold page (mode `text`):

| id | type | cited | gold |
| --- | --- | --- | --- |
| q003 | plain_text | arxiv-1804-glue p.12 | arxiv-1606-squad p.1 |
| q004 | plain_text | arxiv-2407-colpali p.13 | arxiv-2204-layoutlmv3 p.1 |
| q010 | table | cdc-mmwr-7331a1 p.2 | cdc-mmwr-7331a1 p.3 |
| q020 | layout | nasa-roman-slides p.32 | nasa-roman-slides p.2 |
| q022 | layout | arxiv-2407-colpali p.7 | arxiv-2407-colpali p.3 |

Answerable questions whose citations missed the gold page (mode `visual`):

| id | type | cited | gold |
| --- | --- | --- | --- |
| q001 | plain_text | arxiv-2407-colpali p.21 | arxiv-2407-colpali p.1 |
| q003 | plain_text | arxiv-1804-glue p.12 | arxiv-1606-squad p.1 |
| q004 | plain_text | arxiv-2407-colpali p.13 | arxiv-2204-layoutlmv3 p.1 |
| q010 | table | cdc-mmwr-7331a1 p.2 | cdc-mmwr-7331a1 p.3 |
| q020 | layout | nasa-roman-slides p.32 | nasa-roman-slides p.2 |
| q022 | layout | arxiv-2407-colpali p.7 | arxiv-2407-colpali p.3 |

Answerable questions whose citations missed the gold page (mode `hybrid`):

| id | type | cited | gold |
| --- | --- | --- | --- |
| q001 | plain_text | arxiv-2407-colpali p.21 | arxiv-2407-colpali p.1 |
| q003 | plain_text | arxiv-1804-glue p.12 | arxiv-1606-squad p.1 |
| q004 | plain_text | arxiv-2407-colpali p.13 | arxiv-2204-layoutlmv3 p.1 |
| q010 | table | cdc-mmwr-7331a1 p.2 | cdc-mmwr-7331a1 p.3 |
| q020 | layout | nasa-roman-slides p.32 | nasa-roman-slides p.2 |
| q022 | layout | arxiv-2407-colpali p.7 | arxiv-2407-colpali p.3 |

Example: `q010` (table) answered '3,090,582' citing cdc-mmwr-7331a1 p.2; gold is cdc-mmwr-7331a1 p.3.
Nested verify checks quote-in-region and answer-in-quote. A matching string on the wrong page is still a citation-page miss.


Torch 2.11.0+cu128 on NVIDIA GeForce RTX 4070 Ti SUPER.
