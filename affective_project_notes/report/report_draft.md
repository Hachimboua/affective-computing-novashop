# NovaShop Affective Support Engine — report draft

> **AI-drafted scaffold.** Rewrite every section in your own words before you
> export `report.pdf`. Markers:
> `[[TODO]]` = a number or fact still missing (usually from the evaluation),
> `[[WRITE IN MY OWN WORDS]]` = a personal statement only you can write,
> `[[CHECK]]` = verify against the official source.
> Never paste numbers that are not in `engine/evaluation/results/`.

**Cover page (not counted):** Affective Computing project — NovaShop affective assistant. Student: [[name]], solo project ([[GroupXX]]). Date: [[date]].
**Index (not counted).**

## Page budget (7–12 pages of body text ≈ 3,500–5,500 words)

| Section | Target words | Figures/tables (not counted) |
|---|---|---|
| 1. Introduction and scenario | 400 | System overview diagram |
| 2. Text perception (topic 1) | 800 | Pipeline figure; tier table |
| 3. Affective model, map and voice (topic 2) | 800 | Prototype table; map screenshot; voice-check table |
| 4. Decision, state and robustness (topic 3) | 800 | Rule table R0–R7 |
| 5. Software, interface, tests and demo (topic 4) | 500 | Test summary table |
| 6. Evaluation (topic 5) | 700 | Metrics table; confusion matrix; calibration |
| 7. Ethics and limits | 500 | — |
| 8. Difficulties and issues | 400 | — |
| 9. Use of AI | 300 | — |
| **Total** | **≈ 5,200** | |

---

## 1. Introduction and scenario

NovaShop is a fictional online electronics store. The goal of the project is the engine of its customer-support assistant: for every customer message it estimates the emotional state, keeps track of how that state changes over the conversation, and chooses one of six actions (answer, answer with empathy, ask for clarification, offer a human, escalate, close positively) together with a reply.

The work follows the shared project kit: the interface (`run_app.py`), the scenario runner (`run_scenario.py`) and the harness are unchanged (checked byte by byte against the original kit, `tests/test_kit_unchanged.py`); all our code is in `engine/` and our tests in `tests/`.

**How the work was organised.** [[WRITE IN MY OWN WORDS: you did the project alone, covering all five expert topics; explain the order you worked in (kit discovery → evaluation data → perception → affective model → state and policy → robustness → integration → voice → evaluation → documentation), how you used phases with a test gate after each, and what you decided to leave out (face channel, statistics-based model) and why.]]

## 2. Text perception (topic 1)

**What was built.** A knowledge-based estimator (`engine/perception/`) that turns a message into valence, activity and dominance in [-1, 1], a confidence in [0, 1], a language, a support intent and a list of flags.

**How it works.**
1. *Pre-processing* (`preprocess.py`): Unicode normalisation, lower-casing for lookup (the original is kept for caps and punctuation cues), letter elongation ("sooo"), tokens for words, emojis, emoticons and punctuation runs, and clause splitting at sentence ends and contrastive words (*but, however, mas, porém*).
2. *Language identification* (`language.py`): English and Portuguese stop-words plus distinctive lexicon hits, and a Unicode script check. Other languages get the flag `unsupported_language` and a capped confidence.
3. *Lexicon* (`lexicons/*.tsv`): 369 English words, 150 Portuguese words, 34 English and 18 Portuguese phrases, and 20 emojis. Each entry belongs to one of **12 affective tiers** (for example ANGER_STRONG, FRUSTRATION, PROBLEM_MILD, FEAR, SADNESS, CONTENT, JOY); the V/A/D value of each tier is defined once in `config.TIER_VAD`. Phrases are matched before single words (longest match wins).
4. *Rules* (`rules.py`): negation shifts valence by a factor of −0.6 instead of flipping it (so "not bad" is mildly positive and "not good" mildly negative), within a scope of 3 tokens; intensifiers and downtoners multiply the next affective word; exclamation marks and capitals raise activity; after a contrastive word the later clause weighs 0.7 and the earlier 0.3; domain cues (repetition, urgency, demands, helplessness, legal threats, profanity) adjust the estimate or add flags.
5. *Sarcasm* (`sarcasm.py`): a score from known idioms ("thanks for nothing", "obrigado por nada"), incongruity (positive words next to a negative event such as "broke again"), scare quotes, and a negative conversation context. Above 0.6 the positive contributions are inverted and confidence is reduced.
6. *Aggregation and confidence* (`text_estimator.py`): a weighted mean of the contributions squashed with tanh. Confidence grows with the amount of evidence, falls with conflicting cues, short messages, sarcasm and unknown words, and a well-formed neutral sentence gets a moderate "evidence of neutrality" instead of a minimum value.

