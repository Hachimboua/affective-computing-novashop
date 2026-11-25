"""Shared affective-engine weights and thresholds.

Keep tuning values here so students can change the behavior without hunting
through the text-processing pipeline.
"""

MIN_CONFIDENCE = 0.05  # Raising it hides more very-uncertain cases; lowering it exposes weaker estimates.
MAX_CONFIDENCE = 0.95  # Raising it permits stronger certainty claims; lowering it is more cautious.
LOW_CONFIDENCE_THRESHOLD = 0.35  # Raising it flags more estimates; lowering it reserves the flag for weaker evidence.
TEXT_LATENCY_BUDGET_SECONDS = 0.10  # Raising it tolerates slower machines; lowering it demands faster processing.
HIDDEN_REHEARSAL_MIN_PASS_RATE = 0.90  # Raising it demands broader reliability; lowering it accepts more rehearsal misses.
DETAILS_EVIDENCE_LIMIT = 2  # Raising it logs more term evidence; lowering it keeps session details shorter.
VOICE_ENABLED = True  # Turning it off ignores supplied audio; turning it on enables optional voice fusion.
VOICE_FRAME_MS = 25  # Raising it improves low-frequency detail but blurs short changes; lowering it increases detail and noise.
VOICE_HOP_MS = 10  # Raising it reduces work but misses timing detail; lowering it adds computation.
VOICE_PREEMPHASIS = 0.97  # Raising it emphasizes high frequencies more; lowering it preserves more low-frequency energy.
VOICE_MEL_FILTERS = 26  # Raising it keeps finer spectral detail but adds computation; lowering it smooths the spectrum.
VOICE_MFCC_COUNT = 13  # Raising it retains more timbre detail; lowering it compresses the representation further.
VOICE_MIN_PITCH_HZ = 75.0  # Lowering it supports lower voices but increases octave errors.
VOICE_MAX_PITCH_HZ = 500.0  # Raising it supports higher voices but increases false pitch detections.
VOICE_AUTOCORRELATION_MIN = 0.25  # Raising it rejects uncertain pitch more; lowering it accepts noisier F0 estimates.
VOICE_VOICED_ENERGY_FLOOR_DB = -50.0  # Raising it rejects more quiet frames; lowering it admits quieter speech and noise.
VOICE_MAX_ZCR_HZ = 4000.0  # Lowering it rejects more noisy frames; raising it accepts noisier high-frequency frames.
VOICE_SILENCE_DB = -55.0  # Raising it treats more quiet clips as silence; lowering it detects quieter speech.
VOICE_MIN_VOICED_RATIO = 0.10  # Raising it needs more speech-like frames; lowering it accepts sparse voicing.
VOICE_CLIP_LEVEL = 0.98  # Lowering it penalizes near-clipping sooner; raising it tolerates louder peaks.
VOICE_MIN_DURATION_SECONDS = 1.0  # Raising it requires longer clips for full confidence; lowering it trusts shorter clips.
VOICE_FULL_VOICED_RATIO = 0.50  # Raising it needs more speech-like frames for full confidence; lowering it trusts sparse voicing.
VOICE_MIN_SNR_DB = 0.0  # Raising it reduces confidence in noisier audio; lowering it trusts poorer SNR.
VOICE_MAX_SNR_DB = 30.0  # Lowering it reaches maximum confidence sooner; raising it requires cleaner audio.
VOICE_CONFIDENCE_MAX = 0.90  # Raising it trusts voice evidence more; lowering it keeps voice estimates conservative.
VOICE_CLIPPING_PENALTY = 2.0  # Raising it penalizes clipped samples more; lowering it tolerates louder peaks.
VOICE_REFERENCE_STD_FLOOR = 0.10  # Raising it reduces extreme z-scores; lowering it makes narrow reference ranges more influential.
VOICE_ACTIVITY_ENERGY_WEIGHT = 0.65  # Raising it ties activity more to loudness; lowering it relies more on pitch variation and rate.
VOICE_ACTIVITY_PITCH_WEIGHT = 0.20  # Raising it relies more on pitch variability; lowering it reduces speaker-style influence.
VOICE_ACTIVITY_RATE_WEIGHT = 0.15  # Raising it relies more on voiced-segment rate; lowering it reduces segmentation influence.
VOICE_ACTIVITY_Z_SCALE = 0.35  # Raising it expands voice activity scores; lowering it keeps them nearer neutral.
TEXT_VALENCE_WEIGHT = 0.90  # Raising it makes text dominate valence more; lowering it gives voice more influence.
VOICE_VALENCE_WEIGHT = 0.10  # Raising it increases uncertain prosody influence; lowering it keeps voice valence weaker.
TEXT_ACTIVITY_WEIGHT = 0.40  # Raising it makes text dominate activity more; lowering it gives voice more influence.
VOICE_ACTIVITY_WEIGHT = 0.60  # Raising it makes voice contribute more activity; lowering it favors text.
TEXT_DOMINANCE_WEIGHT = 0.95  # Raising it keeps dominance more text-based; lowering it gives voice more influence.
VOICE_DOMINANCE_WEIGHT = 0.05  # Raising it increases uncertain voice dominance influence; lowering it keeps it weaker.
VOICE_CONFIDENCE_WEIGHT = 0.20  # Raising it lets audio quality move fused confidence more; lowering it favors text confidence.
VOICE_AGREEMENT_BONUS = 0.08  # Raising it rewards agreeing modalities more; lowering it reduces the agreement bonus.
VOICE_CONFLICT_PENALTY = 0.15  # Raising it lowers confidence more on disagreement; lowering it tolerates conflicts.
VOICE_VALENCE_CONFIDENCE_FACTOR = 0.30  # Raising it trusts weak voice valence more; lowering it further limits its influence.
VOICE_FLAT_ACTIVITY_THRESHOLD = -0.60  # Raising it flags more calm prosody as conflicting with positive text.
SARCASM_MODALITY_CONFLICT_BONUS = 0.10  # Raising it lets cross-modal conflict raise sarcasm more; lowering it is more cautious.
UNSUPPORTED_CONFIDENCE_CAP = 0.20  # Raising it trusts unsupported text more; lowering it favors clarification.
NEUTRAL_CONFIDENCE = 0.55  # Raising it trusts neutral intent more; lowering it treats neutral input as less certain.
SHORT_TOKEN_LIMIT = 2  # Raising it flags more short messages; lowering it misses terse ambiguity.
SHOUTED_MESSAGE_MAX_TOKENS = 4  # Raising it treats longer emphatic turns as short shouts; lowering it narrows context overrides.
SHORT_CONFIDENCE_FACTOR = 0.55  # Raising it penalizes short text less; lowering it asks for clarification more often.
UNKNOWN_TOKEN_PENALTY = 0.25  # Raising it penalizes unknown vocabulary more; lowering it tolerates unseen words.
MIXED_LANGUAGE_CONFIDENCE_FACTOR = 0.75  # Raising it trusts mixed text more; lowering it favors a clarification.
SARCASM_CONFIDENCE_FACTOR = 0.70  # Raising it penalizes sarcasm less; lowering it signals greater uncertainty.
EVIDENCE_SATURATION_RATE = 0.70  # Raising it reaches confidence faster; lowering it needs more affective evidence.
EVIDENCE_AGREEMENT_PENALTY = 0.30  # Raising it punishes conflicting cues more; lowering it tolerates mixed signals.

