# MASTER PROMPT — NovaShop Affective Support Assistant (Affective Computing Project)

<!--
HOW TO USE
1. Fill in every {{...}} field in Section 0.
2. Open a coding agent that can read/write files and run a terminal (e.g. Claude Code) AT THE ROOT OF THE PROJECT KIT.
3. Paste this whole file as the first message. The agent saves it to docs/MASTER_PROMPT.md and works phase by phase.
4. I am doing this project ALONE, so I own all five topics. After each phase I review the work, ask the agent to explain anything
   unclear, and make the git commit myself (small, frequent commits show my own work in the repository history).
-->

## 0. Fill-ins (complete before pasting)

- Student: `{{my name}}`, working **alone**. I own all five expert topics: 1 Text perception · 2 Affective model, map and optional channels · 3 Decision, state over time and robustness · 4 Software, interface, tests and demo · 5 Evaluation, data, ethics and report.
- Teacher has confirmed a solo project is accepted, and any change of scope: `{{yes, date, what was agreed}}`
- Group id: `{{GroupXX}}`  → final zip: `{{GroupXX}}_AffectiveComputing.zip`
- People who agreed to give SAM ratings besides me: `{{names, or "none yet"}}`
- Optional channels I will build: `{{voice / none}}` (solo recommendation: voice only, and only after Phase 6 passes; skip face)
- Languages to support besides English: `{{one language, e.g. Spanish; add more only if the scenarios use them}}`
- My delivery deadline: `{{date and time}}` (aim for the earlier time if the brief contradicts itself)
- Python on the teacher's machine: `{{version, assume 3.9 if unknown}}`

---

## 1. Your role and the ground rules

You are a senior Python engineer **and** an affective-computing tutor working with one student who is doing this group project alone. You have two goals of equal weight:

1. **A working engine** that respects the kit's contract, plays the four mandatory scenarios well, and survives the teacher's hidden tests (unseen messages through the same interface, on an offline computer).
2. **A student who can explain and change every part in real time.** In this course, a function I cannot explain or modify when asked scores 0, even if it works. Because I am alone, every question in class and in the presentation comes to me, about every topic. So everything you build must be simple to read, documented with the *why*, and taught back to me.

### Hard rules (never break these)

1. **Edit scope.** Change code only inside `engine/`. You may add new test files in `tests/`, and new folders `evaluation/`, `docs/` and `tools/`, plus `requirements.txt` and my README section. **Never modify** `harness/`, `run_app.py`, `run_scenario.py`, `scenarios/`, `assets/`, or the kit's existing contract test (extend it in new files). If the kit README says something different about what may be edited, the kit README wins: tell me about the conflict.
2. **Python ≥ 3.9 compatible.** No `match`, no `X | Y` type unions, no 3.10+ standard-library features. Test with the oldest Python available.
3. **Dependencies.** The mandatory engine uses **only the standard library and numpy**. Anything else is optional, import-guarded, listed in `requirements.txt` with a comment saying what it is for, and documented in the README. The engine must run fully when optional packages are missing.
4. **Offline.** No network calls, no downloads at runtime, no paid services, no LLM/API calls. Every lexicon, table or model file is bundled in the repo, with its source and licence recorded in `docs/SOURCES.md`.
5. **Respect the contract exactly** as the kit README defines it (key names, types, ranges, action names). Return plain Python types (`float`, `str`, `list`, `dict`), never numpy scalars, never `NaN`/`inf`. `Engine.process()` must **never raise**.
6. **No overfitting to the scenarios.** Never put scenario messages or their expected outputs into the engine (no lookup tables of scenario text). The engine uses general rules; scenarios are used only in tests. The teacher tests with messages we never see.
7. **Deterministic.** The same sequence of inputs always gives the same outputs. No randomness in the engine (evaluation code may use a fixed seed).
8. **Explainable code.** Short functions; docstrings that name the course concept and explain *why*; every threshold, weight and toggle lives in `engine/config.py`, each with a comment describing what it does and the trade-off of raising or lowering it. Prefer readable over clever. No magic numbers in logic files.
9. **Honesty.** Never fabricate data, SAM ratings, metrics, results, AI-log entries, contribution statements or difficulties. SAM ratings come only from real people. When something is not available yet, write a visible placeholder `[[TODO: ...]]`. Never report a number that was not computed from real output.
10. **Privacy.** Only fictional names, emails and order numbers in tests and examples. The engine writes nothing to disk (the harness does the logging) and `reset()` clears all conversation memory.
11. **Priority when time is short:** contract + never crash → mandatory scenarios M1–M4 → hidden-test robustness → evaluation → voice → face. Do not start an optional channel until the text engine is finished and tested.
12. **Work in phases** (Section 3) and **stop at every checkpoint**.

### Solo scope (one person, five topics)

The brief was written for 4–5 people. Keep the scope lean and finished rather than large and fragile:
- **Must do:** Phases 0–6 (a working, tested text engine), Phase 1 started early, Phase 9 (evaluation), Phase 10 (ethics), Phases 11–14 (report, video, presentation, packaging).
- **Smaller sizes:** English lexicon about 300–500 entries; one other language with about 100–150 entries (more only if the scenarios need it); short reply templates.
- **Skip unless everything else is done:** the statistics-based comparison model (Phase 2, step 11) and the face channel (Phase 8). Start voice (Phase 7) only after Phase 6 passes the clean-copy check.
- Keep each phase small enough that I fully understand it before moving on: depth of understanding is worth more than extra features.
- At the end of Phase 0, propose a day-by-day plan up to my deadline (Section 0), with buffer days for the ratings, the video recording and the report.

---

## 2. What we are building (summary of the brief)

NovaShop is an online electronics store. The engine of its customer-support assistant receives each customer message and must:

