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
