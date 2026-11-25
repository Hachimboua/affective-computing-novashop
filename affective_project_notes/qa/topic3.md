# Topic 3 — Decision, state over time and robustness: likely questions

1. **How do you keep a state over the conversation?**
   `engine/state/tracker.py`, `_smooth`: `s ← s + α·c·(x − s)` per dimension, with α = 0.5 (`STATE_ALPHA`) and c the message confidence. Uncertain messages move the state less.
   *Follow-up: trade-off of α?* High α reacts fast but is noisy; low α is stable but lags behind a customer who is getting angry.

2. **What else does the state track?**
   Last 8 turns; trend (slope of the last 4 valences); negative streak; severe streak; clarification streak; whether a person was offered or declined; repeated issue; resolution; empathy mode.

3. **How is the action chosen?**
   `engine/policy/policy.py`: ordered rules R0–R7; the first that applies wins. The rule name and a reason with the real numbers go to `details.rule` / `details.reason` in the log.

4. **Why does the order matter?**
   Explicit signals must win over the emotion estimate (scenario M3): safety, human request and legal threats are checked before closing, clarification and empathy.

5. **OFFER_HUMAN vs ESCALATE?**
   Provisional definition (to confirm with the teacher): offering a transfer the customer can accept, versus an urgent priority handover (legal/authority threat, abuse, safety, a severe state for 2 turns, or a human request when already very angry).

6. **When do you ask for clarification?**
   R4: confidence < 0.35 (`CLARIFY_CONF`), a short/ambiguous message with no intent, or an unsupported language. After 2 clarifications in a row (`MAX_CLARIFY`) it offers a person instead, to avoid loops.

7. **What is hysteresis and where do you use it?**
   Different thresholds to enter and leave a mode: empathy starts at state V ≤ −0.25 and only stops above −0.15 (`EMPATHY_EXIT_V`), so the tone does not flip back and forth.

8. **What happens when the system does not know?**
   Low confidence → clarification; unsupported language → bilingual request to write in English or Portuguese with an offer of a person; internal error → a valid fallback result with flag `internal_error`.

9. **How do you handle sarcasm in the policy?**
   A message with `possible_sarcasm` can never close the conversation; its inverted valence usually leads to empathy.

10. **Which mistakes are worse?**
    Missing a needed escalation is worse than an unnecessary offer of a person; the evaluation cost table reflects that (`ACTION_COST` and `MISSED_ESCALATION_COST` in `evaluate.py`).

11. **How do the replies avoid contradictions?**
    `replies.py` picks templates by action and intent; handoff/escalation replies never ask for more detail; closing text only appears with CLOSE_POSITIVE; emergency services only with the safety flag; follow-ups without a topic reuse the earlier topic (`context_intent`).

12. **How did you test robustness?**
    `tests/test_robustness.py` (empty, `None`, numbers, bytes, 20,000 characters, emojis, HTML, other scripts, missing audio), a 40-message rehearsal (`tests/test_rehearsal.py`) and reply-consistency tests (`tests/test_replies.py`).

## Live-change drills (verified)

1. **Offer a person sooner.** `HUMAN_STREAK = 2`. Conversation: "My tablet order is late again, which is annoying." → "I'm disappointed nobody has replied yet." → "Honestly this is frustrating." The offer moves from turn 3 to turn 2.
2. **Ask more clarifying questions.** `CLARIFY_CONF = 0.60`. "Not sure about this one." changes from ANSWER (confidence 0.47) to ASK_CLARIFICATION.
3. **Faster state.** `STATE_ALPHA = 0.9`. Conversation: "My tablet order is late again." → "Still no update and nobody replies to me." → "This is really annoying now." → "I'm so fed up with this shop." The final state valence (`details.state.valence`) moves from about −0.49 (α 0.5) to about −0.34, because the state now follows the latest message more closely, and the 2nd and 4th messages score neutral (their complaint phrases are not in the lexicon: a good example for the limits question). Bonus: `MAX_CLARIFY = 1` makes "eh" → "uhh" offer a person at the second message instead of the third.
