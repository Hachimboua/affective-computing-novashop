# Topic 4: Software, interface, tests, and demo (Phase 0)

## How it works

The software topic is about interface contracts and integration: the engine
must plug into a shared harness without changing the harness, and its behavior
must be reproducible through the same entry point used by both the GUI and
scenario runner.

The current kit imports `Engine` from `engine/engine.py`. In
`harness/loader.py`, `load_engine(project_dir)` imports `engine.engine` and
constructs `Engine()`. `harness/session.py` calls `reset()` at a new
conversation, sends each message to `process(text, audio_path, image_path)`,
normalizes the returned dictionary, measures latency, and records the result.
`harness/gui.py` displays the 2D map and enables its 3D view when dominance is
present. `harness/logger.py` writes the output and `details` to a plain-text
session log. The scenario runner uses the same session and scenario loader, so
testing through it exercises the integration path.

The original starter is deliberately minimal. It recognizes a few individual
words, sums their polarity, adds activity for `!`, and always returns the same
action and reply. The Phase 0 architecture proposal keeps `Engine.reset()` and
`Engine.process()` as the public interface while moving perception, affect,
state, policy, voice, and evaluation into explainable modules under `engine/`.
The kit root README and harness remain unchanged.

Worked baseline example: running mandatory M1 turn 3, "Perfect, that is all I
needed. Thank you!", produced valence `+1.00`, activity `+0.30`, confidence
`0.30`, label `joy`, action `ANSWER`. The starter sums the positive entries
for `perfect` and `thank`, clips the sum at +1, and sets activity to 0.3
because the input contains `!`. The intended positive conversation close is
`CLOSE_POSITIVE`, so this example shows that valid numeric output alone is not
enough; action and reply behavior also need integration tests.

## How to change it

These are likely changes after the proposed architecture is approved:

1. To change processing order or preserve the public API, edit
   `engine/engine.py`, especially `Engine.reset()` and `Engine.process()`.
   Keep the input parameters and contract keys stable so both the GUI and
   runner continue to work.
2. To add or modify a contract regression, add a new file under `tests/`.
   Keep `tests/test_contract.py` unchanged. The new
   `tests/test_kit_unchanged.py` checks hashes of the protected harness,
   scenario, and runner files.
3. To change engine behavior thresholds, use the future
   `engine/config.py` rather than scattering constants in the pipeline. A
   higher escalation threshold should reduce false escalations but risks
   missing severe cases.
4. To change the scenario path used for integration checks, run the existing
   `run_scenario.py` with a different JSON file; do not edit the runner. Its
   output shows each turn's valence, activity, confidence, label, and action.
5. To change student setup instructions, add or revise
   `engine/README.md`. Leave the kit-root `README.md` unchanged pending the
   teacher's answer to the open question.

## Likely teacher questions

1. **How does the harness find the engine?** `harness/loader.py` imports
   `engine.engine` and constructs `Engine`; the module/class path is part of
   the integration contract.
2. **Why keep the harness unchanged?** It is the shared evaluation interface;
   changing it could hide contract failures and would invalidate comparison
   with teacher tests.
3. **What does the contract check?** `harness/contract.py` requires numeric
   valence/activity/confidence, a label, one of six actions, and a reply; it
   also checks value ranges and accepts optional dominance, flags, and details.
4. **What is one concrete starter-engine failure?** In M1 turn 3, the engine
   gives a positive estimate but returns `ANSWER` instead of the expected
   positive close; the baseline is recorded in
   `../evaluation/baseline_logs/M1_calm_faq.txt`.
5. **How are `OFFER_HUMAN` and `ESCALATE` different?** The kit gives both
   names but does not define the difference. The proposed distinction is a
   human handoff offer versus urgent higher-priority routing; confirm this with
   the teacher before encoding it in policy.

## Live-change drills

These are future drills; the referenced modules/settings are proposed and
should be created only after architecture approval.

1. In `engine/config.py`, lower `HUMAN_STREAK` from 3 to 2. Run
   `python run_scenario.py scenarios/mandatory/M2_growing_frustration.json`.
   The policy should offer a human earlier in the repeated negative
   conversation; verify the action and rule name in the log.
2. Add `delighted` to `engine/perception/lexicons/en.tsv` with a positive VAD
   entry, then run `python -m unittest discover tests -v`. A focused perception
   relation should show that the valence for `delighted` is positive; do not
   add any scenario-specific message lookup.
