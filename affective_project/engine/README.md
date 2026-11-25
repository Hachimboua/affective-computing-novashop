# NovaShop affective support engine

**Author:** `[[ADD STUDENT NAME / GROUP]]`

**Topics:** bilingual text perception; V/A/D affect labels; conversation state,
ordered support policy and replies; integration, logging and robustness.

The engine is a transparent, rule-and-lexicon prototype for English and
Portuguese customer-support messages. Its affect estimates and lexicon tiers
are provisional; they are not validated against human ratings. It is not a
production customer-service system.

## Requirements and installation

- Python 3.9 or newer.
- Text-only operation uses the Python standard library.
- Tkinter is needed for the desktop interface. Some Linux installations
  package it separately as `python3-tk`.
- NumPy is optional and needed only by the voice channel after Phase 7. The
  engine continues in text-only mode without it.
- The target teacher computer is offline. Install any needed packages before
  moving the project there.

Text-only operation requires no package installation. Before enabling voice,
install NumPy while online, then transfer the prepared environment or wheel to
the offline teacher computer:

```text
python -m venv .venv
python -m pip install "numpy>=1.23"
```

The unchanged `requirements.txt` documents that the core uses only the
standard library and that NumPy is allowed as an optional dependency. On
Windows, `py -3.12` can replace `python` in the commands below when that
launcher version is installed.

## Run the application and checks

Run the interface from the project root:

```text
python run_app.py
```

Run one mandatory or practice scenario:

```text
python run_scenario.py scenarios/mandatory/M1_calm_faq.json
```

The scenario runner prints each turn and writes a session log under `logs/`.
Use only the supplied scenario files for this command. Do not pass evaluation
messages to the scenario runner.

Run the full unit suite and the public contract check:

```text
python -m unittest discover tests -v
python tests/test_contract.py
```

From the workspace root, the isolated clean-copy gate is:

```text
py -3.12 affective_project_notes/tools/clean_copy_check.py
```

It copies only `affective_project/` to a temporary directory, then runs the
contract test, full suite, and every scenario in that copy. Use the oldest
Python available; in the current environment that is Python 3.12. Generated
scenario output is captured and only pass/fail totals are printed.

## Ratings and evaluation

The interactive human-rating tool is separate from the engine and does not
run predictions:

```text
python -m engine.evaluation.rate --rater <anonymous-rater-id>
```

Use it only with informed, consenting raters. It writes their SAM judgments
under `engine/evaluation/ratings/` (one CSV per anonymous rater).

Compare the engine with the ratings (tune on `dev` only; `test` gives the
honest numbers):

```text
python -m engine.evaluation.evaluate --split dev
python -m engine.evaluation.evaluate --split test
```

For each split this replays every conversation in order with a fresh engine
and compares five variants: the kit's starter engine (baseline, copied in
`engine/evaluation/baselines/`), the full engine, and three ablations
(no negation, no sarcasm detection, no state smoothing). It reports Pearson
and Spearman correlation, MAE and RMSE for valence, activity and dominance
(with 95% bootstrap intervals), label and action accuracy and macro-F1,
confusion matrices, a cost-weighted action error (a missed escalation costs
the most), confidence calibration, latency, and agreement between raters
(Krippendorff's alpha, mean pairwise Pearson, Fleiss' kappa; two or more
raters needed). Results go to `engine/evaluation/results/`:
`<split>_summary.md`, `<split>_metrics.json`, `<split>_predictions.csv` and
`<split>_errors.csv` (the 15 largest errors, with an empty `my_category`
column for the error analysis). Without rating files the command stops with
exit code 2 and writes nothing. It never invents ratings.

The metric formulas live in `engine/evaluation/metrics.py` (plain Python, no
numpy) and are checked against hand-computed examples in
`tests/test_metrics.py`.

Check the voice channel against the expectations in
`assets/audio/README.txt` (needs numpy; no ratings needed):

```text
python -m engine.evaluation.evaluate --voice-check
```

## Lexicon tier synchronization

After reviewing the tier sheet, run the required-argument synchronizer from
the project root:

```text
python -m engine.tools.sync_lexicon_tiers <path-to-sheet>
```

The runtime reads the TSV lexicons; it does not load the review sheet.

## Architecture

```text
run_app.py / run_scenario.py
          |
          v
   harness.Session ----> harness.contract.normalize
          |                         ^
          v                         |
    Engine.process -----------------+
          |                         |
          +--> preprocess + language + intent
          |        |                |
          |        +--> lexicons + rules + sarcasm
          |        |                |
          |        |                v
          |        |          text V/A/D
          |        |                |
          |        +--> optional WAV features + voice estimate
          |                         |
          |                    late fusion
          |                         |
          +--> StateTracker --> ordered R0-R7 policy --> bilingual reply
          |                         |
          +--> compact details + flags + stage timings
                                    |
                                    v
                         session history and text log
```

Voice processing is optional, uses NumPy when available, and accepts mono or
stereo 16-bit PCM WAV files. Text remains dominant for valence; voice has more
influence on activity. The voice-only valence cue is deliberately weak, and
modality disagreement lowers confidence and can flag `modality_conflict`.
Without NumPy, or for a missing/corrupt/unsupported WAV, the engine keeps the
text estimate and adds `audio_unavailable`. Silence is marked `no_speech`.
`audio_path=None` is the text-only path. Face processing is skipped.

