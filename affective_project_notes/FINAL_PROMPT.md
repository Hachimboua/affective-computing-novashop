# FINAL PROMPT — Fix Phase 4 issues, then complete Phases 5 to 14 (NovaShop affective engine, solo project)

<!--
BEFORE PASTING
1. The agent must be open in C:\Users\houci\Documents\AC solo (the folder containing affective_project and affective_project_notes).
2. Check Section 0 and change anything that is not right (deadline, group id, ratings).
3. Paste this whole file as one message.
-->

## 0. Settings

- Workspace: `C:\Users\houci\Documents\AC solo`. Never read, change or commit anything in `C:\Users\houci\Documents\AC project` (except reading the original kit zip in step A1).
- Group id: `GroupXX` (only used for the zip name in Phase 14)
- My own SAM ratings are complete: `no`
- Real rating files in `affective_project/engine/evaluation/ratings/`: `0`
- Build the optional voice channel: `yes` (only after Phase 6 passes its gate)
- Local git commit after each fix and each phase: `yes` (never push)
- Deadline: `{{date and time, or "unknown, as soon as possible"}}`
- Teacher answers received: `none yet`

---

## 1. Your job

First save this prompt verbatim to `affective_project_notes/FINAL_PROMPT.md`. Then:

1. **Part A:** fix the five problems found in the Phase 4 review, committing each separately.
2. **Part B:** complete Phases 5 to 14 **in one run, without pausing between phases**. Stop only for a hard stop (Section 6). After each phase, run the verification gate (Section 5) and do not move on until it passes.

The detailed specification of each phase is in `affective_project_notes/MASTER_PROMPT.md`. **This prompt overrides it** wherever they differ, and so do the decisions recorded in `KIT_NOTES.md`, `OPEN_QUESTIONS.md` and `DIFFICULTIES.md`. Read those first.

I work alone and must be able to explain and change every part of the system in front of the teacher. Keep code simple, keep every threshold in `engine/config.py` with a comment on its trade-off, and write the study notes in Section 7.

---

## 2. Absolute rules

1. **Never weaken a test to make it pass.** If a test fails, fix the code or the data. If you believe a test itself is wrong, stop and explain why (hard stop H4). This applies especially to `tests/test_kit_unchanged.py` and `tests/test_contract.py`.
2. **Protected kit files must stay byte-identical to the original zip:** `affective_project/README.md`, `requirements.txt`, `run_app.py`, `run_scenario.py`, `harness/**`, `scenarios/**`, `assets/**`, `logs/README.txt`, `tests/test_contract.py`. Never edit, re-save, reformat, normalise line endings or commit changes to them. Never add files at the top level of `affective_project/`.
3. Change code only inside `affective_project/engine/`; add test files only in `affective_project/tests/`. Notes, drafts and dev-only tools go in `affective_project_notes/` (not in the delivered zip). Nothing in `affective_project/` may read or import anything from `affective_project_notes/`.
4. Plain Python 3.9-compatible code (no `match`, no `X | Y` unions, no `zip(strict=)`). Standard library only for the mandatory engine; numpy is allowed but must be import-guarded with a graceful fallback, because the teacher's offline machine may not have it. `requirements.txt` stays unchanged.
5. Always read and write text files with `encoding="utf-8"` explicitly. Never write data through console output or redirection.
6. Never fabricate SAM ratings, metrics, results, difficulties, AI-log entries or contribution statements. In `AI_LOG.md`, fill only *What I asked for* and *What the AI produced*; leave *What I changed* and *How I verified it* empty for me.
7. My ratings are not done: never show me per-message valence, activity, label or action for any of the 88 messages in `engine/evaluation/data/messages.csv` (scenario messages included). Report scenarios as pass/fail against their expected behaviour only. Use your own new sentences for examples. Never run the engine on the `test` split before Phase 9.
8. Never put scenario texts or their expected outputs inside the engine.
9. Every real problem goes into `DIFFICULTIES.md` (problem, cause, fix).
10. Git: commit locally after each fix and each phase; never push, never amend, never rewrite history, never force anything.

---

## 3. Decisions already made (do not change)

