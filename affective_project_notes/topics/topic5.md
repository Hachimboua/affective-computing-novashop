# Topic 5: Evaluation and data (Phase 1)

## How it works

Human evaluation compares the system's estimates with independent judgments
instead of treating the developer's intuition as ground truth. The dataset
keeps full conversations together across dev and test so a conversation cannot
leak between tuning and final evaluation. The rating workflow uses three
Self-Assessment Manikin (SAM) dimensions and also gathers a label and a
support-action judgment. Raters see only message text and earlier turns, not
engine predictions.

The current dataset is
`../../affective_project/engine/evaluation/data/messages.csv`. It has 88 messages:
28 original scenario messages (all in dev) and 60 new AI-drafted messages,
explicitly marked `source=ai_draft`. The ten AI-drafted dev conversations add
30 messages to the eight scenario conversations; ten separate test
conversations add the remaining 30 messages. Thus the split has 18 dev
conversations and 10 test conversations, with no conversation crossing splits.
The messages cover English, Portuguese, unsupported scripts, support intents,
negation, intensifiers, sarcasm, mixed emotion, short/ambiguous text, typos,
slang, emoji, caps, explicit human requests, legal language, and closings.

`../../affective_project/engine/evaluation/rate.py` loads the dataset, displays
the current message and its earlier conversation turns, validates 1-9 SAM
ratings, presents fixed label/action choices, and appends each response to
`../../affective_project/engine/evaluation/ratings/<rater-id>.csv`. It resumes by skipping message IDs
already in that file. The spreadsheet template contains the message rows with
blank ratings. `../../affective_project/tests/test_rating.py` checks scale and
ID validation, conversation split isolation, and resuming with prior-turn
context.

Worked example from the real dataset: conversation `AI-D04` is entirely in
dev and contains three negation/intensifier messages; its turn 1 is "The
battery is not bad, but it drains faster than I expected." This is an example
of a mixed clause that raters should judge in context, not a result from the
engine. No engine estimate is available yet, so an engine-vs-human numerical
example is intentionally left as `[[TODO: add a real engine output after the
text engine is implemented]]`.

The instructions cite Bradley and Lang (1994) for SAM. Before the first rating
session, the student must review/edit AI-drafted messages and confirm the
consent/storage details and the meanings of the two human-handling actions
with the teacher. No ratings have been fabricated or entered. Until the
student confirms their own ratings are complete, do not display engine
valence, activity, or labels for any of the 88 evaluation messages; at the
Phase 2 checkpoint, report scenario pass/fail only and use unit-test sentences
as worked examples. Do not tune on these messages before that confirmation.

## How to change it

1. To add a message, edit
   `../../affective_project/engine/evaluation/data/messages.csv` with a unique
   `msg_id`, its conversation ID, a consecutive turn number, one split, the
   text, source, and case type. Put every turn of a conversation in the same
   split. AI-generated entries must use `source=ai_draft`.
2. To change the rater's fixed labels or actions, edit `LABELS` or `ACTIONS` in
   `../../affective_project/engine/evaluation/rate.py`, but coordinate any label-set change with the
   engine and report. The choice lists are visible to raters, so changing them
   affects comparability.
3. To change the scale validation or rater-ID rule, edit
   `parse_scale_value()` or `sanitize_rater_id()` in the same file. Keep SAM
   responses integer-valued from 1 through 9 and IDs safe as filenames.
4. To change what a rater sees, update `rate_messages()` and
   `../ethics/rating_instructions.md` together. The
   workflow must continue to show prior conversation turns and must never
   display engine predictions.
5. To revise spreadsheet entry, regenerate
   `../../affective_project/engine/evaluation/sam_ratings_template.csv` from the dataset; leave rating
   values blank and do not insert sample or fabricated ratings.

## Likely teacher questions

1. **Why split by conversation?** A conversation's turns are related; splitting
   turns separately could let similar context appear in both tuning and test.
   The test checks each conversation has a single split.
2. **Why keep AI-drafted messages separate in `source`?** The student must
   review them, and reports should identify their provenance rather than
   implying they came from real customers.