## Main configuration

Shared settings live in `engine/config.py`. Changing a threshold changes
behavior, so rerun the focused tests and scenarios after a change.

| Setting | Default | Effect of increasing it |
|---|---:|---|
| `TEXT_LATENCY_BUDGET_SECONDS` | 0.10 | Allows more processing time in the latency regression. |
| `DETAILS_EVIDENCE_LIMIT` | 2 | Includes more matched terms in each log detail record. |
| `VOICE_ENABLED` | `True` | Disables voice processing when set to `False`. |
| `VOICE_FRAME_MS` | 25 | Sets short-time analysis frame length. |
| `VOICE_HOP_MS` | 10 | Sets the step between overlapping frames. |
| `TEXT_ACTIVITY_WEIGHT` / `VOICE_ACTIVITY_WEIGHT` | 0.40 / 0.60 | Shifts fused activity toward text or voice. |
| `TEXT_VALENCE_WEIGHT` / `VOICE_VALENCE_WEIGHT` | 0.90 / 0.10 | Keeps fused valence primarily text-based. |
| `STATE_ALPHA` | 0.50 | Reacts faster to new affect, but follows message noise more. |
| `NEG_TURN_V` | -0.25 | Counts milder negative turns toward persistence signals. |
| `TREND_WORSENING_THRESHOLD` | -0.08 | Requires a steeper decline before marking a worsening trend. |
| `ESC_V` | -0.65 | Requires a more negative state for escalation. |
| `ESC_A` | 0.55 | Requires more activity for escalation. |
| `ESC_TURNS` | 2 | Requires more consecutive severe turns. |
| `MAX_CLARIFY` | 2 | Allows a longer clarification loop before offering a person. |
| `EMPATHY_EXIT_V` | -0.15 | Exits the empathic state at a less positive recovery value. |
| `LABEL_D_WEIGHT` | 0.50 | Gives dominance more influence in prototype distance. |
| `LABEL_NEUTRAL_RADIUS` | 0.18 | Assigns `neutral` to a larger area around the origin. |
| `LANG_LEXICON_EVIDENCE_FLOOR` | 0.65 | Trusts a supported-language lexicon match more. |

## Output, details and flags

The public result contains `valence`, `activity`, `dominance`, `confidence`,
`label`, `action`, `reply`, `flags`, and JSON-serializable `details`.
`details` is deliberately compact because the harness logger prints it on one
line:

- `lang`, `lang_confidence`, and `intent` identify the supported-language and
  intent estimate.
- `evidence` contains up to `DETAILS_EVIDENCE_LIMIT` entries in the form
  `[term, V, A, D]`; `evidence_count` is the total number of matches.
- `sarcasm` is the heuristic score. `text` contains rounded V/A/D/confidence;
  when audio is used, `voice` and `fused` contain the modality and combined
  estimates.
- `second_label`, `label_distance`, and `second_distance` explain the
  nearest-prototype decision.
- `state` contains the smoothed `valence` and `activity`, `trend`,
  `neg_streak`, and `clar_streak`.
- `rule` and `reason` identify the first matching policy rule.
- `timing_ms` reports `text`, `state`, `policy_reply`, and whole-engine
  `total` time in milliseconds. When an audio path is supplied, it also
  reports `voice` and `fusion`. These are measurements, not fixed limits.
- `engine_version` identifies this output schema. Internal-error fallback
  details contain the error type but never expose the exception message.

The current fixed flag vocabulary is:

`abuse`, `audio_unavailable`, `audio_used`, `caps`, `contrast`, `downtoner`,
`elongation`, `empty`,
`escalation_cue`, `exclamation`, `hesitation`, `human_declined`,
`human_request`, `intensifier`, `internal_error`, `low_confidence`,
`mixed_emotion`, `mixed_language`, `modality_conflict`, `negative_event`,
`no_affect_words`, `no_speech`, `possible_sarcasm`, `profanity`, `question`,
`repeated_issue`, `safety`,
`short_message`, `trend_worsening`, `unsupported_language`, `emoji`.

## Limits and channel switches

Voice is a lightweight optional channel, not a transcription system or a
validated emotion recognizer. It cannot identify speakers or infer their true
feelings; fixture-derived references and signal-quality measures are only
approximate. The engine does not load face inputs or infer facial affect.

The English/Portuguese lexicons, sarcasm rules, intent cues, and policy
thresholds are transparent but heuristic. Unsupported-language detection is
limited, replies do not access live order systems, and the engine cannot
confirm refunds, delivery status, or account actions. It does not infer a
person's true feelings or replace human support. There are no human SAM
ratings yet, so the estimates are not calibrated.

## Troubleshooting

- **`ModuleNotFoundError: engine`** — run commands from the `affective_project/`
  root, not from the `engine/` subdirectory.
- **The desktop window does not start** — confirm Tkinter is installed; on
  Linux, install the distribution's `python3-tk` package.
- **A scenario creates a log** — logs are written to `logs/`; keep
  `logs/README.txt` and remove only generated session logs after verification.
- **A test hides an internal exception behind a fallback** — set
  `ENGINE_STRICT=1` in the test process to re-raise the original exception.
- **The lexicon sync command rejects its arguments** — provide the review
  sheet path as the required positional argument and verify its tier columns.
- **The offline computer lacks a dependency** — install Python packages
  beforehand; text-only execution itself needs no third-party package.
