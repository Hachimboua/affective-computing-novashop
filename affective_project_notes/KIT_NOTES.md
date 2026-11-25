# Phase 0: Kit discovery and plan

## Scope and source

The starter kit is `../affective_project/`. The kit README is authoritative for
kit files. Per the student's scope decision:

- Leave the kit-root `README.md`, `requirements.txt`, `harness/`,
  `run_app.py`, `run_scenario.py`, scenarios, assets, and the original contract
  test unchanged.
- Put engine and evaluation code under `engine/`; put evaluation scripts under
  `engine/evaluation/` and run/test instructions in `engine/README.md`.
- Put only new test files in `tests/`.
- Keep project notes and generated documentation in this sibling
  `affective_project_notes/` folder, outside the kit.
- Do not add a package dependency unless it is needed beyond the standard
  library and numpy.

The prompt copy is in [MASTER_PROMPT.md](MASTER_PROMPT.md). No engine code has
been changed. New test files and a README at the kit root are still on the
teacher questions list.

## Exact contract

The authoritative source is the kit's `README.md` and `harness/contract.py`.
The harness imports `engine.engine.Engine`, calls `reset()`, then calls
`process(text, audio_path=None, image_path=None)`.

| Key | Required? | Contract |
|---|---:|---|
| `valence` | Yes | Numeric value in [-1, 1], negative to positive. |
| `activity` | Yes | Numeric value in [-1, 1], deactivated to activated. `arousal` is accepted as an alias by the harness. |
| `confidence` | Yes | Numeric value in [0, 1], representing trust in the estimate. |
| `label` | Yes | String, such as `neutral`, `anger`, `fear`, `frustration`, `sadness`, `joy`, or `calm`. |
| `action` | Yes | One of the six action names below. |
| `reply` | Yes | String shown to the customer. |
| `dominance` | No | Optional numeric value in [-1, 1]; returning it enables the 3D map. |
| `flags` | No | Optional list of strings describing useful cues or status. |
| `details` | No | Optional dictionary shown in the session log. |

`harness.contract.normalize()` copies results, accepts `arousal` only when
`activity` is absent, clips numeric values for display while reporting invalid
or out-of-range values, and validates the action against the six-name tuple.
The engine should return valid values itself rather than rely on harness
normalization.

The exact action vocabulary is:

- `ANSWER`
- `ANSWER_EMPATHIC`
- `ASK_CLARIFICATION`
- `OFFER_HUMAN`
- `ESCALATE`
- `CLOSE_POSITIVE`

The kit lists the actions but does not define their individual meanings. A
provisional interpretation is that `OFFER_HUMAN` offers a human handoff, while
`ESCALATE` routes an urgent, threatening, legal, or persistently severe issue
for higher-priority handling. This distinction needs teacher confirmation; do
not present it as kit-defined semantics.

## Harness and log behavior

- `harness.loader.load_engine()` imports `engine.engine.Engine`; preserve that
  path and class name.
- `harness.session.Session.send()` passes both optional media paths, measures
  latency, normalizes the result, appends the input and output to history, and
  logs any raised exception. The engine is still expected not to raise.
- `harness.gui.App` displays the 2D map at x=valence, y=activity; it enables
  the 3D view only after an output contains dominance. It displays the latest
  label, action, flags, confidence, conversation, reply, and expandable log.
- `harness.logger.format_entry()` writes input, map values, confidence, label,
  action, flags, latency, reply, and `details` as a Python string
  representation. Keep `details` compact, readable, and composed of
  serializable plain values.
- `harness.scenarios` reads JSON scenarios, resolves media paths, and runs each
  message in sequence through the same session.
- The GUI and scenario runner write plain-text session logs in `logs/`.

## Starter engine and baseline

The starter is a single `engine/engine.py`. It tokenizes with a basic ASCII
regular expression, sums a tiny positive/negative word dictionary, clips
valence, assigns activity 0.3 only when an exclamation mark appears, and
returns confidence 0.3. It does not handle negation, language, sarcasm, or
conversation state in its decisions. `reset()` only clears a list. Every
message gets `ANSWER` and the same generic reply. Details contain only the
word count.

Baseline artifacts are in `evaluation/baseline_logs/`; an unchanged copy of
the starter engine is in `evaluation/baselines/starter_engine/`. The contract
test passed, and all eight scenario runs exited successfully. The starter
passes the contract but misses most scenario behavior, as shown below.