NEGATION_FACTOR = -0.60  # More negative strengthens the polarity shift; closer to zero makes negation milder.
NEGATION_ACTIVITY_FACTOR = 0.80  # Raising it preserves activity under negation; lowering it dampens more.
NEGATION_SCOPE = 3  # Raising it reaches farther back; lowering it reduces accidental negation scope.
NEGATORS = {
    "en": frozenset(
        ("not", "no", "never", "nothing", "without", "hardly", "neither", "nor")
    ),
    "pt": frozenset(("não", "nunca", "nada", "sem", "nem", "jamais")),
}
NEGATION_SUFFIXES = ("n't",)

# Raising an intensifier multiplier strengthens emotion and may saturate scores;
# lowering it makes emphasis easier to miss. Downtoners use the inverse trade-off.
INTENSIFIERS = {
    "en": {
        "very": 1.30,
        "really": 1.25,
        "so": 1.30,
        "extremely": 1.60,
        "absolutely": 1.50,
        "totally": 1.40,
        "incredibly": 1.50,
    },
    "pt": {
        "muito": 1.30,
        "mesmo": 1.25,
        "tão": 1.30,
        "extremamente": 1.60,
        "absolutamente": 1.50,
        "totalmente": 1.40,
    },
}
DOWNTONERS = {
    "en": {
        "slightly": 0.50,
        "a bit": 0.60,
        "kind of": 0.70,
        "somewhat": 0.70,
        "rather": 0.80,
    },
    "pt": {
        "ligeiramente": 0.50,
        "um pouco": 0.60,
        "mais ou menos": 0.70,
        "meio": 0.70,
    },
}

