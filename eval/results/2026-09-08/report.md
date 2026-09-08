# Text retrieve eval

A keeps the generator answer even when a citation quote fails verify. D-lite abstains on any failed quote. Verify pass rate is computed on citations attached to kept (non-abstain) answers.

| system | recall@5 | citation page hit | verify pass | abstain P | abstain R | p50 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A text | 0.708 | 0.556 | 1.000 | 0.500 | 1.000 | 1825 |
| D-lite text+verify | 0.708 | 0.556 | 1.000 | 0.500 | 1.000 | 1825 |

On this freeze the generator did not keep unverified quotes, so A and D-lite match. D-lite is still the product policy. Abstain recall is 1.0 on the six unanswerable items; precision is 0.5 because six answerable questions were also refused after retrieve (model `unanswerable` or empty citations). Recall@5 is 17/24. Citation page hit is among answerable rows that produced citations.
