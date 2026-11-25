# Topic 1 — Text perception: likely questions

> Answers are short on purpose: say them in your own words and always point to
> the file. "Recited" answers with no link to our system score at most 2/4.

1. **Is your method knowledge-based or statistics-based? Why?**
   Knowledge-based: a lexicon (`engine/perception/lexicons/*.tsv`) plus rules (`rules.py`). We had no labelled training data of our own, we must run offline with the standard library, and we must explain and change each decision live. Cost: limited vocabulary and hand-made rules.
   *Follow-up: what would a statistics-based version need?* Labelled messages (e.g. our SAM-rated set, much larger), features such as bag-of-words, and a model such as ridge regression for V and A; it would learn weights instead of tiers but would be harder to explain.

2. **How is valence computed for a sentence?**
   Each matched word or phrase contributes the V/A/D of its tier (`config.TIER_VAD`), modified by rules (negation, intensifiers, caps, contrast weight). `text_estimator.py` takes a weighted mean of the contributions and squashes it with tanh into [-1, 1].
   *Follow-up: why tanh?* It keeps values inside the range and makes many weak cues saturate smoothly instead of exceeding 1.

3. **How do you handle negation?**
   `rules.py`: a negator ("not", "never", "não"…) affects up to 3 following tokens (`NEGATION_SCOPE`) and multiplies valence by −0.6 (`NEGATION_FACTOR`), a *shift*, not a full flip, following SO-CAL (Taboada et al., 2011). So "not bad" is mildly positive and "not good" mildly negative.
   *Follow-up: why not −1?* "not good" is not as negative as "bad"; a full flip overstates it.

4. **What are the tiers?**
   Twelve groups (ANGER_STRONG, ANGER, FRUSTRATION, PROBLEM_MILD, PROBLEM, FEAR, SADNESS, FATIGUE, NEUTRAL, CONTENT, POSITIVE, JOY), each with one V/A/D point in `config.TIER_VAD`. Each lexicon entry names its tier. One decision per word, easy to review, and a whole group can be changed in one line.
   *Follow-up: why did you move to tiers?* The first per-word values were inconsistent (sad words with high activity, *slow* more negative than *furious*).

5. **How do you detect sarcasm?**
   `sarcasm.py`: known idioms ("thanks for nothing", "obrigado por nada"), incongruity (positive word next to a negative event like "broke again"), scare quotes, and a negative conversation context. Score ≥ 0.6 (`SARCASM_THRESHOLD`) inverts positive contributions and lowers confidence; a sarcastic message can never close the conversation.
   *Follow-up: what does it miss?* Sarcasm without negative event words or known idioms, e.g. "Wow, such fast shipping, only took a month."

6. **How is confidence computed?**
   `_confidence` in `text_estimator.py`: grows with the number of affective cues (saturating), drops with conflicting cues, short messages, unknown words, sarcasm and mixed language; capped at 0.20 for unsupported languages; a well-formed neutral sentence gets 0.55 × language confidence. Clamped to [0.05, 0.95].
   *Follow-up: why not 0 for neutral sentences?* Absence of emotion words in a clear sentence is evidence of neutrality; otherwise every plain question would trigger clarification.

7. **How do you know the language?**
   `language.py`: Unicode script (non-Latin → unsupported), English and Portuguese stop-words, distinctive lexicon hits, and stop-words of other Latin languages. 1–2-word messages are treated as short, not foreign.

8. **How do intensifiers, caps and punctuation work?**
   Intensifiers multiply the next affective word (e.g. "very" 1.3, "extremely" 1.6; downtoners < 1). All-caps words and "!" raise activity; repeated "?" too.

9. **How do contrastive sentences work ("Thanks, but it's broken")?**
   Clauses are split at contrastive words; the later clause weighs 0.7 (`CONTRAST_LATER_WEIGHT`), the earlier 0.3; opposite signs add the flag `mixed_emotion`.

10. **What is the intent used for?**
    `intents.py` finds the support topic (delivery delay, refund, payment…) by keywords in EN/PT; it chooses the reply's next step and helps confidence and policy (e.g. closing intent).

11. **How would you add a new language?**
    Stop-words in `language.py`, negators and intensifiers in `config.py`, a `xx.tsv` lexicon with tiers, intent cues in `intents.py`, reply templates in `replies.py`, and tests with new sentences.

12. **What are the limits?**
    Vocabulary-bound (unknown words carry no emotion, e.g. "nobody replies" phrases not in the lexicon), partial sarcasm, two languages, hand-chosen tiers.

## Live-change drills (verified)

1. **Make negation stronger.** In `engine/config.py` set `NEGATION_FACTOR = -1.0`. Run:
   `python -c "from engine.engine import Engine; print(Engine().process('The new charger is not good.')['valence'])"`
   Expected: valence goes from about −0.33 to about −0.52. Set it back to −0.60.
2. **Add a word.** Append the line `scandalous<TAB>ANGER<TAB><TAB><TAB>` to `engine/perception/lexicons/en.tsv` (or add it through the review sheet and the sync tool). Restart and send "This is scandalous." Expected: from neutral (V 0.00, ANSWER) to about V −0.67, label anger, ANSWER_EMPATHIC.
3. **Add an intensifier.** In `config.INTENSIFIERS["en"]` add `"insanely": 1.5`. "The packaging was insanely bad." goes from about −0.52 (same as "bad") to about −0.70.
