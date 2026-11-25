# Topic 3: State, policy and replies (Phase 4)

## How it works

The text estimator describes one message; a support conversation needs to
remember whether the customer is becoming calmer, repeating a problem, or has
already been offered a person. `engine/state/tracker.py` maintains that
bounded state, and `engine/policy/policy.py` selects an action from an ordered
list of named rules. `engine/policy/replies.py` then creates a deterministic
reply. The public integration is `Engine.process()` in
`engine/engine.py`.

### State over turns

For valence, activity, and dominance, the tracker applies a confidence-weighted
exponential moving average:

`state_t = state_(t-1) + STATE_ALPHA * confidence_t * (message_t - state_(t-1))`

The first message initializes the state. With `STATE_ALPHA = 0.50`, and a
confidence of 0.50, the next state moves 25% of the way from its previous
value toward the new message value. A higher alpha reacts faster but follows
more message-level noise; a lower alpha is steadier but lags. Confidence
reduces the influence of a less certain estimate.

The tracker keeps at most eight recent turns. Each record includes message
V/A/D, confidence, label, intent, chosen action, and flags. Derived signals
include:

- `trend`: least-squares slope of message valence over the latest four turns;
- `neg_streak`: consecutive message valences below `NEG_TURN_V`;
- `peak_negative`: the lowest message valence in retained history;
- `clar_streak`: consecutive preceding `ASK_CLARIFICATION` actions;
- `severe_streak`: consecutive smoothed states meeting both escalation
  thresholds;
- `repeated_issue`: the same non-unknown intent has occurred at least twice
  with negative valence in retained history;
- `human_offered_turn`, `human_declined`, and `escalated`: handoff and
  escalation memory; and
- `resolved`: a resolution cue or a positive closing intent has appeared.

Empathy uses hysteresis: it becomes active for sufficiently negative state or
message affect (or negative high activity), then remains active until smoothed
valence rises above `EMPATHY_EXIT_V`. This prevents a one-turn improvement from
immediately switching the tone back and forth. `reset()` clears all retained
conversation state; a regression test compares its next result with a fresh
engine.

### Ordered decisions

`RULES` in `policy.py` is checked from first to last; the first matching rule
wins. This makes safety and explicit requests take priority over conversational
convenience:

| Rule | Purpose |
|---|---|
| `R0_SAFETY` | A safety flag selects `ESCALATE` with immediate-help guidance. |
| `R1_HUMAN_REQUEST` | A first explicit human request selects `OFFER_HUMAN`; a prior offer, urgent cue, abuse cue, or severe state can select `ESCALATE`. |
| `R2_ESCALATE` | Legal/threat or abuse cues, persistent severe activation, or a long worsening negative streak select `ESCALATE`. |
| `R3_CLOSE` | A positive closing intent selects `CLOSE_POSITIVE`, unless sarcasm is flagged or a handoff has been declined without resolution. |
| `R4_UNCERTAIN` | Unsupported language, low confidence, or unresolved short/ambiguous text selects `ASK_CLARIFICATION`; after the configured clarification limit it offers a person. |
| `R5_OFFER_HUMAN` | Persistent/repeated negative issues offer a person unless one was offered recently or declined; then the reply stays empathic without repeating the offer. |
| `R6_EMPATHY` | Negative state or message affect selects `ANSWER_EMPATHIC`. |
| `R7_DEFAULT` | The fallback is `ANSWER`. |

Each decision returns its rule name and a human-readable reason in `details`.
Reasons include the measured V/A/confidence or streak values when relevant.
The thresholds live in `engine/config.py`; for example, lowering `ESC_V` or
raising `ESC_A` makes escalation less likely, reducing false urgent handoffs
but increasing the chance of missing severe distress. The policy deliberately
uses `OFFER_HUMAN` for support handoff and reserves `ESCALATE` for safety,
urgent, legal/abuse, or sustained-severity conditions.

### Replies

`render_reply()` in `policy/replies.py` chooses one of two templates by
conversation turn, so the same input sequence always produces the same
wording. English action patterns are combined with intent-specific next-step
text; Portuguese has action patterns and intent-specific steps. Empathy names
the detected issue and includes a practical next step. A handoff explicitly
discloses that the assistant is automated. Replies do not claim access to
live order data or promise a refund. Unsupported-language replies ask the
customer to use English or Portuguese and offer a human handoff in both
languages.

### Phase 5 hardening

`Engine.process()` catches unexpected internal failures at the public
boundary, clears the damaged conversation state, and returns a
contract-valid bilingual clarification with an `internal_error` flag. It
exposes only the exception type, not the exception message; tests set
`ENGINE_STRICT=1` to re-raise failures and keep regressions visible. Replies
now include intent-specific next steps in both languages and vary those steps
deterministically by turn. Account and payment wording avoids requesting
sensitive data, and replies do not imply that the assistant checked an order
or completed a transaction.

### Worked example

The new sentence “The modem arrived damaged, and I feel really disappointed.”
is not in `engine/evaluation/data/messages.csv`. It produced V=-0.764,
A=-0.136, D=-0.246, confidence=0.636, label `sadness`, and action
`ANSWER_EMPATHIC` under `R6_EMPATHY`. On the first turn, the EMA initializes
state to the message values; `neg_streak` is 1, trend is 0.0, and empathy is
active. The reason reports state and message valence as -0.76. The reply
apologizes for the problem with the item and offers to review its options.
These are a single new unit-test-style example, not evaluation metrics.