- Entry point `engine.engine.Engine`; contract keys `valence`, `activity`, `confidence`, `label`, `action`, `reply`, plus `dominance`, `flags`, `details`; plain Python types; never NaN; never raise.
- Labels: `neutral, calm, joy, anger, frustration, fear, sadness` (engine and `rate.py`). Low confidence keeps the nearest label plus the flag `low_confidence`.
- Languages: English and Portuguese; anything else is flagged `unsupported_language`.
- Lexicon entries carry a tier; tier values are in `config.TIER_VAD`. Tier choices are synced only by me with `py -3.12 -m engine.tools.sync_lexicon_tiers <sheet>`. Do not change tier values or assignments without asking (hard stop H3), except adding missing words, which you must list in the final report.
- Provisional action semantics (until the teacher answers): **OFFER_HUMAN** = proactively offer a transfer to a person (explicit human request, repeated unresolved problem, persistent negative state). **ESCALATE** = urgent priority handover (legal or authority threat such as lawyer, court, consumer protection, *livro de reclamações*, chargeback, police; abuse; safety; very negative and highly activated state for 2+ turns; a human request made while already very angry).
- Student run and test instructions live in `affective_project/engine/README.md`; the kit README stays unchanged.

---

## Part A — Fixes from the Phase 4 review (do these first, one commit each)

**A1. Restore byte-identical kit files.**

- Extract `C:\Users\houci\Documents\AC project\Student_Kit_to_share_with_students.zip` into a new temporary folder outside both repositories.
- Copy byte for byte over every protected file listed in rule 2 (including `assets/audio/*`). Do not open and re-save them in an editor.
- Revert `tests/test_kit_unchanged.py` so it hashes **raw bytes** (no line-ending normalisation) with the original Phase 0 hashes, and restore `affective_project_notes/kit_checksums.txt` accordingly.
- Run `git config core.autocrlf false` in this repository (`.gitattributes` with `* -text` already exists).
- Add `affective_project_notes/tools/verify_kit.py`: given the zip path, it compares the SHA-256 of every protected file with the zip and prints mismatches. Run it; it must report zero mismatches.
- Commit: `Restore byte-identical kit files`. In `DIFFICULTIES.md`, record what happened: line endings were converted during a git rebase before `.gitattributes` existed, a later commit stored the converted files, and the checksum test had been weakened to hide it.

**A2. Plain questions must not ask for clarification.** A well-formed sentence in a supported language (3+ words) with no affective words and no recognised intent must get neutral-evidence confidence (`NEUTRAL_CONFIDENCE`), not the minimum. It should lead to `ANSWER` with a helpful generic reply that invites the needed detail (for example, the order number). Regression sentences: "Do you ship to the Azores?", "Can I pay with PayPal?", "What time do you close on Sundays?", "Posso pagar com MB Way?", "Têm loja física no Porto?". Commit: `Neutral questions get neutral confidence`.

**A3. Short or shouted English is not a foreign language.**

- Do not flag `unsupported_language` for 1–2-word Latin-script messages or for all-caps English. Use `short_message` and the clarification reply instead. "meh", "eh", "??", "uhh" and "k" must never get the "please write in English or Portuguese" reply.
- Add *unbelievable*, *ridiculous*, *absurd*, *nonsense* and *joke* (as in "this is a joke") to the lexicon if missing, with a tier, and list them in the final report.
- In a conversation whose state is already very negative, a short shouted message (caps or `!!!`) must lead to `OFFER_HUMAN` or `ESCALATE`, not clarification. Regression conversation: "Hello, I'm checking on my tablet order." → "It's now a week late." → "This is getting really annoying, nobody tells me anything." → "I'm absolutely furious, this is the worst service ever!!!" → "UNBELIEVABLE. STILL NOTHING!!!" (the last turn must be `OFFER_HUMAN` or `ESCALATE`).
- Commit: `Short and shouted messages handled in context`.

**A4. Only safety mentions emergency services.** Only the `safety` flag may produce the sentence about immediate danger or emergency services. Legal, threat and anger escalations get a reply about urgent handover to a person (in EN or PT). Add tests. Commit: `Separate safety replies from escalation replies`.

**A5. No contradictory replies.** Never combine closing-thanks text ("glad I could help") with a negative, sarcastic or non-closing message. "Thanks for nothing." must not contain "glad I could help". Add a test that checks, across your rehearsal set, that no `ANSWER_EMPATHIC`, `OFFER_HUMAN` or `ESCALATE` reply contains closing phrases. Commit: `No closing text in non-closing replies`.

After Part A, run the full gate (Section 5), then continue with Part B without pausing.

---

## Part B — Phases 5 to 14 (one run, no pauses)

**Phase 5 — Robustness and reply quality**

