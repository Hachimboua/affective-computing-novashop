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
| 5 — robustness and reply quality | Done | `04c0ea9` |
| 6 — integration and documentation | Done | `7b5f787` |
| 7 — voice channel | Done | `3b3c038` |
| 8 — face channel | Skipped as directed | — |
| 9 — evaluation pipeline | Done (pipeline and tests); numbers wait for real ratings | see note below |
| 10 — ethics and limits | Done (draft with `[[CHECK]]` markers) | see note below |
| 11 — report draft | Done (scaffold to rewrite) | see note below |
| 12 — video script | Done (script and captions; values from your log) | see note below |
| 13 — presentation and Q&A | Done (outline, 6 Q&A files, verified drills) | see note below |
| 14 — packaging and final check | Done (`tools/package.py` tested with dummy files; `FINAL_CHECKLIST.md`) | see note below |

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

### Phase 6 gate

- Python 3.12.10: 89 tests passed; the contract test passed independently.
- Mandatory and practice scenarios: 8/8 passed with generated logs removed.
- Protected-file checksum regression: passed. The original ZIP verifier last
  reported zero mismatches across 29 files at the Phase 5 gate; no protected
  project files changed in Phase 6.
- Clean-copy checker: passed from Python 3.12.10 with the contract test, 89
  tests, and all 8 scenarios.
- Fresh integration generalization: 15/15 English/Portuguese cases passed.
  Logged detail lines stayed at or below 650 characters, including the
  long-evidence probe.
- Changed/created files passed UTF-8 and replacement-character checks; the
  root `requirements.txt` remains byte-identical.
- No engine output for the 88 evaluation messages was generated or displayed.

### Phase 7 gate

- Python 3.12.10: 102 tests passed, including the public contract and
  byte-identical protected-kit check.
- Clean-copy checker: passed with 102 tests and all 8 scenarios.
- Voice regressions cover synthetic pitch/noise/silence, quality-weighted
  confidence, louder-signal activity, speaker pitch invariance, malformed or
  unsupported audio, text-only fallback, and late fusion.
- Fifteen fresh English/Portuguese cases passed with the optional audio path;
  they are absent from `messages.csv` and prior test files.
- Voice references were generated from the six bundled WAV fixtures. NumPy
  remains optional, and the root `requirements.txt` was not changed.
- No engine output for the 88 evaluation messages was generated or displayed.

## Reply fixes and Phases 9–14 (written in the chat session with Claude, 25/11/2026)

The local coding agent was stopped after Phase 7. The remaining work was done
in a separate Claude chat session that read the files from this folder, made
the changes in a copy, tested them, and wrote the files back. Commit them
yourself (see the commit commands in the chat).

- **Reply fixes** (`engine/policy/replies.py`, `engine/perception/intents.py`,
  `engine/state/tracker.py`, `engine/engine.py`, `tests/test_replies.py`):
  action-aware bilingual replies (the clarification cap now offers a person in
  the reply too), Portuguese payment cues (*paguei, cobrado, cobraram,
  débito…*), the conversation's earlier topic used for follow-ups without a
  topic (`context_intent`, logged only when used), and the generic
  "I can help with a NovaShop question" replaced by a concrete next step.
- **Phase 9** (`engine/evaluation/evaluate.py`, `metrics.py`,
  `baselines/starter_engine.py`, `tests/test_metrics.py`,
  `tests/test_evaluate.py`): five variants (starter, full, no negation, no
  sarcasm, no smoothing); metrics checked against Krippendorff's published
  example (0.849) and the standard Fleiss example (0.210), and against scipy,
  statsmodels and the `krippendorff` package; exits with code 2 and writes
  nothing without ratings; `--voice-check` passes 4/4
  (`engine/evaluation/results/voice_check.json`).
- **Phases 10–13:** `ethics/ethics.md`, consent-form wording marked
  `[[CONFIRM]]`, `report/report_draft.md`, `report/contribution_statement.md`,
  `video/script.md`, `video/captions.srt`, `presentation/outline.md`,
  `qa/topic1.md`…`topic5.md`, `qa/whole_system.md`, study notes in
  `topics/topic3.md` and `topics/topic5.md`. Every live-change drill was run
  on new sentences before being written down.
- **Phase 14:** `tools/package.py` (refuses placeholder group id and missing
  report/video/log; checks the kit byte for byte; runs the contract test, all
  tests and all scenarios in the staged `code/`), `tools/verify_kit.py` now
  accepts a folder, `FINAL_CHECKLIST.md`.

### Final gate (chat session)

- Python 3.9.25 without numpy: 131 tests passed (8 voice tests skipped).
- Python 3.13 with numpy: 131 tests passed.
- All 8 scenarios: no PROBLEMS or ERROR lines.
- `verify_kit.py`: 0 mismatches across 29 protected files.
- Packaging dry run (dummy report and video): kit check, contract test,
  131 tests and all scenarios passed inside the staged `code/`; the zip held
  only `report.pdf`, `video_demo.mp4` and `code/` (no notes, caches or extra
  logs).
- Independent rehearsal of 33 new messages: 33/33 actions as expected, no
  contradictory replies.
- No engine output for the 88 evaluation messages was shown.

### What only you can do

See `FINAL_CHECKLIST.md`: tier review, ratings, teacher answers, AI-log fields,
rewriting the report and exporting `report.pdf`, recording the video,
packaging with the real group id, pushing and delivering.