3. **What does SAM measure?** Three 9-point dimensions: valence/pleasure,
   arousal/activity, and dominance/control. The ratings describe expressed
   emotion in text, not the rater's own feeling.
4. **How does the rating CLI avoid bias?** `rate.py` imports no engine module
   and displays only message text, previous turns, rating choices, and
   progress; it never loads predictions.
5. **How can the rater resume?** `load_completed_ids()` reads already-rated
   `msg_id`s, and `rate_messages()` skips those entries while retaining the
   earlier conversation messages as context.

## Live-change drills

1. Add a new three-turn test conversation to
   `../../affective_project/engine/evaluation/data/messages.csv` with one `conversation_id`, turns
   1-3, and `split=test`; run `python -m unittest discover tests -v`. The
   conversation/split test should still pass, and the total should rise by
   exactly three messages.
2. Copy `../../affective_project/engine/evaluation/sam_ratings_template.csv` to a separate file and
   fill the first row with a valid integer valence 1-9, arousal 1-9,
   dominance 1-9, a listed label, and a listed action. Compare it with the
   CLI output schema in `rate.py`; all choices should match and the untouched
   template should remain blank.

## Phase 9 — the evaluation pipeline

### How it works

- **Concept.** Compare what the engine estimates with what people perceive. Humans rate each message on the Self-Assessment Manikin (9-point valence, arousal, dominance) plus a label and the action they would choose. Their agreement with each other is the ceiling for the engine.
- **Our design.** `engine/evaluation/evaluate.py` loads every rater file in `engine/evaluation/ratings/`, converts ratings with (r − 5)/4, averages raters per message, takes majority votes for label and action, then replays each conversation of the chosen split (dev or test) in order with a fresh engine. It does this for five variants: the kit's starter engine (`engine/evaluation/baselines/starter_engine.py`), the full engine, and three ablations (no negation, no sarcasm detection, no state smoothing), and compares them.
- **Metrics** (`engine/evaluation/metrics.py`, plain Python): Pearson, Spearman, MAE, RMSE, sign accuracy, accuracy, macro-F1, confusion matrices, Krippendorff's alpha (interval), Fleiss' kappa, mean pairwise Pearson, percentile bootstrap intervals (seed 13), calibration bins. Each is tested on a hand-computed or published example in `tests/test_metrics.py` (Krippendorff 0.849, Fleiss 0.210).
- **Outputs.** `engine/evaluation/results/<split>_summary.md`, `_metrics.json`, `_predictions.csv`, `_errors.csv` (15 largest errors with a suggested category and an empty `my_category` column).
- **Honesty guard.** Without rating files the script stops with exit code 2 and writes nothing. The end-to-end test uses invented fixture ratings in a temporary folder only.
- **Voice check.** `python -m engine.evaluation.evaluate --voice-check` checks the voice channel on the six kit audio files (no ratings needed): voice activity −0.24 for calm vs +0.25 for agitated, both calm speakers stay calm, noisy files get confidence 0.05.

### How to change it

1. Switch the split: `--split test` (only after tuning is finished on dev).
2. Make missed escalations cost more: `MISSED_ESCALATION_COST` in `evaluate.py`.
3. Add an ablation: one tuple in `VARIANTS` with the config values to override (restore is automatic in `patched_config`).
4. More or fewer bootstrap samples: `--bootstrap 2000` (narrower Monte-Carlo noise, slower).
5. Change the calibration bins: `edges` in `metrics.calibration_bins`.

### Likely teacher questions

- *Why majority vote and what about ties?* A label is only "gold" if most raters agree; ties are excluded from label/action metrics and counted (`ties_excluded`).
- *Why compare with the starter engine?* It is the common starting point for every group; the difference is what our work added.
- *Why replay whole conversations?* The state depends on earlier turns; scoring messages in isolation would test a different system.
- *What does a wide bootstrap interval mean?* Few messages: the true value could be far from the estimate, so claims must be modest.
- *Why plain Python instead of numpy for metrics?* The evaluation then runs on the teacher's machine even without numpy.
