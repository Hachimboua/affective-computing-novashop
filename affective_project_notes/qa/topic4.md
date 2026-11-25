# Topic 4 — Software, interface, tests and demo: likely questions

1. **How is the system run?**
   `python run_app.py` (interface), `python run_scenario.py scenarios/mandatory/M1_calm_faq.json` (no interface), `python -m unittest discover tests` (tests). Instructions are in `engine/README.md`.

2. **What is the engine contract?**
   `Engine.reset()` starts a conversation; `Engine.process(text, audio_path=None, image_path=None)` returns a dict with valence and activity in [-1, 1], confidence in [0, 1], label, one of six actions, reply, plus dominance, flags and details. Checked by the kit's `tests/test_contract.py` and `harness/contract.py`.

3. **How do you guarantee the engine never crashes?**
   `Engine.process` wraps the pipeline in try/except and returns a valid fallback with `internal_error`; in tests `ENGINE_STRICT=1` re-raises so bugs stay visible.

4. **How did you make sure you did not change the kit?**
   `tests/test_kit_unchanged.py` hashes the raw bytes of `harness/`, `run_app.py`, `run_scenario.py`, `scenarios/` and the contract test; `affective_project_notes/tools/verify_kit.py` compares every protected file with the original zip.
   *Follow-up: what went wrong once?* Git converted line endings and a checksum test was weakened to hide it; we restored the files byte for byte and reverted the test.

5. **How many tests, and what do they cover?**
   131 tests in 15 files: perception, labels, state, policy, replies, robustness, rehearsal, scenarios, integration, voice, metrics, evaluation, rating tool, contract and kit integrity.

6. **Which Python versions?**
   Python 3.9 or later; tested on 3.9 without numpy (voice tests skip) and 3.12/3.13 with numpy. No 3.10+ syntax.

7. **What does the log contain?**
   The kit harness writes input, map values, confidence, label, action, flags, latency, reply and our `details` (language, intent, evidence, sarcasm score, text/voice/fused estimates, second label, state, rule, reason, timings).

8. **Why is `details` kept short?**
   The harness prints it on one line; we cap evidence (`DETAILS_EVIDENCE_LIMIT`) and round numbers; a test keeps the line under 650 characters.

9. **How is the project reproducible?**
   Deterministic engine (no randomness), fixed bootstrap seed in evaluation, a clean-copy check that runs the tests and scenarios from a copy of `affective_project/` alone.

10. **What are the dependencies?**
    Standard library only for the mandatory engine; numpy optional (voice). `requirements.txt` is the kit's, unchanged, because the brief allows numpy without listing it.

11. **How is the code organised?**
    `engine/perception`, `engine/affect`, `engine/voice`, `engine/state`, `engine/policy`, `engine/evaluation`, `engine/tools`; all thresholds in `engine/config.py` with a comment on each trade-off.

12. **What does the video show?**
    Running the app, M1–M4 in order with the rule that fired, the session log and the exported `.txt`, and a voice example.

## Live-change drills (verified)

1. **Run one test.** `python -m unittest tests.test_replies -v`.
2. **A test that protects the log.** Set `DETAILS_EVIDENCE_LIMIT = 4` in `config.py` and run `python -m unittest tests.test_integration`: it fails, because a long message now makes the one-line DETAILS entry longer than 650 characters. That shows the test guarding log readability. Set it back to 2 and the test passes again.
3. **Check the kit is intact.** `python affective_project_notes/tools/verify_kit.py <path to the kit zip>`: expect zero mismatches.
