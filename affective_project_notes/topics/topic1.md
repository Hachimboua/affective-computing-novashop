# Topic 1: Text perception (Phase 2)

## What the text engine does

The Phase 2 text pipeline is a standard-library implementation under
`affective_project/engine/perception/`. It normalizes and tokenizes text,
retains capitalization and elongation cues, separates clauses, detects
English/Portuguese and unsupported scripts, and matches single-word, phrase,
emoji, and emoticon entries. Rule modules apply short-scope negation,
intensifiers, downtoners, punctuation, support-domain cues, and transparent
sarcasm heuristics. Sarcasm checks negative-event word forms and repetition
cues as well as idioms in both supported languages. Language detection uses
distinctive stopwords and English/Portuguese word- and phrase-lexicon hits;
unsupported status requires no supported evidence or winning unsupported-
language stopword evidence. The estimator returns valence, activity,
dominance, confidence, a coarse prototype label, language, a simple
intent/entities result, flags, and evidence.
The label vocabulary is `neutral`, `calm`, `joy`, `anger`, `frustration`,
`fear`, and `sadness`.

The `Engine` adapter preserves the kit interface and adds only the text
estimate to its per-conversation history. Audio and images are not analyzed.
The action and reply are still temporary placeholders for later policy work;
do not treat Phase 2 as a complete customer-support assistant.

## Worked examples and limits

Use only unit-test sentences for demonstrations:

1. `not good` has a lower valence estimate than `good`, while negation does not
   simply copy the opposite word's full strength.
2. `The setup was easy but the router is terrible.` sets mixed-emotion and
   contrast flags; the clause after `but` receives the larger configured
   weight.
3. `O meu dispositivo está avariado e fiquei dececionada.` is identified as
   Portuguese and produces negative valence.
4. `I love that for me.` is flagged as possible sarcasm and is estimated
   negatively.
5. The fresh Phase 5 sentence “The charging port on my camera is damaged,
   and I am really disappointed.” produced V=-0.764, A=-0.136, D=-0.246,
   confidence=0.661, label `sadness`, intent `DAMAGED_OR_DEFECTIVE`, and action
   `ANSWER_EMPATHIC` under `R6_EMPATHY`.

These are qualitative illustrations from focused unit tests, not evaluation
set results. Runtime VAD values come from the supplied tier table. Per-term
tiers are AI-assisted meaning-based suggestions and remain unreviewed; the
legacy VAD columns in the review sheet are not used at runtime. See
`../SOURCES.md`. Confidence is a heuristic evidence score, not a calibrated
probability. Sarcasm, language identification, and domain rules can fail on
out-of-vocabulary or mixed-context text. Terse or domain-heavy English with no
recognized stopwords or lexicon entries may still be flagged as unsupported.

### Phase 5 robustness and performance

`tests/probes.py` supplies short, malformed, long, unsupported-language, and
absent-media-path probes. `Engine.process()` returns a contract-valid
clarification with `internal_error` if an unexpected exception escapes the
pipeline; `ENGINE_STRICT=1` re-raises it in tests. The phrase matcher in
`perception/text_matching.py` caches whole-word cue patterns,
`lexicon.match_clause()` checks phrases indexed by their first token, and
`detect_intent()` scans combined cues rather than rescanning the whole message
for every phrase. On Python 3.12, a 5,000-word message took a median 40.7 ms
and a maximum 42.6 ms over five fresh-engine runs, below the configured
100-ms test budget. This is a local benchmark, not a guarantee for slower
hardware.

## How to change it

- Adjust shared thresholds and trade-offs in
  `affective_project/engine/config.py`.
- Change normalization, matching, rules, language, sarcasm, or intents in the
  corresponding `engine/perception/` module. Preserve whole-word boundaries
  in `text_matching.py`; the long-input probe protects the matching path.
- Add focused tests in `affective_project/tests/test_perception.py`, using
  fresh unit-test sentences rather than evaluation messages.
- Review tier choices in `../lexicon_review_sheet.csv`, fill `my tier` where
  needed, and run
  `py -3.12 -m engine.tools.sync_lexicon_tiers <path-to-sheet>` from the kit
  directory. The engine reads the TSV files only.
- Run the unit suite and contract test using the commands in
  `affective_project/engine/README.md`.

The scenario runner prints V/A/confidence/labels for every scenario turn. Do
not run it on the evaluation messages until the student's SAM ratings are
complete. At this checkpoint, report scenario verification as pass/fail only.

## Likely questions

1. **Why use a hybrid lexicon and rules?** Each cue can be inspected and changed
   without a model download or dependency, while phrases and local rules cover
   cases a one-word lookup misses.
2. **Why is there a `low_confidence` flag rather than an uncertain label?**
   This follows the approved Phase 0 choice to preserve the nearest coarse
   prototype label and expose uncertainty separately.
3. **Are the tiers authoritative?** The VAD centers are the supplied tier
   table; per-word tier suggestions are provisional and not human SAM results.
4. **What remains for later phases?** Affective-state mapping refinement,
   conversation state, action policy, tailored replies, and optional channels
   remain outside this text-perception phase.
5. **How is a Latin-script language identified?** `language.py` combines
   distinctive stopwords with supported word- and phrase-lexicon evidence,
   then gives foreign stopwords priority when their evidence is stronger.

## Live-change drills

1. Using only unit-test sentences, adjust
   `CONTRAST_LATER_WEIGHT` in `config.py`; verify the post-contrast clause
   remains more influential and the existing relation test still passes.
2. Change a tier suggestion in the review sheet, sync it to the TSVs, and test
   a new non-evaluation sentence that contains it. Do not infer performance
   on the held-out evaluation conversations.
3. Lower `TEXT_LATENCY_BUDGET_SECONDS` in `engine/config.py` temporarily and
   run `py -3.12 -m unittest discover -s tests -p test_robustness.py` to see
   the long-message performance assertion tighten; restore the configured
   value afterward.