| Run | Result |
|---|---|
| Original contract test | PASS |
| Mandatory scenarios M1-M4 | 4/4 runner exits successful |
| Practice scenarios P1-P4 | 4/4 runner exits successful |
| Contract violations seen in baseline | None |

`run_scenario.py` creates session logs under `logs/`; the logs created for the
baseline run were copied to `evaluation/baseline_logs/` and removed from the
kit's runtime log folder. The pre-existing `logs/README.txt` remains untouched.

## Scenario observations

The expected-behavior column quotes the scenario file. Per-turn actions below
are inferred recommendations, not additional requirements encoded by the
scenario format. Alternatives are noted where the scenario is underspecified.
The starter result is the actual baseline output; every starter action was
`ANSWER`.

### Mandatory scenarios

**M1 - Calm customer with simple questions.** Expected behavior: "Low activity,
neutral to positive valence, simple answers; the last message should close the
conversation positively."

| Turn | Message | Inferred action | Starter result and gap |
|---:|---|---|---|
| 1 | Hi, how long does delivery usually take? | `ANSWER` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; behavior matches broadly. |
| 2 | Thanks. And can I change my delivery address? | `ANSWER` | V=+0.60, A=0.00, confidence=0.30, joy, `ANSWER`; reply remains generic and does not answer the question. |
| 3 | Perfect, that is all I needed. Thank you! | `CLOSE_POSITIVE` | V=+1.00, A=+0.30, confidence=0.30, joy, `ANSWER`; misses the requested positive close. |

**M2 - Frustration that grows over the conversation.** Expected behavior:
"Valence falls and activity rises message by message. The state over time must
show it. The system should offer a human or escalate before the end."

| Turn | Message | Inferred action | Starter result and gap |
|---:|---|---|---|
| 1 | Hi, my order 4821 has not arrived yet. | `ANSWER_EMPATHIC` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; no delay recognition or state. |
| 2 | It was supposed to be here three days ago. | `ANSWER_EMPATHIC` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; no worsening trend. |
| 3 | Nobody has answered my two emails. This is really frustrating. | `ANSWER_EMPATHIC` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; misses clear frustration and repeated contact. |
| 4 | This is unacceptable! I want my money back!! | `OFFER_HUMAN` | V=-0.80, A=+0.30, confidence=0.30, frustration, `ANSWER`; recognizes one negative token only and ignores the request / punctuation intensity. |
| 5 | I am furious. I will contact a lawyer if this is not solved today. | `ESCALATE` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; misses anger and the legal cue. |

**M3 - Explicit requests that must not be missed.** Expected behavior: "Rules
for explicit signals (asking for a person, legal threat) must win over the
emotion estimate."

| Turn | Message | Inferred action | Starter result and gap |
|---:|---|---|---|
| 1 | Can you tell me how to return a product? | `ANSWER` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; reply does not address the return question. |
| 2 | I do not want to talk to a bot, please connect me with a human agent. | `OFFER_HUMAN` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; misses explicit handoff request. |
| 3 | Thank you, but if this is not fixed I will go to the consumer protection authority. | `ESCALATE` | V=+0.60, A=0.00, confidence=0.30, joy, `ANSWER`; positive tokens overwhelm the threat context. |

**M4 - Ambiguous, sarcastic and non-English messages.** Expected behavior:
"The system should show lower confidence on ambiguous input, ask for
clarification when it does not know, notice sarcasm, and handle the Portuguese
messages."

| Turn | Message | Inferred action | Starter result and gap |
|---:|---|---|---|
| 1 | ok | `ASK_CLARIFICATION` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; no short-message uncertainty. |
| 2 | whatever, do what you want | `ASK_CLARIFICATION` or `ANSWER_EMPATHIC` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; misses ambiguity and possible frustration. |
| 3 | Great, another delay. Really great. | `ANSWER_EMPATHIC` | V=+1.00, A=0.00, confidence=0.30, joy, `ANSWER`; sarcasm is read as strongly positive. |
| 4 | It is not bad, thanks. | `ANSWER` | V=+0.10, A=0.00, confidence=0.30, neutral, `ANSWER`; output happens to be mild, but negation is not modeled. |
| 5 | Obrigado, ficou tudo resolvido. | `CLOSE_POSITIVE` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; no Portuguese handling or positive close. |

### Practice scenarios

**P1 - Neutral refund request.** Expected behavior: "Neutral valence, answer
normally."

