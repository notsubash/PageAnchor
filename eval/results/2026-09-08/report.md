# Retrieval ablation

A/B/C keep the generator answer even when a citation quote fails verify. D / D-lite abstain on any failed quote. Verify pass rate is computed on citations attached to kept (non-abstain) answers.

| system | recall@5 | citation page hit | verify pass | abstain P | abstain R | p50 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A text | 0.708 | 0.556 | 1.000 | 0.500 | 1.000 | 1825 |
| D-lite text+verify | 0.708 | 0.556 | 1.000 | 0.500 | 1.000 | 1825 |

Answerable questions whose citations missed the gold page (mode `text`):

| id | type | cited | gold |
| --- | --- | --- | --- |
| q001 | plain_text | arxiv-2407-colpali p.2 | arxiv-2407-colpali p.1 |
| q004 | plain_text | arxiv-2204-layoutlmv3 p.2 | arxiv-2204-layoutlmv3 p.1 |
| q011 | table | arxiv-1804-glue p.8 | arxiv-1804-glue p.2 |
| q012 | table | arxiv-2407-colpali p.21 | arxiv-2407-colpali p.7 |
| q016 | figure | nasa-roman-slides p.29 | nasa-roman-slides p.1 |
| q017 | figure | arxiv-2204-layoutlmv3 p.6 | arxiv-2204-layoutlmv3 p.1 |
| q020 | layout | nasa-roman-slides p.32 | nasa-roman-slides p.2 |
| q022 | layout | arxiv-2407-colpali p.7 | arxiv-2407-colpali p.3 |

Example: `q011` (table) answered '8.5k' citing arxiv-1804-glue p.8; gold is arxiv-1804-glue p.2.
Verify only checks that the quote is a normalized substring of the cited region. It does not check that the quote entails the answer.