**Why this design.** [[WRITE IN MY OWN WORDS: knowledge-based (lexicon + rules) versus statistics-based (a model trained on labelled data): no training data of our own, need to explain and change every decision live, offline and standard-library-only constraint; the cost is limited vocabulary and hand-made rules. Mention VADER and SO-CAL as inspirations (shift negation).]]

**Lexicon review.** The first lexicon values were generated in fixed patterns and had real errors (low-energy words like *disappointed* with high activity, *slow* more negative than *furious*). We replaced per-word numbers with tiers and reviewed the tier of each word. [[WRITE: how many tiers you changed in your review and examples.]]

**Results.** On new sentences that are not in the evaluation set, the perception tests check negation, intensity, caps, sarcasm, Portuguese and unsupported languages (`tests/test_perception.py`). Evaluation against human ratings: see section 6 [[TODO]].

## 3. Affective model, map and voice (topic 2)

**Affective space.** We use the dimensional view (valence, activity/arousal, dominance — Russell, 1980; Mehrabian & Russell, 1974). The interface draws valence on x and activity on y; because the engine also returns dominance, the 3D view is enabled.

**Labels from dimensions** (`engine/affect/space.py`). The label is the nearest of seven prototypes in V/A/D space (dominance weighted 0.5), with a neutral radius of 0.18 around the origin:

| Label | V | A | D |
|---|---|---|---|
| anger | −0.70 | 0.60 | 0.30 |
| frustration | −0.55 | 0.35 | 0.10 |
| fear | −0.60 | 0.55 | −0.50 |
| sadness | −0.60 | −0.40 | −0.35 |
| calm | 0.40 | −0.45 | 0.25 |
| joy | 0.75 | 0.50 | 0.40 |
| neutral | 0 | 0 | 0 |

Dominance is what separates fear (low control) from anger (high control), which is exactly what practice scenario P3 asks for. The runner-up label and both distances are written to the log. When confidence is low the nearest label is kept and the flag `low_confidence` is added.

**Voice channel (optional)** (`engine/voice/`). Implemented by hand with numpy: pre-emphasis, 25 ms frames with a 10 ms hop, Hamming window, FFT power spectrum, RMS energy, zero-crossing rate, spectral centroid, autocorrelation pitch (75–500 Hz) with median smoothing, a 26-filter mel bank and 13 MFCCs. Activity comes from energy (weight 0.65), pitch **variability** (0.20) and a speaking-rate proxy (0.15), standardised against reference statistics. Absolute pitch is not used, because the kit's two calm speakers differ only in pitch (90 vs 260 Hz). Confidence combines duration, voiced ratio, an SNR estimate and clipping. Late fusion (`engine/affect/fusion.py`) weights each modality by its confidence; voice contributes mostly to activity (weight 0.6) and very little to valence (0.1). Without numpy, or with a missing/invalid file, the engine returns the text-only result with the flag `audio_unavailable`.

**Voice check on the kit audio** (real output of `python -m engine.evaluation.evaluate --voice-check`):

| File | Voice activity | Voice confidence |
|---|---|---|
| calm_clean | −0.24 | 0.90 |
| agitated_clean | +0.25 | 0.90 |
| calm_noisy | −0.06 | 0.05 |
| agitated_noisy | +0.32 | 0.05 |
| speaker_low | −0.10 | 0.90 |
| speaker_high | −0.18 | 0.90 |

Agitated is more activated than calm; both calm speakers stay calm despite very different pitch; noisy recordings get much lower confidence, so the fused result falls back to the text. [[WRITE: limits — six synthetic files only, no real speakers, the SNR estimate is rough, and noisy files are treated as "no speech".]]

## 4. Decision, state over time and robustness (topic 3)

**State** (`engine/state/tracker.py`). A confidence-weighted exponential moving average per dimension: `s ← s + α·c·(x − s)` with α = 0.5 (`STATE_ALPHA`). A high α reacts quickly but is noisy; a low α is stable but lags. The tracker also keeps the last 8 turns and derives: trend (slope of the last 4 valences), negative streak, severe streak, clarification streak, whether a person was offered or declined, repeated issue, and resolution.

