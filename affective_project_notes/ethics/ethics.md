# Ethics and limits — draft for the report

> **AI draft.** Read it, check every `[[CHECK]]` against the official text, and
> rewrite it in your own words before it goes into the report. Legal context
> here is a summary for a course project, not legal advice.

## 1. What the system processes and stores (data inventory)

| Data | Where it comes from | Where it is stored | How long | Who can see it |
|---|---|---|---|---|
| Customer message text | Typed in the interface or read from a scenario file | In memory during the conversation (`engine/state/tracker.py` keeps the last 8 turns); `reset()` clears it | Until the conversation ends | The engine only |
| Session log | Written by the kit harness (`harness/logger.py`), not by our engine | `logs/session_<date>_<time>.txt` | Until deleted by the user; only the demo log is delivered | Anyone with the project folder |
| Optional audio file | Attached by the user | Read once from disk; only summary features are kept in `details` | Not stored by the engine | The engine only |
| SAM ratings | Volunteers using `engine/evaluation/rate.py` | `engine/evaluation/ratings/<anonymous id>.csv` | Until the deletion date in the consent form `[[CONFIRM]]` | The student and the teacher |
| Evaluation messages | 28 kit scenario messages and 60 fictional messages | `engine/evaluation/data/messages.csv` | Part of the project | Anyone with the project |

**Minimisation choices we made**
- The engine writes nothing to disk. All logging is done by the kit harness.
- No real customer data is used. Every evaluation message is fictional (no real names, emails or order numbers).
- Raters are identified only by an anonymous id that they choose; the rating tool refuses ids that are not simple letters and digits.
- Audio is reduced to a handful of numeric features (energy, pitch variability, voicing ratio, SNR); the raw signal is not kept.
- The face channel was not built, so no images of people are processed.

## 2. GDPR (Regulation (EU) 2016/679)

- **Principles (Art. 5):** purpose limitation (affect is used only to choose a support action), data minimisation (see above), storage limitation (logs and ratings have a deletion date), transparency (the assistant says it is automated).
- **Lawful basis and consent:** volunteers give informed consent before rating (`ethics/consent_form.md`). In a real deployment NovaShop would need a lawful basis for analysing customer messages, and would have to tell customers that their tone is analysed. `[[CHECK]]`
- **Special categories:** text-only emotion estimation does not use biometric data. Voice and face data become **biometric data** (Art. 4(14)) when processed with specific technical means that allow or confirm unique identification; processing them to identify a person is a special category under Art. 9. Our voice channel does not identify speakers, but voice recordings of real customers would still be personal data. `[[CHECK]]`
- **DPIA (Art. 35):** systematic analysis of customers' emotional state at scale is the kind of processing for which a data protection impact assessment would be expected in a real deployment. `[[CHECK]]`
- **Automated decisions (Art. 22):** the engine only routes a conversation (answer, offer a person, escalate). It does not take decisions with legal or similarly significant effects, and a human route is always available. `[[CHECK]]`
- **Rights:** a rater can ask for their ratings to be deleted using their rater id (consent form).

## 3. EU AI Act (Regulation (EU) 2024/1689)

- **Definition (Art. 3(39)):** an *emotion recognition system* infers emotions or intentions of natural persons **on the basis of their biometric data**. Our mandatory text engine works on text, not biometric data, so it is arguably outside this definition. The optional voice channel does use voice characteristics, which brings it closer to the definition. `[[CHECK]]`
- **Prohibited practice (Art. 5(1)(f)):** emotion recognition in the **workplace and in education institutions** is prohibited, except for medical or safety reasons. A customer-support assistant for shop customers is not in those settings, but using the same engine to monitor NovaShop's own support staff would be. `[[CHECK]]`
- **High-risk (Annex III, point 1(c)):** emotion recognition systems are listed as high-risk biometric systems, which brings obligations such as risk management, data governance, human oversight and logging. `[[CHECK]]`
- **Transparency (Art. 50(3)):** deployers of an emotion recognition system must inform the people exposed to it. Our replies say "I'm an automated assistant" when offering a person; a deployment would also need to say that tone is analysed. `[[CHECK]]`
- **Dates:** the prohibitions apply from 2 February 2025. The high-risk obligations were originally due from 2 August 2026; later EU proposals aimed to postpone parts of them. `[[CHECK the current dates in the official text before submission]]`

## 4. Bias and fairness

- **Lexicon written by few people:** the tiers were suggested by an AI and reviewed by one student, so they reflect a narrow view of how people express emotion. Words that are angry in one community can be neutral in another.
- **Language coverage:** only English and Portuguese are supported. Customers writing in other languages, or mixing languages, get lower confidence and a request to switch language, which is a worse service.
- **Dialects, slang and non-native speakers:** unusual spellings and slang are often unknown words, which lowers confidence and may trigger clarification more often for these customers.
- **Neurodivergent and cultural differences:** people express (or do not express) emotion differently in writing; a flat message is not proof of calm.
- **Voice:** pitch depends on sex, age and speaker; the reference statistics come from six synthetic kit files, so the voice channel has not been tested on real speakers of different groups.
- **Evaluation:** with a handful of raters and fewer than 100 messages, we cannot claim that the engine is fair across groups. We can only describe what we observed.

## 5. What the system cannot do

- It estimates the emotion that a message **expresses**, not what the customer feels. Facial and vocal expressions are not reliable read-outs of inner states (Barrett et al., 2019), and the same holds for text.
- Sarcasm and irony are only partly detected (keyword and incongruity rules). New forms of sarcasm will be missed.
- Short messages ("ok", "fine") are genuinely ambiguous; the engine asks for clarification rather than guessing.
- It understands only English and Portuguese, and only the vocabulary in its lexicons.
- Seven labels and three dimensions are a simplification of human emotion.
- The voice channel was only tested on six synthetic files; noisy recordings make it withdraw (very low confidence) rather than guess.
- It has no access to real order systems, so it never states an order status; it asks for the order number and hands over to people.

## 6. Design commitments

1. Affect is used **only to improve support**: choosing between answering, empathy, clarification and handing over. Never for pricing, marketing, upselling or profiling.
2. The assistant **discloses that it is automated** whenever it offers a person, and a human route is always available (explicit requests always win over the emotion estimate).
3. **Explicit signals beat estimates:** legal threats, safety cues and requests for a person override the emotion model.
4. **Costs of errors are not equal:** a missed escalation is treated as worse than an unnecessary offer of a person (see the cost table in `engine/evaluation/evaluate.py`).
5. **Uncertainty is shown, not hidden:** low confidence is flagged in the log and leads to clarification instead of a confident wrong action.

## References

- Barrett, L. F., Adolphs, R., Marsella, S., Martinez, A. M., & Pollak, S. D. (2019). Emotional expressions reconsidered. *Psychological Science in the Public Interest, 20*(1), 1–68.
- Regulation (EU) 2016/679 (General Data Protection Regulation).
- Regulation (EU) 2024/1689 (Artificial Intelligence Act).