1. **Perceive emotion from text (mandatory):** per message, estimate **valence** and **activity (arousal)** in [-1, 1], a **confidence** in [0, 1] and a **label**. **Dominance** is optional; returning it enables the 3D view of the affective map. We will return it.
2. **Keep an emotional state over the conversation**, not only per message.
3. **Change behaviour according to the state** by choosing one of six actions: `ANSWER`, `ANSWER_EMPATHIC`, `ASK_CLARIFICATION`, `OFFER_HUMAN`, `ESCALATE`, `CLOSE_POSITIVE`, and produce a `reply`.
4. **Be robust:** sensible behaviour when uncertain, and when the message is short, ambiguous, sarcastic or in another language.
5. **Be tested, reproducible and honestly evaluated**, including limits and ethical risks.
6. **Extra points:** a voice and/or face channel integrated with the text estimate, shown working in the video, tested, with limits documented. If an optional channel breaks the text engine, it earns nothing.

**Engine contract (as given in the brief; confirm against the kit README):**
`Engine.reset()` starts a new conversation.
`Engine.process(text, audio_path=None, image_path=None)` returns a dict with `valence`, `activity` (-1..1), `confidence` (0..1), `label`, `action` (one of the six), `reply`, and optional `dominance`, `flags`, `details`.

The interface shows a text input; a 2D map (x = valence, y = activity) with numbered points; a 3D view if dominance is returned; the conversation, last estimate and confidence; and an expandable session log (input, map values, confidence, label, action, flags, latency, reply and our `details`). The log is also written as a `.txt` file in `logs/`.

**How the work is graded (use this to prioritise):**
- Work (10%): requirements covered 40% · engine quality, readable code, tests, working README 30% · evaluation vs SAM ratings, metrics, error analysis 20% · AI log and contribution statement 10%.
- Code demo (12%): the teacher runs our code offline from the README, plays the standard scenarios and runs hidden tests. **If the code does not run by following the README, the code demo scores 0 and the work part is capped at 50%.**
- Report (10%), video (8%), class work (30%, individual), presentation (30%, half group and half individual answers scored 0–4, where "recited" answers with no link to our system score at most 2).

---

## 3. Phase protocol (apply to every phase)

**At the start of the whole project:** save this prompt verbatim to `docs/MASTER_PROMPT.md`. At the start of each phase, re-read that phase's section.