CONTRAST_WORDS = frozenset(
    (
        "but",
        "however",
        "although",
        "though",
        "yet",
        "mas",
        "porém",
        "contudo",
        "embora",
        "todavia",
    )
)
CONTRAST_EARLIER_WEIGHT = 0.30  # Raising it gives the first clause more say; lowering it emphasizes the contrast clause.
CONTRAST_LATER_WEIGHT = 0.70  # Raising it emphasizes the post-contrast clause; lowering it preserves earlier context.
MIXED_EMOTION_MIN_MAGNITUDE = 0.12  # Raising it ignores weaker conflicts; lowering it flags subtler mixed emotion.

EXCLAMATION_ACTIVITY = 0.08  # Raising it makes exclamations more activating; lowering it is more punctuation-cautious.
EXCLAMATION_VALENCE_AMPLIFIER = 0.04  # Raising it boosts expressed polarity; lowering it reduces punctuation influence.
QUESTION_ACTIVITY = 0.04  # Raising it treats repeated questions as more activated; lowering it is more neutral.
ELLIPSIS_ACTIVITY = -0.08  # More negative calms hesitant text more; closer to zero makes ellipses matter less.
CAPS_AMPLIFIER = 1.15  # Raising it amplifies all-caps affect words; lowering it reduces shouting influence.
CAPS_WORD_ACTIVITY = 0.08  # Raising it adds more activation per capitalized word; lowering it softens that cue.
CAPS_MESSAGE_ACTIVITY = 0.12  # Raising it emphasizes whole-message shouting; lowering it reduces message-level effect.
CAPS_MIN_LENGTH = 3  # Raising it ignores more short acronyms; lowering it treats shorter uppercase words as emphasis.
ELONGATION_ACTIVITY = 0.05  # Raising it treats stretched spelling as more activated; lowering it discounts elongation.
BASELINE_ACTIVITY = -0.04  # More negative assumes calmer neutral text; closer to zero removes that calm prior.

REPETITION_VALENCE = -0.12  # More negative penalizes repeated problems more; closer to zero reduces persistence bias.
REPETITION_ACTIVITY = 0.10  # Raising it activates repeated complaints more; lowering it treats repetition as less urgent.
URGENCY_ACTIVITY = 0.18  # Raising it makes urgency stronger; lowering it reduces false urgency escalations.
URGENCY_DOMINANCE = 0.12  # Raising it reads urgency as more assertive; lowering it keeps dominance more neutral.
DEMAND_DOMINANCE = 0.18  # Raising it treats demands as more controlling; lowering it reduces assertiveness bias.
HELPLESSNESS_DOMINANCE = -0.20  # More negative lowers perceived control more; closer to zero is more conservative.
PROFANITY_VALENCE = -0.18  # More negative penalizes profanity more; closer to zero reduces dialect/profanity bias.
PROFANITY_ACTIVITY = 0.18  # Raising it activates profanity more; lowering it avoids overreacting to casual slang.

