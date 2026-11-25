# Whole system: questions any examiner can ask you

1. **Walk me through what happens when I type a message.**
   `Engine.process` → `estimate_text` (pre-process, language, intent, lexicon + rules, sarcasm, confidence, label) → if audio: `estimate_voice` and `fuse_text_voice` → `StateTracker.begin_turn` (smoothed state, streaks, trend) → `choose_action` (first matching rule R0–R7) → `render_reply` (template by action, intent, language) → result dict with `details` for the log.

2. **Where is every threshold?**
   `engine/config.py`, each with a comment saying what raising or lowering it does.

3. **Which part would you improve first?**
   [[your choice, e.g. the lexicon coverage of complaint phrases such as "nobody replies", or sarcasm without known words]], because the error analysis shows [[TODO]].

4. **What does your engine do with "ok"?**
   Short, no intent, low confidence → asks for clarification; after an empathic reply, "ok" is read as acknowledgement instead.

5. **What if the customer writes in German?**
   German stop-words → `unsupported_language`, confidence ≤ 0.20, bilingual reply asking for English or Portuguese with an offer of a person.

6. **What if the customer threatens legal action but sounds polite?**
   Explicit signal → R2 escalates regardless of the emotion estimate (scenario M3, "Thank you, but … consumer protection authority").

7. **How do you know your engine is better than the starter?**
   The evaluation compares both on the same rated messages. [[TODO: numbers]]

8. **How does the system behave over a long angry conversation?**
   The state moves towards negative and activated; empathy first; a person is offered when the state stays ≤ −0.45 for 3 negative turns or worsens; escalation for a severe state over 2 turns or 4 negative turns with a worsening trend.

9. **What would you need to deploy this for real?**
   Real data and ratings, many more languages and phrases, privacy measures (consent, retention, DPIA), transparency notices, human oversight, monitoring for bias, and confirmation of the AI Act obligations.

10. **Which design decision are you least sure about?**
    [[your answer, e.g. the provisional OFFER_HUMAN vs ESCALATE definition, or the hand-chosen tier values]].

11. **What did you write yourself and what did the AI write?**
    [[Answer honestly from your AI log: what you asked, what you changed, how you verified. Be ready to change any part live.]]

12. **Show me how to change X now.**
    Use the drills in `qa/topic1.md` … `topic5.md`; always say what you expect to happen before running it.
