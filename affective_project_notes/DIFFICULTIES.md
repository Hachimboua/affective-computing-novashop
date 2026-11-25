# Difficulties and issues

## Phase 0

- The initial prompt supplied a prompt-file path but not the kit directory.
  The expected harness and scenarios were absent from the repository root.
  The student then provided `Student_Kit_to_share_with_students`; discovery
  located the actual kit under its `affective_project/` subfolder.
- The kit README restricts edits to `engine/`, while the master prompt asks
  for new tests, evaluation files, and documentation. The student resolved
  this by keeping engine/evaluation code under `engine/`, placing new tests
  only in `tests/`, placing notes outside the kit in the sibling
  `affective_project_notes/`, leaving the kit-root README unchanged, and
  adding remaining scope questions for the teacher.
- Scenario runs create logs under the kit's `logs/` directory. The baseline
  session logs were copied into the notes folder and the run-generated copies
  were removed; the pre-existing `logs/README.txt` was preserved.
- No consenting raters or confirmed retention period were supplied during
  Phase 1. The rating workflow and consent draft are ready, but real ratings
  have not been collected; the consent draft retains visible TODOs for access
  and deletion timing. The teacher also needs to clarify the action semantics
  before raters judge `OFFER_HUMAN` versus `ESCALATE`.

## Phase 2

- The first generated emoji lexicon was affected by Windows console text
  encoding, replacing emoji characters with question marks. Rewrote the data
  as UTF-8 and added support and a focused test for emoji variation selectors.
- Lexicon entries and sarcasm/language rules are provisional hand-assigned
  heuristics. The SAM ratings are still uncollected, so no threshold tuning
  against the evaluation set was performed.
- Scenario integration was verified with logs and per-message estimates
  suppressed; only scenario pass/fail status was retained for this checkpoint.
- The Latin-script fallback improves detection of languages outside English
  and Portuguese but remains a heuristic; terse or domain-heavy English can
  also have few supported stopwords.
- Six selected test-split messages were reworded without changing their
  conversation, turn, split, or case-type metadata. The blank SAM template was
  synchronized to keep its text in agreement with the dataset.

### Phase 2 follow-up: lexicon issues

- Portuguese lexicon entries had accented characters replaced by `?` in
  `pt.tsv` and `phrases_pt.tsv`. Rewrote the affected entries as UTF-8,
  corrected the intended words, and added loader rejection and matching tests.
- English phrase fragments such as `customer`, `service`, and `quickly` had
  been assigned standalone word values, making neutral words misleading
  sentiment evidence. Removed the fragments from `en.tsv` and represented
  complete expressions in `phrases_en.tsv`.
- The Latin-language fallback over-triggered on ordinary English and sometimes
  overrode supported phrase evidence. Language identification now considers
  distinctive English/Portuguese lexical evidence and foreign stopwords, with
  regressions for English, Portuguese, and borrowed English phrases.
- Flat per-entry VAD values were inconsistent for low-energy emotions and
  strong anger. Switched word and phrase lexicons to the supplied tier table,
  retained optional per-coordinate overrides, and made meaning-based tier
  suggestions available for student review and synchronization. Suggestions
  remain unreviewed; no evaluation-message outputs were used.