SARCASM_THRESHOLD = 0.60  # Lower catches more sarcasm but risks false positives; higher misses subtle cases.
SARCASM_POSITIVE_INVERSION = -0.80  # More negative reverses positive wording more; closer to zero keeps literal positivity.
SARCASM_POSITIVE_MIN = 0.15  # Raising it requires stronger positive wording; lowering it increases incongruity triggers.
SARCASM_CONTEXT_VALENCE = -0.50  # More negative requires worse context; raising it uses context more readily.
DOMAIN_NEGATIVE_TERMS = frozenset(
    (
        "late",
        "delay",
        "delayed",
        "broken",
        "damaged",
        "missing",
        "failed",
        "failure",
        "lost",
        "wrong",
        "cracked",
        "defective",
        "not arrived",
        "never arrive",
        "never arrived",
        "never be delivered",
        "not delivered",
        "supposed to be here",
        "atrasado",
        "atrasada",
        "nunca chega",
        "nunca chegou",
        "não foi entregue",
        "partido",
        "danificado",
        "perdido",
        "errado",
    )
)
SARCASM_NEGATIVE_EVENT_TERMS = DOMAIN_NEGATIVE_TERMS | frozenset(
    (
        "break",
        "breaks",
        "breaking",
        "broke",
        "stopped working",
        "never arrived",
        "never got here",
        "did not arrive",
        "didn't arrive",
        "partida",
        "quebra",
        "quebrou",
        "quebrado",
        "quebrada",
        "parou de funcionar",
        "não funciona",
        "nunca chegou",
    )
)
SARCASM_IDIOMS = {
    "en": frozenset(
        (
            "thanks for nothing",
            "yeah right",
            "oh great",
            "just perfect",
            "what a surprise",
            "just what i needed",
            "love that for me",
            "couldn't be better",
            "what could possibly go wrong",
            "fantastic timing",
            "well that's just great",
        )
    ),
    "pt": frozenset(
        (
            "obrigado por nada",
            "que surpresa",
            "perfeito mesmo",
            "era só o que faltava",
            "era mesmo o que faltava",
            "só que não",
            "nem podia ser melhor",
            "que maravilha",
        )
    ),
}
SARCASM_REPETITION_CUES = frozenset(("again", "another", "still"))
QUOTED_POSITIVE_TERMS = frozenset(
    ("fast", "quick", "perfect", "great", "excellent", "rápido", "perfeito")
)

REPETITION_CUES = frozenset(("again", "yet another", "third time", "once again"))
REPETITION_CONTEXT_TERMS = frozenset(
    ("still", "yet", "again", "atrasado", "atrasada", "pendente")
)
URGENCY_CUES = frozenset(
    ("asap", "now", "immediately", "urgent", "urgently", "hoje", "agora", "urgente")
)
DEMAND_CUES = frozenset(
    ("demand", "demanding", "require", "exijo", "exigir", "quero")
)
HELPLESSNESS_CUES = frozenset(
    ("please help", "i am lost", "i'm lost", "don't know what to do", "não sei o que fazer")
)
PROFANITY_TERMS = frozenset(
    ("damn", "hell", "shit", "crap", "bloody", "caralho", "merda", "porra")
)
HUMAN_REQUEST_CUES = frozenset(
    (
        "real person",
        "human",
        "human agent",
        "speak to a person",
        "talk to a person",
        "manager",
        "supervisor",
        "real atendente",
        "agente humano",
        "pessoa real",
    )
)
ESCALATION_CUES = frozenset(
    (
        "lawyer",
        "sue",
        "chargeback",
        "consumer protection",
        "report you",
        "court",
        "law",
        "never buying again",
        "advogado",
        "tribunal",
        "proteção do consumidor",
        "reclamação formal",
    )
)
SAFETY_CUES = frozenset(
    (
        "hurt myself",
        "harm myself",
        "kill myself",
        "end my life",
        "suicide",
        "magoar-me",
        "fazer mal a mim próprio",
        "acabar com a minha vida",
    )
)
ABUSE_CUES = frozenset(
    (
        "i will hurt you",
        "i'll hurt you",
        "you are an idiot",
        "you're an idiot",
        "you are useless",
        "vou fazer mal a ti",
        "vou magoar-te",
        "és um idiota",
    )
)
HUMAN_DECLINED_CUES = frozenset(
    (
        "no thanks",
        "not now",
        "i do not want a human",
        "i don't want a human",
        "i do not want a person",
        "não quero uma pessoa",
        "não quero um agente",
        "não é necessário",
    )
)
AMBIGUOUS_CUES = frozenset(
    (
        "ok",
        "okay",
        "whatever",
        "?",
        "hmm",
        "cannot follow",
        "clearer",
        "more context",
        "unsure",
    )
)
ACKNOWLEDGMENT_CUES = frozenset(("ok", "okay", "thanks", "thank you", "obrigado", "obrigada"))
RESOLUTION_CUES = frozenset(
    (
        "that solved it",
        "problem is solved",
        "it is resolved",
        "all sorted",
        "that is all",
        "that's all",
        "ficou tudo resolvido",
        "está tudo resolvido",
        "problema resolvido",
    )
)