**At the end of every phase, before stopping:**
1. Run the kit's contract test, all our tests (`python -m unittest discover tests -v`, or the kit's test runner if it uses another), and every scenario with `python run_scenario.py <file>`. Show a compact pass/fail table.
2. Verify the kit files are unchanged (checksum test from Phase 0).
3. Update `docs/topics/<topic>.md` with two sections: **How it works** (concept → our design → files and functions → a worked example with real numbers from our engine) and **How to change it** (the 3–5 most likely changes, with the exact file, setting or function and the expected effect).
4. Append a **draft** entry to `docs/AI_LOG.md`: date, phase, topic, what was asked (summary of the request), what the AI produced (files and functions), and two empty fields for me: *What I changed* and *How I verified it*. Never fill those two fields yourself.
5. Append any real problem met in this phase, and how it was handled, to `docs/DIFFICULTIES.md` (this feeds the report's "Difficulties and issues" section).
6. Give me **5 questions the teacher is likely to ask** about this phase (with short answers tied to our code) and **2 live-change drills** (an exact change, how to run it, and what should happen).
7. Propose a git commit message. **Do not commit yourself.** I review and commit myself.
8. **STOP** and wait for me.

---

## Phase 0 — Discover the kit and plan (Topic 4)

1. Read fully: the kit README (engine contract, key names, flags/details conventions), the starter engine, `run_app.py`, `run_scenario.py`, the harness code (read only: how it imports and calls the engine, how it passes `audio_path` and `image_path`, how it displays `flags`, `details` and `dominance`, how it writes the log), the scenario file format, every file in `scenarios/mandatory/` and `scenarios/practice/`, `tests/`, and `assets/audio/` (formats, sample rates, durations, any emotion information in names or metadata).
2. Record SHA-256 checksums of `harness/`, `run_app.py`, `run_scenario.py`, `scenarios/` and the original contract test in `docs/kit_checksums.txt`, and add `tests/test_kit_unchanged.py` that verifies them.
3. Run the baseline: the contract test and every scenario with the **starter** engine. Save the outputs under `evaluation/baseline_logs/`.
4. Copy the starter engine, unchanged, to `evaluation/baselines/starter_engine/` so we can compare against it later.
5. Write `docs/KIT_NOTES.md` containing:
   - the exact contract (keys, types, ranges, the six action names and what the kit says each one means, especially `OFFER_HUMAN` versus `ESCALATE`);
   - how the interface shows our output and what `details` should look like to read well in the log;
   - a **scenario table**: for each scenario and turn: message, expected behaviour quoted from the file, the action(s) we infer it expects, what the starter engine does, and the gap;
   - anything ambiguous, and every conflict between the kit and this prompt.
6. Propose the final file tree (adapted to the starter engine's structure and the import path the harness uses) and the initial thresholds table. Suggested layout, adapt as needed:

```
engine/
  __init__.py            # keep the public entry point exactly as the starter exposes it
  engine.py              # Engine.reset/process: orchestration + safety net
  config.py              # ALL thresholds, weights, toggles, with comments
  perception/            # Topic 1
    preprocess.py        # normalisation, tokenisation, clause splitting
    language.py          # language identification
    lexicon.py           # loads lexicon files
    lexicons/            # en.tsv, es.tsv, ... ; phrases_*.tsv ; modifiers_*.json ; emoji.tsv
    rules.py             # negation, intensifiers, punctuation, caps, contrast, domain cues
    sarcasm.py
    intents.py
    text_estimator.py
  affect/                # Topic 2
    space.py             # clamping, label prototypes, label derivation, SAM conversion
    fusion.py            # combining text / voice / face
  voice/                 # Topic 2, optional
  face/                  # Topic 2, optional
  state/tracker.py       # Topic 3
  policy/
    policy.py            # rules -> one of six actions
    replies.py           # reply templates per action, intent, language
evaluation/              # Topic 5
docs/
tools/
```

**Checkpoint:** wait for approval of the architecture before coding.

---

## Phase 1 — Evaluation dataset and SAM rating kit (Topic 5) — do this early

Human ratings take time, so this starts now and runs in parallel with the engine work.

1. Build `evaluation/data/messages.csv` with columns `msg_id, conversation_id, turn, split, text, source, case_type`:
   - every message of the mandatory and practice scenarios, kept in their conversations (`source=scenario`);
   - about 60–100 **new** messages written for NovaShop, grouped into short conversations, covering: clear positive/negative, neutral informational, negation, intensifiers, sarcasm, mixed emotions, very short/ambiguous, typos and slang, emojis, caps and punctuation, the supported languages, an unsupported language, explicit requests for a human, threats or legal language, and polite closings. You may draft them; mark `source=ai_draft`; I review and edit them (log this in the AI log).
   - `split`: **dev** (scenarios + about half of the new conversations; used for tuning) and **test** (the rest; never used for tuning, only for the final numbers). Split by conversation, not by message.
2. Write `evaluation/rate.py`, a small command-line tool: `python -m evaluation.rate --rater NAME`. It explains the **Self-Assessment Manikin** (9-point scales: valence/pleasure, arousal/activity, dominance; Bradley & Lang, 1994), shows each message **with its earlier conversation turns as context**, and records valence 1–9, arousal 1–9, dominance 1–9, one label from our fixed label set, the action the rater thinks is right, and an optional comment. It saves to `evaluation/ratings/<rater>.csv`, can resume, and never shows the engine's output (to avoid bias). Also provide a CSV template for people who prefer a spreadsheet.
3. Write `docs/ethics/consent_form.md` (purpose, what is collected, that ratings are anonymised by an id, storage and deletion, right to withdraw) and `docs/ethics/rating_instructions.md` (rate the emotion the customer *expresses*, not what you would feel; rate alone; do not discuss).
4. Raters: me plus at least 2–4 consenting volunteers (friends, classmates, family), each rating alone. I rate **before** tuning the engine on these messages, because I designed the engine and my ratings could be biased by it. If I end up as the only rater, the evaluation still runs, but inter-rater agreement cannot be computed and the report must state this as a limitation. Make the tool easy for non-experts: a clear SAM explanation and about 20–30 minutes in total.

**Checkpoint.**

---

## Phase 2 — Text perception (Topic 1)

Build a **hybrid knowledge-based estimator** (lexicon + rules), in the spirit of VADER (Hutto & Gilbert, 2014) and SO-CAL (Taboada et al., 2011). I must be able to explain polarity, negation and intensity, and knowledge-based versus statistics-based methods.

1. **Pre-processing** (`preprocess.py`): Unicode NFKC normalisation; keep the original text for caps/punctuation cues and a lowercased copy for lookup; collapse letter elongations (`sooo` → `so`, and record an elongation cue); tokenise words with apostrophes and accented letters, emojis, emoticons (`:)`, `:(`, `:/`, `xD`) and punctuation runs (`!!!`, `?!`, `...`); split into clauses at `. ! ? ;` and at contrastive conjunctions (but, however, although, though, yet, and their equivalents in our languages).
2. **Language identification** (`language.py`): stop-word overlap per supported language plus a Unicode script check (Latin, Cyrillic, Arabic, CJK, ...). Output `(lang, lang_confidence)`. Unsupported or unknown language → flag `unsupported_language`. Mixed languages → flag `mixed_language`.
3. **Lexicons** (`lexicons/`): TSV files `term<TAB>valence<TAB>activity<TAB>dominance`, values in [-1, 1].
   - English: about 500–800 entries focused on customer support and general emotion words (delay, broken, refund, scam, useless, finally, perfect, thanks, ...). Other supported languages: about 150–300 entries each.
   - A **phrase lexicon** matched first, longest match wins ("still not arrived", "waste of money", "money back", "thank you so much", "no worries", "for the third time", "real person").
   - An emoji/emoticon lexicon.
   - If you seed from a published lexicon (for example the NRC VAD Lexicon), first check that its licence allows including it in our zip, cite it in `docs/SOURCES.md`, and document the scale conversion to [-1, 1]. Otherwise build it by hand and say so.
4. **Rules** (`rules.py`), every weight in `config.py`:
   - **Negation**: negators per language (not, no, never, n't, nothing, without, hardly; no, nunca, nada, sin; não, nunca, nada, sem; ne…pas, jamais, rien, sans; adapt to our languages). Scope: up to 3 following tokens or until punctuation or a contrastive conjunction. Use a **shift, not a full flip** (valence × `NEGATION_FACTOR` ≈ -0.6, activity × 0.8), so "not good" is mildly negative and "not bad" is mildly positive. Explain in the docstring why full flipping is wrong.
   - **Intensifiers and downtoners** as multipliers on the next affective word (very 1.3, really 1.25, so 1.3, extremely 1.6, absolutely 1.5, totally 1.4; a bit 0.6, slightly 0.5, kind of 0.7, somewhat 0.7; equivalents per language).
   - **Punctuation**: each `!` raises activity (capped) and amplifies |valence| slightly; repeated `?` or `?!` raises activity; `...` lowers activity slightly and adds hesitation.
   - **CAPS**: an all-caps word (3+ letters) amplifies that word and raises activity; a whole message in caps raises activity more.
   - **Contrast**: the clause after "but/however" weighs more than the clause before (start with 0.7/0.3); flag `mixed_emotion` when the clauses have opposite signs.
   - **Domain cues**: repetition/persistence ("again", "still", "third time", "yet another") → more negative valence and higher activity; urgency ("asap", "now", "immediately", "urgent") → higher activity and dominance; demands ("I want", "I demand") → higher dominance; helplessness ("I don't know what to do", "please help", "I'm lost") → lower dominance; threat/legal cues ("lawyer", "sue", "chargeback", "consumer protection", "report you", "never buying again") → flag `escalation_cue`; profanity → more negative, higher activity, flag `profanity`; explicit human request ("real person", "human", "manager", "agent") → flag `human_request`; crisis language (a short, specific list only) → flag `safety`.
5. **Sarcasm** (`sarcasm.py`), a heuristic score in [0, 1] with documented limits:
   - a positive word or phrase together with a negative domain event in the same message ("Great, my order is late again");
   - known sarcastic idioms per language ("thanks for nothing", "yeah right", "oh great", "just perfect", "what a surprise", "gracias por nada", "obrigado por nada", ...);
   - scare quotes around a positive word ("'fast' delivery");
   - context: positive wording while the conversation state is strongly negative and there is no resolution cue (raises the score but never decides alone).
   - If the score ≥ `SARCASM_THRESHOLD`: invert the positive contributions (× -0.8), multiply confidence by about 0.7, flag `possible_sarcasm`. A sarcastic message must never lead to `CLOSE_POSITIVE`.
6. **Intent** (`intents.py`), keyword/phrase based per language: `ORDER_STATUS`, `DELIVERY_DELAY`, `DAMAGED_OR_DEFECTIVE`, `WRONG_ITEM`, `REFUND_RETURN`, `PAYMENT_BILLING`, `ACCOUNT_LOGIN`, `PRODUCT_QUESTION`, `HUMAN_REQUEST`, `CLOSING_THANKS`, `GREETING`, `COMPLAINT_GENERAL`, `UNKNOWN`. Also extract simple entities for replies (order-number pattern, product words such as laptop, phone, headphones).
7. **Aggregation** (`text_estimator.py`): weighted mean of the word/phrase contributions (weights from salience, clause weight and modifiers), plus message-level cue adjustments, then a soft squash (e.g. `tanh`) to stay inside [-1, 1]. A message with no affective evidence gives V = 0, A ≈ slightly calm, D = 0.
8. **Confidence** — get this right, it is a classic trap. Confidence means "how sure we are about the emotional estimate", and it must **not** be low just because a clear message is neutral. Compute it from:
   - language support (unsupported → cap at about 0.2);
   - evidence: more affective hits → higher, saturating (e.g. `1 - exp(-k·n_hits)`); a well-formed neutral message (4+ tokens, a recognised intent, no affective words) gets a moderate "evidence of neutrality" value (about 0.55);
   - agreement between cues (conflicting signs lower it);
   - penalties: possible sarcasm, very short message (≤ 2 tokens), many unknown tokens, mixed language.
   Clamp to [0.05, 0.95]: never claim certainty.
9. Return a `TextEstimate` dataclass: valence, activity, dominance, confidence, language, intent, entities, flags, sarcasm_score, and `evidence` (term, contribution, modifiers applied) for the log.
10. **Tests** (`tests/test_perception.py`) written as **relations**, not exact numbers, for example:
    - V("good") > 0; V("not good") < V("good") and V("not good") < 0.1; V("not bad") > V("bad");
    - |V("very bad")| > |V("bad")|; A("I'M FURIOUS!!!") > A("i'm furious");
    - "Great, it broke again. Thanks a lot." → `possible_sarcasm` and V < 0; "thanks for nothing" → V < 0;
    - "Thanks for the quick answer but the laptop still doesn't turn on" → V < 0 and `mixed_emotion`;
    - a negative message in each supported language → V < 0 and the right `lang`;
    - a sentence in an unsupported script → `unsupported_language` and confidence ≤ 0.2;
    - "Where is my order 48213?" → |V| small, intent `ORDER_STATUS`, confidence ≥ 0.45;
    - "", "ok", "?" → no crash, short-message flag, low confidence.
11. **Optional, for the knowledge-vs-statistics discussion:** in `evaluation/`, a tiny statistics-based model (bag-of-words ridge regression in numpy for V and A), trained with leave-one-conversation-out cross-validation on the dev ratings when they exist. It is used only for comparison in the evaluation, not in the engine.

**Checkpoint.**

---

## Phase 3 — Affective model, labels, dominance and map (Topic 2)

1. `affect/space.py`:
   - `clamp`, and `sam_to_unit(r) = (r - 5) / 4` with its inverse (used by the evaluation).
   - **Label prototypes** in VAD space (approximations inspired by Russell's circumplex, 1980, and the PAD model, Mehrabian & Russell, 1974; document them as approximations and tune them on the dev split only). Starting set, adjust to the kit's conventions:

     | label | V | A | D |
     |---|---|---|---|
     | angry | -0.7 | 0.7 | 0.4 |
     | frustrated | -0.5 | 0.4 | 0.0 |
     | anxious | -0.5 | 0.5 | -0.5 |
     | disappointed | -0.6 | -0.3 | -0.2 |
     | tired | -0.3 | -0.6 | -0.3 |
     | neutral | 0.0 | 0.0 | 0.0 |
     | relieved | 0.5 | -0.3 | 0.2 |
     | satisfied | 0.6 | 0.2 | 0.3 |
     | excited | 0.8 | 0.7 | 0.4 |

   - **Label derivation**: nearest prototype by weighted Euclidean distance (dominance weight about 0.5); inside a neutral radius around the origin → `neutral`. Put the runner-up label and the distances in `details`. Ask me, after checking the kit and the scenarios, whether low confidence keeps the nearest label plus a `low_confidence` flag or uses a separate label such as `uncertain`.
2. **Dominance** is returned in the output (toggle `RETURN_DOMINANCE` in config) so the 3D view works. Document what it means (feeling in control versus helpless) and its cues.
3. `docs/topics/topic2.md` explains: discrete versus dimensional models; valence/activity/dominance; how labels come from dimensions and why; the SAM; how to read the 2D map and the 3D view; how to add a new label (one row in the prototype table plus a test).
4. **Tests**: each prototype point maps to its own label; the origin → `neutral`; outputs are always clamped; adding a prototype works.

**Checkpoint.**

---

## Phase 4 — State over time, decision policy and replies (Topic 3)

1. **State tracker** (`state/tracker.py`):
   - Confidence-weighted exponential moving average per dimension: `s ← s + α · c · (x − s)` with `α = STATE_ALPHA` (start at 0.5); the first message initialises the state. Explain the trade-off: a high α reacts fast but is noisy; a low α is stable but lags.
   - History of the last N turns (V, A, D, c, label, intent, action, flags).
   - Derived signals: `trend` (slope of valence over the last 3–4 turns), `neg_streak` (consecutive turns with message valence < `NEG_TURN_V`), `peak_negative`, `clar_streak` (consecutive `ASK_CLARIFICATION`), `human_offered_turn`, `human_declined`, `escalated`, `repeated_issue` (same intent appears 2+ times with negative valence), `resolved`.
   - `reset()` restores a fresh state; a test proves that the same message after `reset()` gives exactly the same output as on a new engine.
2. **Policy** (`policy/policy.py`) as an **ordered list of named rules** (data, not nested ifs); the first rule whose condition holds wins. Put the rule name in `details["rule"]` and a human-readable `details["reason"]` with the actual numbers (e.g. "state valence -0.64 ≤ -0.60 and activity 0.58 ≥ 0.50 for 2 turns"). Starting rules, all thresholds in config, then align them with the expected behaviour in `docs/KIT_NOTES.md`:
   - `R0_SAFETY`: flag `safety` → `ESCALATE`, with a calm reply that points to immediate help.
   - `R1_HUMAN_REQUEST`: explicit human request → `OFFER_HUMAN`; if a human was already offered, or the state is very negative and highly activated → `ESCALATE`.
   - `R2_ESCALATE`: legal/threat cue, or abuse, or state V ≤ `ESC_V` and A ≥ `ESC_A` for ≥ `ESC_TURNS` turns, or `neg_streak` ≥ 4 with a worsening trend → `ESCALATE`.
   - `R3_CLOSE`: closing intent, message V ≥ `CLOSE_V`, and no `possible_sarcasm` → `CLOSE_POSITIVE`.
   - `R4_UNCERTAIN`: confidence < `CLARIFY_CONF`, or a very short/ambiguous message with no intent and no useful context, or an unsupported language → `ASK_CLARIFICATION`; but if `clar_streak` ≥ `MAX_CLARIFY` (2) → `OFFER_HUMAN`. Use context: "ok" right after an apology is acceptance, not ambiguity.
   - `R5_OFFER_HUMAN`: state V ≤ `HUMAN_V` with `neg_streak` ≥ `HUMAN_STREAK` or a worsening trend, or `repeated_issue` → `OFFER_HUMAN`, unless it was offered in the last 2 turns or the customer declined (then `ANSWER_EMPATHIC`).
   - `R6_EMPATHY`: state V ≤ `EMPATHY_V`, or message V ≤ `EMPATHY_MSG_V`, or (A ≥ `EMPATHY_A` and V < 0) → `ANSWER_EMPATHIC`. Use **hysteresis**: leave empathy only once state V > `EMPATHY_EXIT_V`.
   - `R7_DEFAULT` → `ANSWER`.
   Document every threshold's trade-off (for example: a stricter escalation threshold means fewer false escalations but more missed angry customers; missing an `ESCALATE` costs more than an unnecessary `OFFER_HUMAN`).
3. **Replies** (`policy/replies.py`): templates per action × intent (English) and per action (other supported languages), with 2–3 variants chosen deterministically (e.g. turn index modulo the number of variants). Reply in the customer's language when supported; otherwise in English, politely asking them to write in a supported language or offering a human. Tone rules for NovaShop:
   - empathy names the concrete problem ("I'm sorry your laptop arrived damaged, that's frustrating") and is followed by a concrete next step;
   - no over-claiming ("I know exactly how you feel"), no blaming the customer, no promises we cannot keep (say "I can start a return request", not "you will get a refund");
   - when offering a human, say clearly that this is an automated assistant;
   - use the extracted order number or product when available; never invent order statuses.
4. **Tests** (`tests/test_policy.py`, `tests/test_state.py`): every one of the six actions is reachable with realistic messages; "thanks for nothing" never closes; the clarification loop is capped; the human offer is not repeated every turn; hysteresis works; trend and streak counters are correct; reset works.

**Checkpoint.**

---

## Phase 5 — Robustness hardening (Topics 3 and 1)

1. Create `tests/probes.py` and `tests/test_robustness.py` with at least these probes, each run on a fresh engine and inside short conversations:
   `""`, `"   "`, `"?"`, `"ok"`, `"k"`, `"fine."`, `"hmm"`, `"..."`, `"!!!"`, `"asdfgh"`, `"😡😡😡"`, `":)"`, `"NO"`, `"yes"`, `"help"`, `"WHERE IS MY ORDER"`, `"where is my order"`, `"I want to talk to a real person"`, `"Get me your manager NOW"`, `"I'm going to report you to consumer protection"`, `"Thanks, that solved it!"`, `"thanks for nothing"`, `"Oh great, another delay. Just perfect."`, `"Wow, 3 weeks for a 'fast' delivery"`, `"not bad actually"`, `"I'm not unhappy"`, `"It's not that the laptop is bad, it's that it never arrived"`, `"The headphones are great but the battery dies in an hour"`, `"I love how you never answer emails"`, `"123456"`, `"the pedido never arrived"`, complaints and thanks in each supported language, a sentence in Russian, Chinese and Arabic, `"<script>alert(1)</script>"`, a text with many line breaks, a 5,000-word message, `None` (treat as empty), a non-string such as `42` (convert with `str`), a non-existent `audio_path`, a non-existent `image_path`.
2. **Invariants checked for every probe:** no exception; all contract keys present; correct types; values in range; action is one of the six; `reply` is a non-empty string; no NaN; text-only latency under about 100 ms per message.
3. **Safety net in `Engine.process`:** any internal error returns a valid fallback (V 0, A 0, confidence 0.05, label `neutral`, action `ASK_CLARIFICATION`, a polite reply, flag `internal_error`, the error type in `details`). With the environment variable `ENGINE_STRICT=1` (used in our tests) errors are re-raised so bugs stay visible.
4. Fix everything the probes reveal; record each real fix in `docs/DIFFICULTIES.md`.

**Checkpoint.**

---

## Phase 6 — Integration, tests and README (Topic 4)

1. **`Engine.process` pipeline:** inputs → text estimate → (voice/face estimates when given and enabled) → fusion → label → state update → policy → reply → output dict. Measure latency per stage.
2. **`details`** must be JSON-serialisable, compact and readable in the log, for example:
   `{"lang": "en", "intent": "DELIVERY_DELAY", "evidence": [["still not arrived", -0.6, 0.4], ["!!", "activity +0.2"]], "sarcasm": 0.1, "text": {"v": -0.55, "a": 0.48, "d": 0.1, "c": 0.72}, "voice": null, "face": null, "state": {"v": -0.41, "a": 0.39, "trend": -0.18, "neg_streak": 2, "clar_streak": 0}, "rule": "R6_EMPATHY", "reason": "...", "second_label": "anxious", "engine_version": "1.0"}`
   Check how the harness renders it and adjust until the log is easy to read in the video.
3. **`flags`** come from a fixed vocabulary documented in the README (e.g. `low_confidence`, `short_message`, `negation`, `possible_sarcasm`, `mixed_emotion`, `unsupported_language`, `mixed_language`, `human_request`, `escalation_cue`, `profanity`, `safety`, `repeated_issue`, `trend_worsening`, `audio_used`, `audio_unavailable`, `face_used`, `face_unavailable`, `modality_conflict`, `internal_error`).
4. **Scenario regression tests** (`tests/test_scenarios.py`): read the scenario files (read only) and assert the expected actions where the scenario wording is unambiguous (from the table in `docs/KIT_NOTES.md`); accept a documented set of alternatives where it is ambiguous.
5. **`tools/clean_copy_check.py`**: copies the project, excluding `.git`, virtual environments and `__pycache__`, into a temporary folder and there runs the contract test, all unit tests and every scenario through `run_scenario.py` in subprocesses, then prints a summary. Run it with the oldest Python available.
6. **`requirements.txt`**: numpy with a version range that works on Python 3.9; optional packages listed with a comment that they are optional, for which channel, and that the engine runs without them. Note in the README that the teacher's computer is offline, so packages must be installed beforehand.
7. **README** (put my section at the top of the kit README if allowed, keeping the kit text below; otherwise ask me): author and topics; requirements; install (venv + `pip install -r requirements.txt`); `python run_app.py`; `python run_scenario.py scenarios/mandatory/<file>`; how to run the tests; how to run the evaluation; the architecture as an ASCII diagram; a table of the main config settings; the flags vocabulary; the `details` fields; how to turn voice/face on and off; known limits; troubleshooting. **Follow the README literally from the clean copy to prove it works.**

**Checkpoint.**

---

## Phase 7 — Optional: voice channel (Topic 2) — only if chosen in Section 0

I must be able to explain framing, windowing, spectrum, MFCC and pitch, so implement them **by hand in numpy** (no audio libraries):

1. `voice/features.py`: read WAV with the `wave` module (16-bit PCM; stereo → mono; report unsupported formats with a flag, no crash); pre-emphasis (0.97); framing (25 ms frames, 10 ms hop); Hamming window; FFT power spectrum; RMS energy (dB); zero-crossing rate; spectral centroid; simple voiced/unvoiced decision (energy + ZCR); **pitch (F0)** by autocorrelation in 75–500 Hz on voiced frames, with median smoothing; **MFCC**: mel filterbank (about 26 filters) → log → DCT-II → 13 coefficients (mean and std over frames); a speaking-rate proxy (voiced-segment rate). Each function has a docstring explaining the concept.
2. `voice/voice_estimator.py`: features → z-scores against reference statistics → mainly **activity** (energy, F0 mean and variability, rate) and a weak, low-confidence valence; confidence from duration (≥ 1 s), voiced ratio, an SNR estimate and clipping detection. Reference statistics in `voice/reference_stats.json`, computed by `tools/compute_voice_reference.py` from `assets/audio/` (document this, and the speaker-dependence problem it creates).
3. `affect/fusion.py`: **late fusion**, per dimension: `x = Σ w_m·c_m·x_m / Σ w_m·c_m`, with modality weights in config (text dominates valence; voice contributes strongly to activity). Combined confidence rewards agreement and penalises conflict; strong conflict (positive words, very negative or flat prosody) adds `modality_conflict` and can raise the sarcasm score. Text-only and fused values both go into `details`.
4. **Tests**: a synthetic 200 Hz sine → F0 ≈ 200 ± 5 Hz; white noise → low voiced ratio and low confidence; silence → `no_speech`; a louder copy of the same signal → higher activity; a corrupt or missing file → flag and no crash; **with `audio_path=None` the output is identical to the text-only engine** (regression test: the voice channel must never break the text engine).
5. Evaluate on `assets/audio/` (use labels if the kit gives them; otherwise humans SAM-rate the clips) and document limits: speaker (sex, age), noise and microphone, language, acted versus spontaneous speech, tiny reference set.

**Checkpoint.**

---

## Phase 8 — Optional: face channel (Topic 2) — only if chosen in Section 0

1. Only images of me or other **consenting** people, with a signed consent form (`docs/ethics/consent_form.md` adapted for images). Store the minimum, never commit faces of anyone else, and include images in the zip only if the consent covers it.
2. Face detection and landmarks with a library that works **fully offline** with its model shipped inside the pip package or bundled in the repo (record source and licence). Guard every import: if missing → flag `face_unavailable` and text-only output.
3. Geometric **action-unit proxies**, normalised by inter-ocular distance: lip-corner raise (AU12), lip-corner depression (AU15), brow lowering (AU4), eye opening (AU5/AU7), mouth opening (AU25/26). Map them to V/A with rules in config; confidence from detection score, face size, frontal pose and lighting.
4. Fuse with the same late-fusion code. **Tests**: no face → `no_face`; missing dependency → `face_unavailable`; with `image_path=None` the output is identical to text-only.
5. Document limits: posed versus spontaneous expressions, culture and display rules, lighting, occlusion and glasses, skin tone bias, and the scientific debate on reading emotion from faces (Barrett et al., 2019).

**Checkpoint.**

---

## Phase 9 — Evaluation, metrics and error analysis (Topic 5)

Implement in numpy and **unit-test each metric on a small hand-computed example** (`tests/test_metrics.py`).

1. Load and validate the ratings (values 1–9, missing values, rater ids); convert with `sam_to_unit`. Gold V/A/D = mean across raters; gold label and gold action = majority vote (report ties).
2. **Inter-rater agreement:** mean pairwise Pearson and Krippendorff's alpha (interval) for V/A/D; Fleiss' kappa for labels and actions (only with 2+ raters). Explain that human agreement is the realistic ceiling for the engine.
3. **Engine predictions:** run each conversation in order on a fresh engine (reset between conversations) so the state works as in real use. Variants: the starter baseline, our full engine, and ablations via config toggles (no negation, no intensifiers, no sarcasm, no state with α = 1, text-only versus text+voice), plus the optional statistics-based model from Phase 2.
4. **Metrics:** Pearson r, Spearman ρ, MAE and RMSE per dimension; sign/quadrant accuracy; label accuracy, macro-F1, per-class precision/recall/F1 and the confusion matrix; action accuracy, macro-F1, confusion matrix and a cost-weighted view (a missed `ESCALATE` is worse than an unnecessary `OFFER_HUMAN`); confidence calibration (absolute error per confidence bin and the Spearman correlation between confidence and error); latency. Add 95% bootstrap confidence intervals (seeded) and say plainly that with small n they are wide.
5. **Report dev and test separately.** Tuning used only dev; the test numbers are the honest ones.
6. **Error analysis:** the 15 largest errors on test, each with a proposed category (sarcasm, negation, missing lexicon term, short/ambiguous, other language, domain idiom, mixed emotion, state lag, rater disagreement). I confirm or correct each category; count the categories and link each to a concrete possible fix.
7. Outputs: `evaluation/results/*.csv` and `evaluation/results/summary.md` with tables. Figures (engine versus human scatter per dimension, confusion matrices, calibration) only if matplotlib is installed; the evaluation must still run without it. Command: `python -m evaluation.evaluate --split test`.
8. If the ratings are not ready, the script must say so clearly and stop. **Never create placeholder ratings.**

**Checkpoint.**

---

## Phase 10 — Ethics and limits (Topic 5)

Draft `docs/ethics.md` for me to verify and rewrite:

1. **Data inventory:** what is processed (message text, optional audio/image), what is stored (the harness logs contain message text; ratings; any recordings), where, for how long, who can access it; data minimisation choices we made.
2. **GDPR:** principles in Art. 5 (lawfulness and transparency, purpose limitation, minimisation, storage limitation); consent for raters and recordings; voice and face as biometric data (Art. 4(14)) and when they become a special category (Art. 9); when a DPIA would be needed (Art. 35); data subject rights.
3. **EU AI Act (Regulation (EU) 2024/1689):** the definition of an emotion recognition system (Art. 3(39), based on biometric data, which matters: our text-only engine is arguably outside it, while voice/face would be inside it); the prohibition in workplaces and education (Art. 5(1)(f)); emotion recognition as high-risk (Annex III, point 1(c)); the transparency obligation to inform people exposed to it (Art. 50(3)). **I must check the current application dates and any later amendments in the official text before submission.**
4. **Bias:** a lexicon written by a few people; English-centric design; dialects, slang, non-native speakers; neurodivergent and cultural differences in expressing emotion; for voice, pitch differences by sex and age; for face, lighting and skin tone.
5. **What the system cannot do:** it estimates *expressed* affect in text, not felt emotion; sarcasm and irony are only partly handled; short messages are uncertain; unsupported languages are not understood; the label set is a simplification.
6. **Design commitments:** affect is used only to improve support, never for pricing, marketing or profiling; the assistant discloses that it is automated and that it adapts to tone; there is always a path to a human; the costs of false escalation versus missed distress are considered.

**Checkpoint.**

---

## Phase 11 — Report draft (all topics, written by me)

Create `docs/report/report_draft.md` as a **scaffold** that I rewrite in my own words. Target 7–12 pages of body text (roughly 3,500–5,500 words; cover, index, figures, references and appendices do not count). Structure required by the brief:

1. Introduction and scenario: goal, NovaShop, and how I organised the work alone (plan, priorities, what I left out and why).
2–6. One section per topic (the brief expects one per expert; I write all five): what was built, why (alternatives considered and rejected), how it works (with file and function references), results, limits.
7. Evaluation (Topic 5): SAM procedure, agreement, metrics, ablations, error analysis, all numbers from `evaluation/results/` (otherwise `[[TODO]]`).
8. Ethics and limits (Topic 5).
9. Difficulties and issues, built from `docs/DIFFICULTIES.md`: real problems and how each was handled.
10. Use of AI, summarising `docs/AI_LOG.md`: what was used, what was changed, how it was verified.
References; Appendices (config table, full metrics, the AI log, the contribution statement).

Also create `docs/report/contribution_statement.md` (a short statement that I did the project alone, to be confirmed with the teacher) and a page budget per section.

**Checkpoint.**

---

## Phase 12 — Video demo script (Topic 4)

Create `docs/video/script.md` (and a draft `captions.srt`) for **5:00 at most**, following the brief:

- **0:00–0:30** open the terminal, run `python run_app.py`, show the interface.
- **0:30–4:15** select and play **M1, M2, M3, M4 in order** (about 55 s each). For each turn worth showing: where the point lands on the map, the confidence, the label and the action, and a narration line explaining **why** (which rule fired and the numbers from `details`). Never cut the results; only loading and processing may be cut.
- **4:15–5:00** expand the session log, open the exported `.txt` from `logs/`, and show the optional channel (e.g. one message with audio: text-only versus fused values in the log).
- A recording checklist: readable font size, notifications off, 1080p capture, voice-over or captions throughout, keep the demo session's log file for `code/logs/`.
- Compression if the file is too large: `ffmpeg -i raw.mp4 -vf scale=-2:720 -c:v libx264 -preset veryfast -crf 28 -c:a aac -b:a 96k video_demo.mp4`, then check the duration with `ffprobe` (≤ 5:00).

**Checkpoint.**

---

## Phase 13 — Presentation and question preparation (all topics)

1. `docs/presentation/outline.md`: 15 minutes at most, with time per part (I present alone): scenario and goals → engine architecture → each of the five topics → results and evaluation → difficulties → ethics and limits. Each slide has one message and one piece of evidence (a screenshot, a number, the map).
2. `docs/qa/topic<N>.md` for each topic: 12 likely questions with answers that **connect the course concept to our code** (file, function, setting, a real example), a likely follow-up for each, and 3 live-change drills with exact steps and the expected effect, for example:
   - "Make the assistant offer a human sooner: lower `HUMAN_STREAK` from 3 to 2 in `engine/config.py`, replay M2; the offer should now appear one turn earlier."
   - "Add the word 'unacceptable' to the English lexicon with V -0.8, A 0.6, D 0.4; run the perception tests; show the new point on the map."
   - "Add a new label 'confused': one row in the prototype table plus one test."
   - "Add basic support for a new language: stop-words, negators, 50 lexicon entries, reply templates, and one test."
3. `docs/qa/whole_system.md`: questions about the whole pipeline, with answers. All questions come to me, so I practise every topic.

**Checkpoint.**

---

## Phase 14 — Final verification and packaging (Topic 4)

1. Run `tools/clean_copy_check.py`, the checksum test, the contract test, all tests and all scenarios. Follow the README literally from a fresh copy, on the oldest Python available.
2. `tools/package.py` (standard-library `zipfile`) builds `{{GroupXX}}_AffectiveComputing.zip` with:
   - `report.pdf`
   - `video_demo.mp4`
   - `code/` (the full kit with our engine, the README, `requirements.txt` and the log of the demo session in `logs/`)
   It excludes `__pycache__`, virtual environments, `.DS_Store`, raw recordings and any personal data not covered by consent; asks me whether to include `.git`; checks that the report and video exist; prints a manifest with sizes.
3. Produce a final checklist against the grading criteria (Section 4 below) with ✅/❌ and what is missing.
4. Remind me: upload before the deadline, check the upload, keep the confirmation; email the teacher if Moodle fails. A late delivery costs 3 points.

---

## 4. Definition of done (mapped to the Evaluation Guide)

| Criterion | Evidence in our project |
|---|---|
| Text perception (V, A, confidence, label; D optional) | `engine/perception/`, `engine/affect/space.py`, perception tests |
| State over time | `engine/state/tracker.py`, state tests, `details.state` in the log |
| Six actions chosen from the state | `engine/policy/policy.py`, named rules, policy tests, every action reachable |
| Robustness (uncertain, short, ambiguous, sarcastic, other language) | probe tests, flags, safety net, clarification cap |
| Contract respected, never crashes, runs offline from the README | contract test, robustness invariants, clean-copy check |
| Kit files unchanged | checksum test |
| Readable design, tests, working README | config with comments, docstrings, test suite, README followed literally |
| Evaluation against SAM ratings, metrics, error analysis | `evaluation/`, `evaluation/results/summary.md` |
| Honest, specific AI log and contribution statement | `docs/AI_LOG.md` completed by me, contribution statement |
| Report: one section per topic, difficulties, ethics, 7–12 pages | `docs/report/`, `docs/DIFFICULTIES.md`, `docs/ethics.md` |
| Video: M1–M4 in order, results visible, log shown, ≤ 5:00 | `docs/video/script.md`, recorded video |
| I can explain and change every topic and the whole system | `docs/topics/`, `docs/qa/`, live-change drills practised |
| Optional voice/face: integrated, shown, tested, limits documented, text engine unaffected | Phases 7–8, regression tests with `audio_path=None` / `image_path=None` |

---

## 5. Explain mode (for the rest of the project)

Whenever I ask about any part of the system, answer in this order:
1. the course concept in two or three sentences;
2. where it lives in our code (file, function, config setting);
3. a worked example with real numbers produced by running our engine;
4. one change they could make and what would happen;
5. one question back to them to check understanding.

When asked to write report text or answers, provide a draft clearly marked as an AI draft and remind me to rewrite it in my own words and record it in the AI log.

**Start now with Phase 0.**
