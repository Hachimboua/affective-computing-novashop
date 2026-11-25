# Open questions

## For the teacher

- Are new files under `tests/` permitted, given that the Project Brief says the
  contract test "can be extended with your own tests" but the kit README says
  work only in `engine/`? The existing contract test will remain unchanged.
- Is adding a student run/test README at the project root permitted? The
  current decision is to leave the kit-root README unchanged and put those
  instructions in `engine/README.md`.
- What exact distinction should the policy use between `OFFER_HUMAN` and
  `ESCALATE`? The kit lists both names but gives no definitions.
- Is Portuguese the sole required language beyond English? The mandatory M4
  scenario includes Portuguese; other language requirements are unspecified.
- Is the optional voice channel in scope, and are the synthetic WAVs the only
  approved audio data? The master prompt recommends voice only after the text
  engine is complete and says to skip face.
- What Python version is installed on the teacher's machine? The kit says 3.9+;
  this environment has Python 3.14.6.
- Please confirm the solo-project approval, group identifier, delivery
  deadline, student display name, and whether SAM raters are available.

## Resolved for implementation

- Architecture approved: preserve `engine.engine.Engine`, organize modules
  under `engine/`, and follow the kit/notes/test file boundaries recorded in
  `KIT_NOTES.md`.
- Low confidence keeps the nearest prototype label and adds a
  `low_confidence` flag; do not introduce a separate `uncertain` label.
- Until the student confirms their own SAM ratings are complete, do not
  display the engine's valence, activity, or label for any of the 88 evaluation
  messages (including scenarios). Phase 2 reporting should show scenario
  pass/fail only and use unit-test sentences for worked examples. Do not tune
  on this dataset before the student's ratings are complete.

## Still to confirm

- Confirm Section 0 choices for optional channels, supported languages, and
  Python compatibility target. Leave unknown facts marked `[[TODO: ...]]`;
  do not invent them.
- Group identifier and the replacement deadline are still unknown; packaging
  must not invent either value.

## Decided by the AI, to confirm

- Until the teacher clarifies the action semantics, use the continuation
  prompt's provisional distinction: `OFFER_HUMAN` offers a transfer for a
  human request or persistent unresolved distress; `ESCALATE` is an urgent
  priority handover for safety, abuse, legal/authority threats, or sustained
  severe high-activation distress. Explicit legal or safety signals take
  priority over the emotion estimate.
- With no real ratings present, Phase 9 will stop after implementing and
  testing the evaluation pipeline; no placeholder ratings or metrics will be
  created, and later report/video material will use `[[TODO]]` placeholders.
- The student selected the optional voice channel, so implement it only after
  the Phase 6 integration gate passes. Skip face as directed by the
  continuation prompt.
- The Phase A1 audit found that the Phase 0 protected blobs in `HEAD` already
  matched the original ZIP, although 23 working-tree files had different raw
  bytes. The rebase preceded `.gitattributes`, and Phase 3 had normalized the
  test hash; the byte-copy, raw-byte test, local `core.autocrlf=false`, and ZIP
  verifier now address the discrepancy without rewriting Git history.
