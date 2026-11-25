# Text perception engine

The engine keeps the kit's `engine.engine.Engine` interface and currently
estimates text only. It supports English and Portuguese using bundled,
hand-assigned VAD entries plus transparent rules for negation, emphasis,
punctuation, domain cues, sarcasm, and simple support intents. These estimates
are starting points, not human-validated ratings. Audio and image inputs are
not analyzed in this phase; policy still returns the temporary `ANSWER`
action.
The coarse emotion labels use the kit vocabulary: `neutral`, `calm`, `joy`,
`anger`, `frustration`, `fear`, and `sadness`.

## Checks

From the `affective_project/` directory, run:

```text
python -m unittest discover tests -v
python tests/test_contract.py
```

The scenario runner prints valence, activity, confidence, and labels for each
scenario message. Wait until your own SAM ratings are complete before running
it on any of the evaluation messages.

## Tuning

Shared thresholds and weights are in `config.py`. Do not tune against the
evaluation messages; use unit-test sentences while implementing and reserve
the held-out conversations for final evaluation after the rating work is
complete. Lexicon entries and their provenance are documented in the
project's sibling [`SOURCES.md`](../../affective_project_notes/SOURCES.md).