**Policy** (`engine/policy/policy.py`): an ordered list of named rules; the first that applies wins, and its name and a reason with the actual numbers are written to the log (`details.rule`, `details.reason`).

| Rule | Action | When |
|---|---|---|
| R0_SAFETY | ESCALATE | safety cue |
| R1_HUMAN_REQUEST | OFFER_HUMAN (ESCALATE if already offered, urgent cue or severe state) | explicit request for a person |
| R2_ESCALATE | ESCALATE | legal or authority threat, abuse, severe state for 2 turns, or 4 negative turns with a worsening trend |
| R3_CLOSE | CLOSE_POSITIVE | closing intent, valence ≥ 0.35, no sarcasm |
| R4_UNCERTAIN | ASK_CLARIFICATION (OFFER_HUMAN after 2 in a row) | low confidence, short/ambiguous message, unsupported language |
| R5_OFFER_HUMAN | OFFER_HUMAN | persistent negative state (≤ −0.45 with 3 negative turns or worsening trend), repeated issue, or a short shout in distress |
| R6_EMPATHY | ANSWER_EMPATHIC | negative state or message, with hysteresis (exit only above −0.15) |
| R7_DEFAULT | ANSWER | otherwise |

**OFFER_HUMAN vs ESCALATE** (provisional, `[[CONFIRM with the teacher]]`): offering a transfer that the customer can accept, versus an urgent priority handover. Explicit signals win over the emotion estimate (scenario M3).

**Replies** (`engine/policy/replies.py`): templates per action and intent in English and Portuguese, two variants chosen deterministically, in the customer's language, bilingual when the language is not supported. Rules: name the problem, give a concrete next step, never claim to be human, never invent an order status, mention emergency services only for safety cues.

**Robustness.** A safety net returns a valid result on any internal error (flag `internal_error`; re-raised in tests with `ENGINE_STRICT=1`). Probes include empty text, `None`, numbers, 20,000 characters, emojis, HTML, other scripts and missing audio. A 40-message hidden-test rehearsal (`tests/test_rehearsal.py`) covers all six actions.

[[WRITE: one example conversation explained turn by turn with the rule that fired — use a new sentence set, not the evaluation messages, unless your ratings are done.]]

## 5. Software, interface, tests and demo (topic 4)

- Architecture: `engine/engine.py` composes perception → (voice + fusion) → label → state → policy → reply; all settings in `engine/config.py`, each with a comment on its trade-off.
- Contract: plain Python types, values in range, never raises; checked by the kit's `tests/test_contract.py`.
- Tests: 131 automated tests in 15 files (perception, policy, state, replies, robustness, rehearsal, scenarios, integration, voice, metrics, evaluation, rating tool, contract, kit unchanged). They pass on Python 3.9 without numpy (voice tests skipped) and on Python 3.12/3.13 with numpy.
- Reproducibility: deterministic engine, a clean-copy check (`affective_project_notes/tools/clean_copy_check.py`) and a byte-for-byte kit check (`verify_kit.py`).
- Demo: [[TODO: describe the video — M1–M4 in order, the log, the voice example]].

## 6. Evaluation (topic 5)

**Procedure.** 88 messages in 28 conversations: the 28 kit scenario messages and 60 new fictional messages covering negation, sarcasm, short messages, other languages, legal threats and closings; split by conversation into dev (tuning) and test (final numbers). Raters used the Self-Assessment Manikin (Bradley & Lang, 1994) on 9-point scales for valence, arousal and dominance, plus a label and the action they thought right, with earlier turns shown as context and no engine output shown. Ratings were converted with (r − 5) / 4. [[TODO: number of raters, how they were recruited, consent.]]

**Agreement between raters.** [[TODO: Krippendorff's alpha per dimension, mean pairwise Pearson, Fleiss' kappa for label and action — from `test_summary.md`. Explain that human agreement is the ceiling for the engine.]]

**Engine vs humans (test split).** [[TODO: table from `engine/evaluation/results/test_summary.md`: Pearson with 95% CI and MAE for V/A/D, label and action accuracy and macro-F1, cost-weighted action error — for the starter baseline, the full engine and the three ablations.]]

**Ablations.** [[TODO: what changed when negation, sarcasm detection or state smoothing were switched off, and what that says about each component.]]

**Calibration.** [[TODO: error per confidence bin; is confidence meaningful?]]