| Turn | Message | Inferred action | Starter result and gap |
|---:|---|---|---|
| 1 | Hello, I would like to know how refunds work. | `ANSWER` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; generic reply does not answer. |
| 2 | I bought a keyboard last week, can I return it? | `ANSWER` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; no product/return intent extraction. |
| 3 | Understood, thanks. | `ANSWER` or `CLOSE_POSITIVE` | V=+0.60, A=0.00, confidence=0.30, joy, `ANSWER`; no contextual completion or tailored reply. |

**P2 - Disappointed and tired customer.** Expected behavior: "Negative valence
with LOW activity (sadness, not anger); empathic answers."

| Turn | Message | Inferred action | Starter result and gap |
|---:|---|---|---|
| 1 | I am really disappointed with my last order. | `ANSWER_EMPATHIC` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; misses disappointment. |
| 2 | I am tired of waiting for the replacement. | `ANSWER_EMPATHIC` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; misses low-activity negative affect. |
| 3 | I do not think it will ever arrive. | `ANSWER_EMPATHIC` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; no negation, delay cue, or empathy. |

**P3 - Anxious about a payment.** Expected behavior: "Negative valence, higher
activity, low dominance (fear rather than anger)."

| Turn | Message | Inferred action | Starter result and gap |
|---:|---|---|---|
| 1 | I am worried my payment failed. | `ANSWER_EMPATHIC` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; misses worry and billing intent. |
| 2 | I am scared the money is gone and the order disappeared! | `ANSWER_EMPATHIC` | V=0.00, A=+0.30, confidence=0.30, neutral, `ANSWER`; punctuation alone raises activity; fear and low dominance are absent. |
| 3 | Please help me, I do not know what to do. | `ANSWER_EMPATHIC` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; misses helplessness and reassurance need. |

**P4 - Negation and praise.** Expected behavior: "\"not bad\" is mildly
positive, \"not happy at all\" is negative."

| Turn | Message | Inferred action | Starter result and gap |
|---:|---|---|---|
| 1 | The delivery was not bad. | `ANSWER` | V=-0.50, A=0.00, confidence=0.30, frustration, `ANSWER`; negation reverses the intended polarity. |
| 2 | I am not happy at all with the packaging. | `ANSWER_EMPATHIC` | V=0.00, A=0.00, confidence=0.30, neutral, `ANSWER`; misses negated dissatisfaction. |
| 3 | Still, the support team was great, thank you. | `ANSWER` or `CLOSE_POSITIVE` | V=+1.00, A=0.00, confidence=0.30, joy, `ANSWER`; positive sum saturates and does not use conversation context. |

## Assets and baseline environment

`assets/audio/README.txt` describes the WAVs as synthetic, voice-like teaching
signals. All six WAV files were verified as mono, 16 kHz, 16-bit PCM, 32,000
frames (2.000 seconds). The filenames distinguish calm/agitated, clean/noisy,
and high/low pitch. The README warns that a fixed baseline mistakes the high
speaker pitch for higher arousal and does not reduce noisy-file confidence.
There are no face assets.

The Phase 0 contract test and eight scenario runs used the default Python
3.14.6. The Windows launcher also has Python 3.12.10 and 3.15 available;
3.12.10 is the oldest installed and was used for Phase 1 tests. The teacher's
version is still unknown. Requirements remain standard library only (numpy is
allowed).

## Proposed architecture and initial thresholds

Preserve `engine.engine.Engine` as the entry point expected by the harness.
Keep orchestration in `engine/engine.py`; split concepts into small modules
under `engine/`. This honors the kit boundary while avoiding one oversized
module.

```text
engine/
  __init__.py                 # preserve import compatibility if exported
  engine.py                   # Engine.reset/process pipeline and safety net
  config.py                   # shared thresholds, weights, feature toggles
  perception/
    preprocess.py             # normalization, tokenization, clauses
    language.py               # supported-language and script cues
    lexicon.py                # load lexicons and phrases
    rules.py                  # negation, modifiers, punctuation, domain cues
    sarcasm.py                # transparent heuristic
    intents.py                # support intents and entities
    text_estimator.py         # V/A/D/confidence estimate
    lexicons/                 # bundled English and Portuguese data
  affect/
    space.py                  # SAM conversion, prototypes, labels, clamping
    fusion.py                 # late fusion; text-only by default
  state/
    tracker.py                # confidence-weighted state and history signals
  policy/
    policy.py                 # ordered, named decision rules
    replies.py                # short, deterministic and intent-aware replies
  voice/                      # optional; start only after Phase 6 passes
  evaluation/                 # scripts and evaluation data/code
  README.md                   # student run/test instructions; not kit-root README
tests/
  test_contract.py            # existing kit file, unchanged
  test_kit_unchanged.py       # new checksum test
  test_perception.py          # new focused behavior tests
affective_project_notes/
  MASTER_PROMPT.md
  KIT_NOTES.md
  kit_checksums.txt
  evaluation/
    baseline_logs/
    baselines/starter_engine/
```

