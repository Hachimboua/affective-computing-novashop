# Presentation outline (15 minutes, one speaker)

> One message and one piece of evidence per slide. Rehearse with a timer; aim
> for 13–14 minutes so questions start on time. All questions come to you, so
> practise with `qa/topic1.md` … `qa/topic5.md` and `qa/whole_system.md`.

| Time | Slide | Message | Evidence on the slide |
|---|---|---|---|
| 0:00–1:00 | 1. Title and goal | An engine that reads emotion in customer messages and decides what to do | Title, your name, "solo project" |
| 1:00–2:00 | 2. NovaShop scenario and the six actions | The engine chooses between answer, empathy, clarification, offer a person, escalate, close | The six actions with a one-line example each |
| 2:00–3:30 | 3. Architecture | One pipeline: text perception → (voice + fusion) → label → state → policy → reply | Block diagram from `engine/README.md`; "all settings in `config.py`" |
| 3:30–5:00 | 4. Topic 1: text perception | Lexicon of 12 tiers + rules (negation as a shift, intensifiers, contrast, sarcasm), confidence that rewards evidence | "not bad" vs "bad" example; tier table |
| 5:00–6:30 | 5. Topic 2: affective space, map, voice | Labels are the nearest of 7 prototypes in V/A/D; dominance separates fear from anger; voice adds activity | Prototype table; map screenshot; voice-check table (calm −0.24 vs agitated +0.25) |
| 6:30–8:30 | 6. Topic 3: state and decisions | Confidence-weighted moving average; 8 ordered rules; explicit signals win | Rule table R0–R7; a state curve for an example conversation |
| 8:30–9:30 | 7. Topic 3: robustness | Short, ambiguous, sarcastic, other-language input; safety net never crashes | 3 example messages with flags and action |
| 9:30–10:30 | 8. Topic 4: software and tests | 131 tests, Python 3.9 to 3.13, kit files byte-identical, offline | Test summary table; the clean-copy check |
| 10:30–12:30 | 9. Topic 5: evaluation | SAM ratings, agreement, engine vs humans, ablations, error analysis | `[[TODO: test-split table and the biggest error categories]]` |
| 12:30–13:30 | 10. Difficulties | Encoding, lexicon fragments, language rule, line endings, replies | 3–4 bullets, each with "found by / fixed by" |
| 13:30–14:30 | 11. Ethics and limits | Expressed vs felt emotion; GDPR and AI Act; affect used only for support | 4 design commitments |
| 14:30–15:00 | 12. Conclusion | What works, what does not, what you would do next | 3 bullets |

## Live demo (only if time allows)

A 30-second backup: run M2 in the interface and point at the human offer and the escalation. Keep the video ready in case the live demo fails.

## Before the presentation

- Re-run `py -3.12 -m unittest discover tests` and one scenario the morning of the presentation.
- Have `engine/config.py` open in an editor: many questions end with "change it now".
- Practise every live-change drill in the Q&A files at least once.