### Phase 5 worked example and validation

The fresh sentence “The charging port on my camera is damaged, and I am really
disappointed.” produced V=-0.764, A=-0.136, D=-0.246, confidence=0.661,
label `sadness`, intent `DAMAGED_OR_DEFECTIVE`, and action `ANSWER_EMPATHIC`
under `R6_EMPATHY`. It is a unit-test-style demonstration, not an evaluation
message.

The 40-message rehearsal covers eight new conversations, reaches all six
actions, and passes 40/40. Fifteen additional English/Portuguese
generalization cases pass 15/15. The full suite passes 87 tests; the eight
mandatory/practice scenarios also pass from a clean copy. These checks do not
reveal or score the 88 evaluation messages.

### Tests

`tests/test_state.py` checks the confidence-weighted EMA, trend, streak,
repeated-issue detection, offer/decline/escalation memory, empathy hysteresis,
and reset. `tests/test_policy.py` covers all six actions, the clarification
cap, the human-offer cooldown and decline, deterministic reply variants,
Portuguese and unsupported-language replies, and the rule that “thanks for
nothing” does not close positively. It also checks specific bilingual intent
steps and consecutive reply variation. `tests/test_scenarios.py` checks the
scenario action expectations without changing the scenario files. The
40-message rehearsal in `tests/test_rehearsal.py` uses new messages, checks
action reachability and a 90% minimum pass rate, and avoids `messages.csv`.

## How to change it

- To make affect state react faster or more slowly, change `STATE_ALPHA` in
  `engine/config.py`; the EMA test derives its expected result from this
  setting.
- To alter repeated complaints, worsening trajectories, or urgent handoff,
  review `NEG_TURN_V`, `REPEATED_ISSUE_MIN`, `STATE_TREND_WINDOW`,
  `TREND_WORSENING_THRESHOLD`, `ESC_V`, `ESC_A`, `ESC_TURNS`, and
  `ESC_NEG_STREAK` in `engine/config.py`; tightening escalation can reduce
  false alarms but miss distress, while loosening it can over-escalate. Keep
  safety cues ahead of ordinary conversational rules.
- To adjust empathy entry and recovery, review `EMPATHY_V`, `EMPATHY_MSG_V`,
  `EMPATHY_A`, `EMPATHY_NEGATIVE_V`, and `EMPATHY_EXIT_V` in
  `engine/config.py`; preserve the hysteresis test when changing these values.
- To change the clarification loop or repeat-offer behavior, edit
  `MAX_CLARIFY`, `HUMAN_OFFER_COOLDOWN_TURNS`, or the corresponding named
  rule in `engine/policy/policy.py`; retain the cap and decline regression
  tests. For error handling, run with `ENGINE_STRICT=1` in tests so an
  unexpected exception fails visibly instead of using the public fallback.
- To change a reply, edit the corresponding action pattern or intent step in
  `engine/policy/replies.py`; preserve deterministic turn-based selection,
  the automated-assistant disclosure, and the no-unverified-promises rule.

## Likely teacher questions

1. **Why smooth state instead of using only the latest message?** The
   confidence-weighted EMA in `StateTracker._smooth()` retains recent context
   while letting low-confidence messages move it less.
2. **Why are there two kinds of human action?** `OFFER_HUMAN` is a support
   handoff; `ESCALATE` is reserved for safety, urgency, legal/abuse cues, or
   sustained severe state.
3. **Why does the engine not close on every thank-you?** `R3_CLOSE` also
   checks positive valence and rejects `possible_sarcasm`; “thanks for
   nothing” is a regression case.
4. **What prevents endless clarification, and how are internal errors handled?**
   `R4_UNCERTAIN` offers a person at `MAX_CLARIFY`; the public engine boundary
   returns a contract-valid clarification on unexpected errors, while
   `ENGINE_STRICT=1` makes tests re-raise the error.
5. **How is empathy prevented from switching abruptly?** The tracker uses
   separate entry and exit conditions, with `EMPATHY_EXIT_V` as the recovery
   threshold.

## Live-change drills

1. In `engine/config.py`, change `STATE_ALPHA` from `0.50` to `0.70`, then run
   `py -3.12 -m unittest discover -s tests -p 'test_state.py'`. The EMA
   assertions should still pass, and the computed state should move farther
   toward the new message. Restore `0.50` after the drill.
2. Change `HUMAN_OFFER_COOLDOWN_TURNS` from `2` to `0`, then run
   `py -3.12 -m unittest discover -s tests -p 'test_policy.py'`. The
   `test_human_offer_is_not_repeated_immediately` regression should fail
   because the persistent-issue example can offer a person again on the next
   turn. Restore `2`; the failure demonstrates why cooldown behavior is
   tested.
3. Edit one intent-specific English or Portuguese step in
   `engine/policy/replies.py`, then run `py -3.12 -m unittest discover -s tests
   -p 'test_policy.py'` to verify the reply remains specific, safe, and
   deterministic.