SQUASH_SCALE = 1.15  # Raising it pushes estimates toward extremes sooner; lowering it keeps values near zero.
TIER_VAD = {
    "ANGER_STRONG": (-0.85, 0.80, 0.40),
    "ANGER": (-0.70, 0.60, 0.30),
    "FRUSTRATION": (-0.55, 0.35, 0.10),
    "PROBLEM_MILD": (-0.35, 0.15, 0.00),
    "PROBLEM": (-0.50, 0.20, 0.00),
    "FEAR": (-0.60, 0.55, -0.50),
    "SADNESS": (-0.60, -0.35, -0.35),
    "FATIGUE": (-0.45, -0.60, -0.30),
    "NEUTRAL": (0.00, 0.00, 0.00),
    "CONTENT": (0.45, -0.45, 0.25),
    "POSITIVE": (0.50, 0.10, 0.25),
    "JOY": (0.80, 0.55, 0.40),
}
LABEL_D_WEIGHT = 0.50  # Raising it lets perceived control affect labels more; lowering it emphasizes valence and activity.
LABEL_NEUTRAL_RADIUS = 0.18  # Raising it selects neutral more often; lowering it assigns emotion labels more readily.
LABEL_PROTOTYPES = {
    "anger": (-0.70, 0.60, 0.30),
    "frustration": (-0.55, 0.35, 0.10),
    "fear": (-0.60, 0.55, -0.50),
    "sadness": (-0.60, -0.40, -0.35),
    "calm": (0.40, -0.45, 0.25),
    "joy": (0.75, 0.50, 0.40),
    "neutral": (0.00, 0.00, 0.00),
}
STATE_ALPHA = 0.50  # Raising it reacts faster but is noisier; lowering it is steadier but lags.
STATE_HISTORY_SIZE = 8  # Raising it preserves more context; lowering it limits old turns' influence.
STATE_TREND_WINDOW = 4  # Raising it smooths trends but reacts later; lowering it reacts faster but noisier.
TREND_WORSENING_THRESHOLD = -0.08  # More negative needs a sharper decline; closer to zero offers help sooner.
NEG_TURN_V = -0.25  # More negative counts fewer turns as complaints; closer to zero counts milder concerns.
ESC_V = -0.65  # More negative escalates less often; closer to zero catches severe states sooner.
ESC_A = 0.55  # Raising it requires more activation; lowering it increases urgent handoffs.
ESC_TURNS = 2  # Raising it needs longer persistence; lowering it reacts to shorter severe episodes.
ESC_NEG_STREAK = 4  # Raising it tolerates longer complaint streaks; lowering it escalates sooner.
HUMAN_V = -0.45  # More negative delays offers; closer to zero offers a person for milder distress.
HUMAN_STREAK = 3  # Raising it needs more negative turns; lowering it offers a person sooner.
REPEATED_ISSUE_MIN = 2  # Raising it waits for more repeated issues; lowering it may over-offer.
DOMAIN_PROBLEM_VALENCE = -0.25  # More negative strengthens missed-service cues; closer to zero is more conservative.
HUMAN_OFFER_COOLDOWN_TURNS = 2  # Raising it avoids repeated offers longer; lowering it permits quicker reminders.
CLARIFY_CONF = 0.35  # Raising it asks more clarifying questions; lowering it answers on weaker evidence.
MAX_CLARIFY = 2  # Raising it permits longer loops; lowering it offers a human sooner.
EMPATHY_V = -0.25  # More negative enters empathy less often; closer to zero uses empathy more readily.
EMPATHY_EXIT_V = -0.15  # Raising it exits empathy sooner; lowering it keeps an empathetic tone longer.
EMPATHY_MSG_V = -0.35  # More negative needs stronger message negativity; closer to zero is more responsive.
EMPATHY_A = 0.55  # Raising it needs stronger activation; lowering it empathizes with calmer complaints.
CLOSE_V = 0.35  # Raising it requires stronger positivity; lowering it risks premature conversation closure.
WORD_SALIENCE = 1.00  # Raising it gives single words more influence; lowering it favors message-level cues.
PHRASE_SALIENCE = 1.25  # Raising it trusts multiword cues more; lowering it reduces phrase dominance.

