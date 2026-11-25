# Topic 2: Affective space and labels (Phase 3)

## How it works

A dimensional model represents expressed affect as coordinates rather than
choosing a category immediately. This engine uses valence (negative to
positive), activity (deactivated to activated), and dominance (helpless to in
control). A label is a useful summary, but it loses detail; the dimensions
remain in the output.

The estimator derives V/A/D from text evidence. `engine/affect/space.py`
converts 1-9 Self-Assessment Manikin ratings to the unit scale and maps a
point to the closest prototype with weighted Euclidean distance:

`distance = sqrt((V - Vp)^2 + (A - Ap)^2 + LABEL_D_WEIGHT * (D - Dp)^2)`

The prototype coordinates and distance weight are in
`affective_project/engine/config.py`. They are approximations inspired by
dimensional affect models, not measured boundaries between emotions.
`LABEL_NEUTRAL_RADIUS` reserves a small region around the origin for
`neutral`. If the point lies outside that region, the closest prototype wins.
The output's `details` include `second_label`, `label_distance`, and
`second_distance`, so a nearby alternative is visible instead of hiding
classification ambiguity.

For example, the new test sentence “The repeated billing error is wearing me
down.” produced V=-0.560, A=-0.086, D=-0.199 and the label `sadness`. Its
weighted distance to `sadness` was 0.334; the runner-up was `frustration` at
0.485. These are unit-test example values, not evaluation results. The 2D map
plots valence horizontally and activity vertically; dominance can add a third
axis when the interface supports it. A low-confidence estimate keeps its
nearest label and exposes uncertainty through `low_confidence`.

The inverse SAM conversion supports evaluation later. No SAM ratings were
available during this phase, so the prototypes were not tuned against the
evaluation messages.

## Optional voice channel (Phase 7)

The optional voice path reads mono or stereo 16-bit PCM WAV data and extracts
short-time energy, zero-crossing rate, spectral centroid, autocorrelation
pitch, Mel-frequency cepstral coefficients, a voiced-frame speaking-rate
proxy, signal-to-noise estimate, and clipping ratio. NumPy is an optional
dependency; if it is absent or the WAV cannot be read, the engine keeps its
text-only result and adds `audio_unavailable`. Silence is represented with
`no_speech`, rather than treating a silent recording as emotional evidence.

Late fusion scales the text and voice contribution by each modality's
confidence. Text remains the primary source for valence, while voice can
contribute more to activity. Mean pitch is not used as an emotion cue because
the bundled low- and high-pitch speaker examples are both calm; pitch
variability is only a weak cue. Agreement can modestly increase confidence,
while opposite polarity or strongly positive text with flat prosody can lower
confidence and add `modality_conflict`. The output preserves separate `text`
and `voice` estimates alongside `fused`, so the approximate voice contribution
is inspectable. These fixture-based heuristics are not human-calibrated.

## How to change it

- To change the label geometry, edit one prototype row in
  `affective_project/engine/config.py`; expected effect: points near that
  coordinate become more likely to receive that label.
- To make dominance more influential, adjust `LABEL_D_WEIGHT` in the same
  file; expected effect: differences in perceived control alter the nearest
  label more strongly.
- To expand or shrink the neutral region, adjust `LABEL_NEUTRAL_RADIUS`;
  expected effect: a larger radius labels more low-magnitude points neutral.
- To change conversion between the 1-9 SAM scale and the unit scale, update
  `sam_to_unit` and `unit_to_sam` in `affective_project/engine/affect/space.py`
  and keep their inverse tests synchronized.
- To add a label, add its V/A/D prototype to `LABEL_PROTOTYPES` and add a
  focused test using a new sentence; no other label vocabulary should be
  introduced.

## Likely teacher questions

1. **Why keep both dimensions and a label?** A label is readable, while V/A/D
   preserve intensity and control information; both are returned by
   `engine/perception/text_estimator.py`.
2. **How is the label chosen?** `classify_vad` in `engine/affect/space.py`
   ranks prototypes by weighted Euclidean distance and applies the neutral
   radius from `engine/config.py`.
3. **Why weight dominance by 0.5?** It lets control cues matter without
   allowing dominance to overwhelm valence and activity; the trade-off is
   explicit in `LABEL_D_WEIGHT`.
4. **What does the runner-up tell us?** It shows the next-nearest label and
   distance in the engine's `details`, which helps explain borderline
   classifications.
5. **Are the prototypes empirically validated?** No. They are documented
   approximations, and tuning awaits real SAM ratings; no evaluation-message
   outputs were used.