**Error analysis.** [[TODO: the 15 largest errors from `test_errors.csv`, your own category for each (sarcasm, negation, missing word, short/ambiguous, other language, mixed emotion, state lag, rater disagreement), counts per category, and a concrete fix for the two biggest categories.]]

**Limits of the evaluation.** Few raters, fewer than 100 messages, wide confidence intervals; dev and test written by the same person; ratings of expressed (not felt) emotion.

## 7. Ethics and limits

[[Use `affective_project_notes/ethics/ethics.md` — summarise data inventory, GDPR, AI Act (with checked articles and dates), bias, what the system cannot do, and the design commitments.]]

## 8. Difficulties and issues

Real problems met during the project (details in `affective_project_notes/DIFFICULTIES.md`):

1. **Edit scope.** The kit allows edits only in `engine/`, while documentation and tests had to live somewhere: engine code and evaluation went into `engine/`, new tests into `tests/` (as the brief allows), notes outside the delivered code.
2. **Encoding.** Writing files through the Windows console replaced accented Portuguese letters with `?` (38 lexicon entries such as *péssimo*, *não chegou*). Fixed by rewriting the files as UTF-8 and making the loader reject damaged entries.
3. **Lexicon fragments.** Multi-word expressions had been split into single words, giving strong positive values to words like *a*, *customer* and *service*. Fixed by moving them to phrase files and adding a test that no stop-word appears in the word lexicons.
4. **Language detection.** A rule meant to catch other languages also fired on ordinary English, which then received no emotion at all. Fixed by counting lexicon hits as language evidence and treating 1–2-word messages as short, not foreign.
5. **Lexicon values.** Generated values were inconsistent (activity of sad words, intensity order); replaced by a tier system reviewed word by word.
6. **Line endings and the kit check.** A git operation converted the kit files to Windows line endings, and a checksum test was then weakened to ignore line endings instead of fixing the files. Found in an external review; the original files were restored byte for byte, the test reverted to raw bytes, and a rule "never weaken a test" was added.
7. **Plain questions and replies.** Neutral questions without a known topic got minimum confidence and a request for clarification; some replies contradicted the action. Fixed with neutral-evidence confidence and action-aware replies.
8. **Voice.** Absolute pitch wrongly made the high-pitched calm speaker look agitated; activity now uses pitch variability and energy.

[[WRITE IN MY OWN WORDS: which of these you found hardest, what you learned, and what you would do differently.]]

## 9. Use of AI

[[WRITE IN MY OWN WORDS, using `AI_LOG.md`. Be specific:
- which tools you used (a chat assistant, Claude, to write the project prompts and to review the code; a coding agent [[name of the tool]] to implement the phases);
- what was asked and produced in each phase;
- what you changed yourself (for example the tier review, the evaluation messages, decisions on OFFER_HUMAN vs ESCALATE);
- how you verified it: the automated tests, the scenario runs, and the independent reviews that found the encoding, fragment, language-detection, line-ending and reply bugs listed in section 8;
- what you can now explain and change yourself.]]

## References

- Barrett, L. F., et al. (2019). Emotional expressions reconsidered. *Psychological Science in the Public Interest, 20*(1), 1–68.
- Bradley, M. M., & Lang, P. J. (1994). Measuring emotion: the Self-Assessment Manikin and the semantic differential. *Journal of Behavior Therapy and Experimental Psychiatry, 25*(1), 49–59.
- Hutto, C., & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. *Proceedings of ICWSM.*
- Krippendorff, K. (2011). Computing Krippendorff's alpha-reliability. University of Pennsylvania.
- Mehrabian, A., & Russell, J. A. (1974). *An approach to environmental psychology.* MIT Press.
- Russell, J. A. (1980). A circumplex model of affect. *Journal of Personality and Social Psychology, 39*(6), 1161–1178.
- Taboada, M., Brooke, J., Tofiloski, M., Voll, K., & Stede, M. (2011). Lexicon-based methods for sentiment analysis. *Computational Linguistics, 37*(2), 267–307.
- Regulation (EU) 2016/679 (GDPR); Regulation (EU) 2024/1689 (AI Act).

## Appendices (not counted)

A. Main configuration settings (copy the table from `engine/README.md`).
B. Full metrics (`engine/evaluation/results/*_summary.md`).
C. AI log (`AI_LOG.md`).
D. Contribution statement (`report/contribution_statement.md`).