The scenarios require Portuguese messages, so English and Portuguese are the
proposed supported languages; confirm this scope before building lexicons.
Voice is optional and should wait until the text engine passes integration
tests. Skip face unless all mandatory work is complete and there is explicit
consent and approval.

The following are proposed starting values, not tuned values. Keep them in
`engine/config.py`, document the trade-off beside each, and tune only on dev
data after Phase 1. The kit scenarios must not be embedded in the engine.

| Setting | Initial proposal | Trade-off / status |
|---|---:|---|
| `NEGATION_FACTOR` | -0.6 | Stronger shift can overstate negation; weaker shift misses reversed sentiment. |
| Negated activity multiplier | 0.8 | Lower is calmer; higher retains more activation from the negated cue. |
| Intensifiers | very 1.3, really 1.25, so 1.3, extremely 1.6, absolutely 1.5, totally 1.4 | Larger multipliers amplify emphasis but can saturate estimates. |
| Downtoners | a bit 0.6, slightly 0.5, kind of 0.7, somewhat 0.7 | Smaller multipliers suppress intensity more, but may under-read understated complaints. |
| Contrast weights | earlier clause 0.3, later clause 0.7 | More later-clause weight follows the prompt's contrast rule; it can underweight positive context. |
| Sarcasm threshold | 0.6 (provisional) | Lower catches more sarcasm but risks false positives; higher misses subtle cases. |
| Neutral prototype radius | 0.18 (provisional) | Larger radius labels more messages neutral; smaller radius creates more discrete labels. |
| `STATE_ALPHA` | 0.5 | Higher reacts quickly but is noisy; lower is stable but lags. |
| `CLARIFY_CONF` | 0.35 (provisional) | Higher asks more clarifying questions; lower may answer on weak evidence. |
| `MAX_CLARIFY` | 2 | Lower caps loops sooner; higher can frustrate customers. |
| `ESC_V`, `ESC_A`, `ESC_TURNS` | -0.65, 0.55, 2 (provisional) | Stricter escalation thresholds reduce false escalations but risk missing severe cases. |
| `HUMAN_V`, `HUMAN_STREAK` | -0.45, 3 (provisional) | Earlier human offers cost more handoffs; later offers can leave persistent issues unresolved. |
| Empathy entry/exit | enter at state V <= -0.25; exit above -0.15 (provisional) | A wider gap adds hysteresis and reduces tone flipping, but keeps empathy longer. |
| `CLOSE_V` | 0.35 (provisional) | Higher requires stronger positive evidence; lower can close prematurely. |

The contract does not prescribe an uncertain label. At the Phase 0 checkpoint,
the student approved the proposed architecture and chose to keep the nearest
prototype label while adding a `low_confidence` flag.

## Relative work plan

The deadline and several Section 0 fill-ins remain unknown, so this is a
relative plan rather than a dated schedule. Keep at least two buffer days
before delivery for ratings, report/video revisions, and clean-copy fixes.

| Work day | Focus |
|---|---|
| D0 | Approve the architecture and resolve teacher questions; complete the missing Section 0 details. |
| D1 | Start evaluation dataset and rating kit; recruit raters and collect independent SAM ratings before tuning. |
| D2-D3 | Implement and test text preprocessing, language support, lexicon, rules, intent, sarcasm, and confidence. |
| D4 | Add affective-space labels, dominance, and map-related tests. |
| D5 | Add state tracking, named policy rules, and deterministic replies. |
| D6 | Robustness probes, integration, scenario regression tests, clean-copy check, student run instructions. |
| D7 | Evaluation, error analysis, ethics, report scaffold, topic notes and Q&A practice. Add voice only if the text engine is complete and time remains. |
| Buffer 1 | Resolve test/evaluation failures and collect any late ratings; do not add optional features. |
| Buffer 2 | Record/revise video, run final checks and package before the actual deadline. |
