"""Shared affective-engine weights and thresholds.

Keep tuning values here so students can change the behavior without hunting
through the text-processing pipeline.
"""

MIN_CONFIDENCE = 0.05  # Raising it hides more very-uncertain cases; lowering it exposes weaker estimates.
MAX_CONFIDENCE = 0.95  # Raising it permits stronger certainty claims; lowering it is more cautious.
LOW_CONFIDENCE_THRESHOLD = 0.35  # Raising it flags more estimates; lowering it reserves the flag for weaker evidence.
UNSUPPORTED_CONFIDENCE_CAP = 0.20  # Raising it trusts unsupported text more; lowering it favors clarification.
NEUTRAL_CONFIDENCE = 0.55  # Raising it trusts neutral intent more; lowering it treats neutral input as less certain.
SHORT_TOKEN_LIMIT = 2  # Raising it flags more short messages; lowering it misses terse ambiguity.
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
        "atrasado",
        "atrasada",
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
NEUTRAL_INTENT_MIN_TOKENS = 4  # Raising it requires more context for neutral intent; lowering it trusts shorter messages.
SARCASM_IDIOM_SCORE = 0.95  # Raising it makes idioms more decisive; lowering it treats idioms as weaker evidence.
SARCASM_INCONGRUITY_SCORE = 0.72  # Raising it requires stronger context-word mismatch; lowering it catches more possible sarcasm.
SARCASM_QUOTED_SCORE = 0.65  # Raising it trusts quotation as sarcasm evidence less; lowering it catches more quoted irony.
SARCASM_CONTEXT_SCORE = 0.55  # Raising it relies more on conversation context; lowering it requires stronger direct cues.
