# Text-perception data sources

The legacy per-term VAD estimates retained in the review sheet were AI-assisted
provisional values, not imported from a published lexicon. Runtime VAD values
come from the tier table in `affective_project/engine/config.py`; the per-term
tier suggestions are AI-assisted and have not yet been reviewed by the student.
Neither set of values is human-validated ground truth.

| File | Entries | Valence range | Activity range | Dominance range |
|---|---:|---:|---:|---:|
| `affective_project/engine/perception/lexicons/en.tsv` | 367 | -0.85 to 0.80 | -0.60 to 0.80 | -0.50 to 0.40 |
| `affective_project/engine/perception/lexicons/pt.tsv` | 150 | -0.85 to 0.80 | -0.60 to 0.80 | -0.50 to 0.40 |
| `affective_project/engine/perception/lexicons/phrases_en.tsv` | 33 | -0.70 to 0.80 | -0.45 to 0.60 | -0.50 to 0.40 |
| `affective_project/engine/perception/lexicons/phrases_pt.tsv` | 18 | -0.70 to 0.50 | -0.45 to 0.60 | -0.50 to 0.30 |
| `affective_project/engine/perception/lexicons/emoji.tsv` | 21 | -0.82 to 0.85 | -0.35 to 0.80 | -0.60 to 0.45 |

Each VAD coordinate is finite and within [-1, 1]. The loader rejects empty
or duplicate terms and values outside that range. The inventory includes
English and Portuguese single words and phrases plus emoji/emoticon entries.
Record any later human review and changes separately; do not describe these
initial estimates as a sourced or validated external lexicon.

The [review sheet](./lexicon_review_sheet.csv) exports all 568 English and
Portuguese word and phrase entries, grouped by suggested tier. Tier suggestions
are meaning-based and remain unreviewed; the engine uses the suggestions until
the student supplies a `my tier` choice. The legacy V/A/D and `my value` columns
are retained for reference and do not drive runtime values. `Review flag` marks
potentially contradictory legacy VAD entries; none were changed during tiering.
Per-coordinate overrides in the TSVs remain blank unless explicitly set.

After editing `my tier`, run
`py -3.12 -m engine.tools.sync_lexicon_tiers <path-to-sheet>` from the
`affective_project` directory. The script copies the student's choice, or the
suggested tier when `my tier` is empty, into the TSV `tier` column. Runtime
loads only those TSVs and never reads the review sheet.
