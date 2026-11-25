# Instructions for human raters

## Before you begin

Read `consent_form.md`. Use an anonymous rater ID, for example `R01`.

- **With the rating tool** (Python installed): open a terminal in the
  `affective_project` folder and run `py -3.12 -m engine.evaluation.rate --rater R01`
  (on Mac/Linux: `python3 -m engine.evaluation.rate --rater R01`). The tool can
  resume: it skips messages already saved in that rater's CSV.
- **With a spreadsheet** (no Python needed): fill a copy of
  `sam_ratings_template.csv`, going down the rows in order (each conversation is
  in turn order, so earlier rows are the context), and send it back named
  `R01.csv`.
Rate independently; do not discuss messages or ratings with other raters until
everyone has finished. The tool does not show engine estimates or predictions.

## What to rate

Rate the emotion the customer **expresses in the message**, using earlier turns
only as context. Do not rate what you personally would feel in the situation.
Use the whole message, including punctuation, emojis, and the conversation
history, but do not assume facts that are not stated.

The Self-Assessment Manikin (SAM) uses three 9-point dimensions:

- **Valence / pleasure:** 1 = very unpleasant or negative; 9 = very pleasant or
  positive.
- **Arousal / activity:** 1 = very calm or low-energy; 9 = very activated,
  excited, or agitated.
- **Dominance / control:** 1 = very powerless or lacking control; 9 = very
  much in control.

Choose the best-fitting label from exactly these seven: `neutral`, `calm`,
`joy`, `anger`, `frustration`, `fear`, `sadness`.
Then choose the support action you think is appropriate:
`ANSWER`, `ANSWER_EMPATHIC`, `ASK_CLARIFICATION`, `OFFER_HUMAN`, `ESCALATE`,
or `CLOSE_POSITIVE`.

The kit does not define the exact distinction between `OFFER_HUMAN` and
`ESCALATE`. The provisional interpretation is that `OFFER_HUMAN` offers a
human handoff, while `ESCALATE` routes an urgent or high-risk issue for
higher-priority handling. Confirm this distinction with the teacher before
collecting action ratings; do not treat this provisional text as an official
course definition.

Use the middle of a scale when the expression is mixed or neither strongly
positive nor negative. A clear neutral information request can have a moderate
rating; low valence/arousal is not the same as uncertainty. If a message is
ambiguous, rate the expression as written and add a short optional comment if
that helps explain your choice.

## Time and comments

There are 88 messages in short conversations. Allow about 20-30 minutes and
take breaks if needed. Comments are optional; keep them brief and do not enter
personal information, names, email addresses, or real order/account numbers.
