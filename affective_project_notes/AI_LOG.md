# AI log

## 2026-11-25 - Phase 0 - Topic 4

- **What I asked for:** Use the supplied NovaShop master prompt, discover the
  student kit, and complete Phase 0 without changing protected kit files.
- **What the AI produced:** Saved a verbatim copy of the master prompt; read
  the kit README, starter engine, harness, contract test, scenarios, and audio
  notes; recorded baseline outputs and checksums; copied the starter engine
  for later comparison; proposed an architecture and initial thresholds; added
  a new `tests/test_kit_unchanged.py` checksum test. See `KIT_NOTES.md`,
  `kit_checksums.txt`, and `evaluation/baseline_logs/`.
- **What I changed:**
- **How I verified it:**

## 2026-11-25 - Phase 1 - Topic 5

- **What I asked for:** Start the human-rating dataset and SAM rating kit
  before tuning the engine, keeping test conversations separate from dev.
  The student also instructed that engine V/A/labels for these 88 messages
  remain undisplayed until their own ratings are complete, and that Phase 2
  show scenario pass/fail only.
- **What the AI produced:** Added 60 original AI-drafted messages in 20
  conversations, combined them with the 28 scenario messages in
  `engine/evaluation/data/messages.csv`, created the resumable
  `engine/evaluation/rate.py` CLI and spreadsheet template, and drafted consent
  and rating instructions in `affective_project_notes/ethics/`. Added focused
  tests in `tests/test_rating.py`.
- **What I changed:**
- **How I verified it:**

## 2026-11-25 - Phase 2 - Topic 1

- **What I asked for:** Implement text perception without tuning on the 88
  evaluation messages or displaying their engine valence, activity, or labels.
  At the checkpoint, report scenario pass/fail only and use unit-test
  sentences for examples.
- **What the AI produced:** Added the standard-library English/Portuguese
  perception pipeline, configurable thresholds, bundled provisional lexicons,
  focused tests, source notes, and engine run/test instructions. The public
  engine contract remains in place; action policy and replies remain
  temporary. Added the Phase 2 topic notes and documented remaining limits.
- **What I changed:**
- **How I verified it:** On Python 3.12.10, all 24 discovered tests passed.
  All eight mandatory/practice scenarios passed the contract/integration
  check; only pass/fail status was displayed. No evaluation-message V/A/labels
  were displayed or used for tuning.

## 2026-11-25 - Phase 2 follow-up

- **What I asked for:** Use only the kit's seven emotion labels in the engine
  and rating CLI; broaden sarcasm cues; flag unsupported Latin-script
  languages; document the label/confidence rules; reword six test-split rows;
  and keep engine output for all 88 messages hidden.
- **What the AI produced:** Updated engine/rater labels, language detection,
  sarcasm event and idiom cues, focused tests and docs. Reworded the six
  requested test-split messages while preserving their conversation IDs,
  turns, and case types, and synchronized the blank rating template.
- **What I changed:**
- **How I verified it:** All 28 tests passed on Python 3.12.10. The six
  rewritten rows remain in the test split and are no longer near-copies of the
  scenario messages by the similarity check; the dataset and rating template
  remain synchronized at 88 rows. No per-message engine output was displayed.

## 2026-11-25 - Phase 2 follow-up: lexicons and language detection

- **What I asked for:** Repair corrupted Portuguese lexicon entries, remove
  English phrase fragments from the word lexicon, improve supported-language
  evidence, and add new regression sentences without using the 88 evaluation
  messages for engine output or tuning.
- **What the AI produced:** Corrected the Portuguese word and phrase lexicons,
  made the loader reject `?` and U+FFFD, moved English phrase fragments into
  phrase entries, added the requested common words, and combined stopword and
  distinctive lexicon evidence for language identification. Added 30 English
  and 15 Portuguese language regressions, valence and lexicon regressions, and
  checks that the new sentence sets are absent from `messages.csv`. Refreshed
  lexicon inventory ranges and the language-detection notes.
- **What I changed:** None recorded.
- **How I verified it:** All 34 tests passed on Python 3.12.10, including the
  checks that regression sentences are not in `messages.csv`. No engine
  output for the 88 evaluation messages was produced or displayed.

## 2026-11-25 - Phase 2 follow-up: word review and language stopwords

- **What I asked for:** Remove neutral fragments and invented English forms,
  add requested phrases and words, export both word lexicons for review, test
  low-energy activity and anger valence, and flag unsupported languages when
  foreign stopwords appear without supported-language stopwords.
- **What the AI produced:** Removed the requested English fragments and
  nonstandard derivatives, added `relaxed` and five English phrases, expanded
  German/French/Dutch stopword detection, and added the requested regressions.
  Created `lexicon_review_sheet.csv` with all 518 English/Portuguese word
  entries grouped by the kit's emotion categories, blank `my value` cells, and
  21 review flags. Existing flagged VAD values were not changed.
- **What I changed:** None recorded.
- **How I verified it:** All 38 tests ran. The language, phrase, neutral-shop,
  and contract checks passed; five low-energy/anger value assertions remain
  failing on entries awaiting the student's review. No engine output for the
  88 evaluation messages was produced or displayed.

## 2026-11-25 - Phase 2 follow-up: tiered lexicons

- **What I asked for:** Replace per-entry VAD values with configurable tiers,
  add meaning-based suggested tiers and blank student choices to the review
  sheet, retain coordinate overrides, and keep the review sheet outside the
  runtime engine.
- **What the AI produced:** Added the supplied 12-tier VAD table to
  `engine/config.py`; migrated English/Portuguese word and phrase TSVs to
  tier plus optional coordinate overrides; and added a standalone
  `engine/tools/sync_lexicon_tiers.py`. The review sheet now contains all 568
  word and phrase entries, suggested tiers, blank `my tier` cells, and the
  original VAD columns for reference. Removed the neutral `replacement` word
  entry and documented that tier suggestions are unreviewed.
- **What I changed:** None recorded.
- **How I verified it:** All 41 tests passed on Python 3.12.10. The sync
  command processed all 568 entries, preserving blank overrides; tests cover
  partial coordinate overrides and `my tier`/suggestion fallback. The engine
  does not reference the review sheet or sync script. No engine output for the
  88 evaluation messages was produced or displayed.

## 2026-11-25 - Phase 3 - Topic 2

- **What I asked for:** Replace threshold-based emotion labels with nearest
  V/A/D prototypes using dominance weight 0.5 and a neutral radius; include
  the runner-up and distances; test the requested new sentences; keep the
  88-message engine output hidden.
- **What the AI produced:** Added the affect-space conversion and prototype
  classifier, configured the seven kit labels, added focused and
  generalization regressions, and drafted the Topic 2 study notes. A
  Portuguese calm-lexicon coverage gap remains documented for student review.
