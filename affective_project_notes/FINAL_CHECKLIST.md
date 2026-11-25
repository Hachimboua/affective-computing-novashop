# Final checklist (mapped to the Evaluation Guide)

✅ = done and verified · ⏳ = only you can do it · ❌ = not done

## Work: engine and documentation (10%)

| Criterion (weight) | Status | Evidence |
|---|---|---|
| Text perception: valence, activity, confidence, label; dominance | ✅ | `engine/perception/`, `engine/affect/space.py`; `tests/test_perception.py` |
| State over time | ✅ | `engine/state/tracker.py`; `tests/test_state.py`; M2 scenario test |
| Six actions chosen from the state | ✅ | `engine/policy/policy.py` (rules R0–R7); `tests/test_policy.py`, `tests/test_rehearsal.py` (40/40) |
| Robustness: uncertain, short, ambiguous, sarcastic, other language | ✅ | `tests/test_robustness.py`, `tests/test_replies.py`; safety net in `engine/engine.py` |
| Quality: design, readable code, tests, README that works (30%) | ✅ | 131 tests (Python 3.9 without numpy, 3.12/3.13 with numpy); all settings commented in `config.py`; `engine/README.md` |
| Evaluation: SAM comparison, metrics, error analysis (20%) | ⏳ pipeline ✅, numbers need ratings | `engine/evaluation/evaluate.py`, `metrics.py`; run `--split dev`, then `--split test` |
| AI log and contribution statement (10%) | ⏳ | Fill *What I changed* / *How I verified it* in `AI_LOG.md`; complete `report/contribution_statement.md` |

## Report (10%)

| Criterion | Status | Evidence |
|---|---|---|
| Correctness and depth (35%) | ⏳ | `report/report_draft.md`: rewrite in your own words, add evaluation numbers |
| One section per topic (25%) | ⏳ draft ✅ | Sections 2–6 of the draft |
| Difficulties and issues (15%) | ⏳ draft ✅ | Section 8 + `DIFFICULTIES.md` |
| Structure and length 7–12 pages (15%) | ⏳ | Page budget in the draft (~5,200 words) |
| Ethics and limits (10%) | ⏳ draft ✅ | `ethics/ethics.md`; check every `[[CHECK]]` |

## Video (8%) and code demo (12%)

| Criterion | Status | Evidence |
|---|---|---|
| M1–M4 in order, results visible | ⏳ | `video/script.md` |
| Full path from terminal to results, log shown | ⏳ | Script 0:00–0:30 and 4:15–5:00 |
| Commentary and clarity | ⏳ | Narration in the script; `video/captions.srt` |
| ≤ 5 minutes, readable | ⏳ | ffmpeg and ffprobe commands in the script |
| Code runs from the README on another computer, offline | ✅ | `clean_copy_check.py`; `package.py` re-runs everything in the staged `code/` |
| Contract respected; hidden tests | ✅ | Kit contract test; rehearsal 40/40; independent rehearsal 33/33 |
| Kit files unchanged | ✅ | `verify_kit.py`: 0 mismatches across 29 files; raw-byte checksum test |

## Optional channel: voice (+2)

| Condition | Status | Evidence |
|---|---|---|
| Integrated with the text estimate | ✅ | `engine/affect/fusion.py` |
| Shown working in the video | ⏳ | Script 4:15–5:00 (calm vs agitated) |
| Tested | ✅ | `tests/test_voice.py`; `evaluate --voice-check` passes 4/4 |
| Limits documented | ✅ | `topics/topic2.md`, report section 3, `ethics/ethics.md` |
| You can explain it | ⏳ | `qa/topic2.md` (framing, windowing, MFCC, pitch) |

## Class work and presentation (60%)

| Item | Status | Evidence |
|---|---|---|
| Explain and change every part live | ⏳ | `qa/topic1.md` … `topic5.md`, `qa/whole_system.md`: practise every drill |
| 15-minute presentation | ⏳ | `presentation/outline.md` |

## Delivery

| Step | Status |
|---|---|
| Teacher confirms solo project, deadline, `tests/` and README placement, OFFER_HUMAN vs ESCALATE | ⏳ (`OPEN_QUESTIONS.md`) |
| Tier review in the lexicon sheet, then sync and tests | ⏳ |
| Your own SAM ratings, then 2–4 volunteers | ⏳ |
| Run the evaluation (dev, then test) and add the numbers to the report | ⏳ |
| Export `report.pdf`, record and compress `video_demo.mp4`, keep the demo log | ⏳ |
| `package.py` with your real group id | ⏳ |
| `git push`, upload to Moodle before the deadline, keep the confirmation | ⏳ |