LANG_UNKNOWN_CONFIDENCE = 0.10  # Raising it trusts unidentified text more; lowering it encourages clarification.
LANG_UNSUPPORTED_CONFIDENCE = 0.15  # Raising it trusts unsupported scripts more; lowering it is more cautious.
LANG_UNSUPPORTED_LATIN_CONFIDENCE = 0.18  # Raising it trusts unsupported Latin languages more; lowering it caps them harder.
LANG_NONLATIN_FRACTION = 0.50  # Raising it needs more non-Latin letters to classify; lowering it flags mixed scripts sooner.
LANG_SUPPORTED_BASE_CONFIDENCE = 0.55  # Raising it trusts one supported-language cue more; lowering it requires more evidence.
LANG_STOPWORD_CONFIDENCE_STEP = 0.10  # Raising it increases confidence per stop word; lowering it slows confidence growth.
LANG_MAX_CONFIDENCE = 0.95  # Raising it allows stronger language certainty; lowering it avoids overclaiming.
LANG_PORTUGUESE_HINT_CONFIDENCE = 0.60  # Raising it trusts unique Portuguese terms more; lowering it avoids false language calls.
LANG_MIXED_CONFIDENCE = 0.50  # Raising it trusts mixed-language cues more; lowering it favors clarification.
LANG_LEXICON_EVIDENCE_FLOOR = 0.65  # Raising it trusts a matched supported-language term more; lowering it preserves language uncertainty.
UNKNOWN_WORD_CONFIDENCE_FLOOR = 0.50  # Raising it limits the unknown-word penalty; lowering it penalizes unfamiliar text more.
NEUTRAL_INTENT_MIN_TOKENS = 3  # Raising it requires more context for neutral evidence; lowering it trusts shorter text.
SARCASM_IDIOM_SCORE = 0.95  # Raising it makes idioms more decisive; lowering it treats idioms as weaker evidence.
SARCASM_INCONGRUITY_SCORE = 0.72  # Raising it requires stronger context-word mismatch; lowering it catches more possible sarcasm.
SARCASM_QUOTED_SCORE = 0.65  # Raising it trusts quotation as sarcasm evidence less; lowering it catches more quoted irony.
SARCASM_CONTEXT_SCORE = 0.55  # Raising it relies more on conversation context; lowering it requires stronger direct cues.
EMPATHY_NEGATIVE_V = 0.0  # Lowering requires stronger negativity; raising empathizes at weaker negative valence.
POSITIVE_FEEDBACK_V = 0.60  # Raising it requires stronger positive evidence to skip clarification; lowering answers more uncertain praise.