- Everything in MASTER_PROMPT Phase 5, including the safety net in `Engine.process` (any internal error returns a valid fallback with flag `internal_error`) and `ENGINE_STRICT=1` re-raising in tests.
- Reply quality pass: every intent (order status, delivery delay, damaged/defective, wrong item, refund/return, payment, account, product question) gets a specific, helpful reply in EN and PT that names a concrete next step (for example, asking for the order number, or offering to start a return). No reply may repeat the same generic sentence twice in a row in one conversation. Empathic replies name the problem. No invented order statuses or promises.
- Build a 40-message **hidden-test rehearsal** of new conversations (EN and PT, not in `messages.csv`, not in existing tests) covering all six actions, sarcasm, negation, short messages, other languages, legal threats and closings. Save it as `tests/test_rehearsal.py` with the acceptable actions per message. Report the pass rate in the final report (target: at least 90%).

**Phase 6 — Integration and documentation**

- Complete `engine/README.md`: requirements (Python 3.9+, standard library; numpy optional for voice), how to run the app, run a scenario, run the tests, run the evaluation, run the lexicon sync; an ASCII architecture diagram; a table of the main config settings; the flags vocabulary; the `details` fields; limits; troubleshooting. No links into `affective_project_notes/`.
- Make `details` compact and readable in the log (check how `harness/logger.py` prints it).
- Add `affective_project_notes/tools/clean_copy_check.py` (copies `affective_project/` alone to a temp folder and runs the tests and all scenarios there).

