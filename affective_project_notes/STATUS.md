# Project status

## Part A — review fixes

| Item | Status | Commit |
|---|---|---|
| A1 — restore byte-identical kit files | Done | `af638ab` |
| A2 — neutral confidence for plain questions | Done | `e64df3c` |
| A3 — short and shouted messages | Done | `2f3dd34` |
| A4 — safety-specific emergency guidance | Done | `82c6d19` |
| A5 — non-closing replies | Done | `5e79070` |
| Part A verification gate | Done | Additional fresh regression coverage committed separately |

### Part A gate results

- Python 3.12: 79 tests passed. Python 3.9 is unavailable in this environment.
- Mandatory and practice scenarios: 8/8 passed; generated session logs removed.
- Protected kit verification: zero mismatches across 29 files.
- Clean-copy simulation: 79 tests and 8/8 scenarios passed.
- Fresh generalization: 15/15 English/Portuguese cases and 4/4 short Latin
  clarification cases passed. The sentences were absent from the evaluation
  CSV and existing tests before being added as regressions.
- No engine output for the 88 evaluation messages was generated or displayed.

## Part B — phase progress

| Phase | Status | Commit |
|---|---|---|
| 5 — robustness and reply quality | Done | — |
| 6 — integration and documentation | In progress | — |
| 7 — voice channel | Not started; gated on Phase 6 | — |
| 8 — face channel | Skipped as directed | — |
| 9 — evaluation pipeline | Not started; no real ratings available | — |
| 10 — ethics and limits | Not started | — |
| 11 — report draft | Not started | — |
| 12 — video script | Not started | — |
| 13 — presentation and Q&A | Not started | — |
| 14 — packaging and final check | Not started | — |

The evaluation messages remain unavailable for tuning and per-message output.
Real SAM ratings, teacher answers, the group identifier, and the delivery
deadline remain outstanding.

### Phase 5 gate

- Python 3.12: 87 tests passed.
- Mandatory and practice scenarios: 8/8 passed with generated logs removed.
- Protected kit verification: zero mismatches across 29 files.
- Clean-copy simulation: 87 tests and 8/8 scenarios passed.
- Fresh English/Portuguese generalization: 15/15 passed; the 40-message
  rehearsal passed 40/40 across eight conversations and reached all six
  actions.
- The 5,000-word local benchmark measured a 40.7-ms median and 42.6-ms
  maximum across five fresh-engine runs, below the 100-ms test budget.
- No engine output for the 88 evaluation messages was generated or displayed.