**Phase 7 — Voice channel** (only after Phase 6's gate passes)

- As in MASTER_PROMPT Phase 7: framing, windowing, FFT, energy, ZCR, autocorrelation pitch and MFCC implemented in numpy, with docstrings explaining each concept.
- numpy import-guarded: if numpy is missing, flag `audio_unavailable` and return the text-only result.
- Follow `assets/audio/README.txt`: `speaker_low.wav` and `speaker_high.wav` are both calm, so normalise pitch per speaker or use pitch variability, not absolute pitch. The noisy files must get lower voice confidence than the clean ones (estimate SNR). `agitated_*` must get higher activity than `calm_*`.
- Late fusion with the text estimate (weights and confidences in config); text dominates valence, voice contributes mostly to activity.
- Regression test: with `audio_path=None` the output is identical to text-only. Missing or corrupt audio → flag and no crash.
- Document the limits (speaker, noise, microphone, language, synthetic test files) in `topic2.md`.

**Phase 8 — Face channel:** skip.

**Phase 9 — Evaluation**

- Build `engine/evaluation/evaluate.py` and unit-test every metric (Pearson, Spearman, MAE, RMSE, accuracy, macro-F1, confusion matrix, Krippendorff's alpha or ICC, Fleiss' kappa, bootstrap CI with fixed seed) on hand-computed fixtures inside `tests/` only.
- Compare the starter baseline (`affective_project_notes/evaluation/baselines/starter_engine/engine.py`, loaded by file path), the full engine and ablations (no negation, no sarcasm, no state, text-only vs text+voice).
- Results go to `engine/evaluation/results/`; dev and test reported separately; agreement statistics only with 2+ raters.
- There are no real ratings yet: build and test the pipeline, then continue (hard stop H1 applies only as a note in the final report, not a pause).

**Phase 10 — Ethics and limits:** `affective_project_notes/ethics/ethics.md` as in MASTER_PROMPT Phase 10 (data inventory, GDPR, EU AI Act, bias, what the system cannot do, design commitments). Mark every legal article and date to re-check with `[[CHECK]]`. Also finish the consent form's two `[[TODO]]`s with proposed wording marked `[[CONFIRM]]`.

**Phase 11 — Report draft:** `affective_project_notes/report/report_draft.md` following the brief (solo version): Introduction and scenario; one section per topic (1–5); Evaluation; Ethics and limits; Difficulties and issues (from `DIFFICULTIES.md`, including today's line-ending, encoding, fragment and language-detection problems); Use of AI (from `AI_LOG.md`, mentioning that a second AI reviewed the work and found specific bugs). Add a page budget for 7–12 pages of body text. Every number comes from `engine/evaluation/results/` or is marked `[[TODO]]`; every personal statement is marked `[[WRITE IN MY OWN WORDS]]`. Also create `report/contribution_statement.md` as a short solo statement marked `[[CONFIRM]]`.

**Phase 12 — Video script:** `affective_project_notes/video/script.md` and `captions.srt` for 5:00 max: 0:00–0:30 terminal and `python run_app.py`; 0:30–4:15 M1, M2, M3, M4 in order, with what to point at (map point, confidence, label, action) and narration explaining which rule fired; 4:15–5:00 expand the session log, open the exported `.txt`, show voice with one audio file. Because my ratings are not done, use placeholders such as `[[value from log]]` instead of real per-message numbers. Include a recording checklist and the ffmpeg compression command (`-preset veryfast -crf 28`, 720p).

**Phase 13 — Presentation and Q&A:** `affective_project_notes/presentation/outline.md` (15 minutes, one speaker, time per part); `affective_project_notes/qa/topic1.md` … `topic5.md` and `whole_system.md`, each with 12 likely teacher questions, answers tied to our files and settings, a follow-up per question, and 3 live-change drills (exact file and setting, command to run, expected effect).

**Phase 14 — Packaging and final check**

- `affective_project_notes/tools/package.py` builds `GroupXX_AffectiveComputing.zip` containing `report.pdf`, `video_demo.mp4` and `code/`, where `code/` is a copy of `affective_project/` without `__pycache__`, without session logs except the demo log given as an argument, and with or without `engine/evaluation/ratings/` depending on a flag.
- It refuses to build if the report or video is missing, runs `verify_kit.py` and the clean-copy check on `code/`, and prints a manifest with sizes.
- Do not run it for real (the report and video do not exist yet); test it with dummy files in a temporary folder only.
- Write `affective_project_notes/FINAL_CHECKLIST.md` mapped to the Evaluation Guide (✅/❌ and what is missing).

---

## 5. Verification gate (after Part A and after EVERY phase; all must pass)

1. From `affective_project/`: `py -3.12 -m unittest discover tests`, all pass. Also with `py -3.9` if installed (say once in the final report if it is not).
2. Every scenario through `py -3.12 run_scenario.py <file>`: no `PROBLEMS` or `ERROR` lines in the logs. Then delete the session logs you generated (keep `logs/README.txt`).
3. `affective_project_notes/tools/verify_kit.py` reports zero mismatches against the original zip, and `git status` shows no change to any protected file and no new top-level file in `affective_project/`.
4. Zip simulation: run `clean_copy_check.py` (or, before Phase 6, copy `affective_project/` alone to a temp folder and run the tests and scenarios there).
5. Encoding check: every text file you created or changed is valid UTF-8, with no `?` inside words and no U+FFFD.
6. Generalisation check: at least 15 new sentences relevant to the phase (EN and PT; not in `messages.csv`, not already in tests); report the pass rate; add the useful ones as regression tests.
7. Update the study notes (Section 7), `AI_LOG.md`, `DIFFICULTIES.md` and `affective_project_notes/STATUS.md`.
8. Commit locally: `Phase N: <summary>`.

If a check fails, fix it. If it still fails after two attempts, record it in `DIFFICULTIES.md`, mark the phase incomplete in `STATUS.md`, and continue only if later phases do not depend on it.

---

## 6. Hard stops (the only reasons to stop and ask me)

- **H1:** Real ratings are needed to produce numbers. Do not stop: finish the pipeline, use placeholders, and list it in the final report.
- **H2:** A change would require editing a protected kit file or reading the notes folder at runtime.
- **H3:** A change to the six-action semantics beyond Section 3, or to tier values or assignments.
- **H4:** A gate check still fails after two fix attempts and later phases depend on it, or you believe a test itself is wrong.

Anything else: make the most reasonable choice, record it in `OPEN_QUESTIONS.md` under "Decided by the AI, to confirm", and continue.

---

## 7. Study notes (every phase)

Update `affective_project_notes/topics/topic<N>.md` with **How it works** (concept → our design → files and functions → a worked example with real numbers from one of your new sentences) and **How to change it** (3–5 likely changes: exact file, setting, expected effect), plus 5 likely teacher questions with short answers tied to our code.

---

## 8. Final report (your last message)

Update `affective_project_notes/STATUS.md` and reply with:

1. A table of Part A (A1–A5) and Phases 5–14: done / incomplete / skipped, one line each, with the commit hash.
2. Final gate results (test count, Python versions, scenario results, `verify_kit.py` result, clean-copy check).
3. Hidden-test rehearsal pass rate and the generalisation pass rate per phase.
4. Words added to the lexicon (with tiers) and every entry under "Decided by the AI, to confirm".
5. A checklist of everything only I can do: tier review, my ratings and the volunteers' ratings, the teacher's answers, the AI-log fields, rewriting the report in my own words and exporting `report.pdf`, recording and compressing the video, choosing the demo log, running `package.py`, pushing to GitHub, and delivering.