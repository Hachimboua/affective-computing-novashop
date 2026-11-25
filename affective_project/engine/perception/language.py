"""Lightweight language and script identification for supported text."""
import unicodedata

from .. import config
from .lexicon import load_lexicons


SUPPORTED_LANGUAGES = ("en", "pt")
STOPWORDS = {
    "en": frozenset(
        (
            "a",
            "about",
            "am",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "been",
            "but",
            "can",
            "do",
            "does",
            "for",
            "from",
            "have",
            "how",
            "i",
            "if",
            "in",
            "is",
            "it",
            "me",
            "my",
            "no",
            "not",
            "of",
            "on",
            "or",
            "our",
            "please",
            "the",
            "this",
            "to",
            "was",
            "we",
            "what",
            "when",
            "where",
            "with",
            "you",
            "your",
        )
    ),
    "pt": frozenset(
        (
            "a",
            "ao",
            "aos",
            "as",
            "com",
            "como",
            "da",
            "das",
            "de",
            "do",
            "dos",
            "e",
            "é",
            "em",
            "estou",
            "eu",
            "foi",
            "me",
            "minha",
            "não",
            "no",
            "o",
            "os",
            "para",
            "por",
            "que",
            "se",
            "um",
            "uma",
            "você",
        )
    ),
}
UNSUPPORTED_LATIN_STOPWORDS = {
    "de": frozenset(
        ("ich", "bin", "der", "die", "das", "und", "nicht", "ist", "mit", "mein")
    ),
    "es": frozenset(
        ("el", "la", "los", "las", "mi", "pedido", "quiero", "gracias", "está", "no")
    ),
    "fr": frozenset(
        (
            "le",
            "la",
            "les",
            "mon",
            "ma",
            "merci",
            "commande",
            "est",
            "pas",
            "je",
            "suis",
        )
    ),
    "nl": frozenset(
        ("ik", "ben", "de", "het", "een", "en", "niet", "mijn", "met", "voor")
    ),
}
PORTUGUESE_HINTS = frozenset(
    (
        "obrigado",
        "obrigada",
        "encomenda",
        "chegou",
        "reembolso",
        "ajudem",
        "ajuda",
        "atrasado",
        "atrasada",
        "ficou",
        "apoio",
        "pagamento",
        "posso",
        "têm",
        "loja",
        "física",
    )
)
SCRIPT_LANGUAGE = {
    "CYRILLIC": "ru",
    "ARABIC": "ar",
    "CJK": "zh",
    "HIRAGANA": "ja",
    "KATAKANA": "ja",
    "HANGUL": "ko",
    "GREEK": "el",
    "HEBREW": "he",
    "DEVANAGARI": "hi",
    "THAI": "th",
}


def _letter_script(char):
    try:
        name = unicodedata.name(char)
    except ValueError:
        return "UNKNOWN"
    if "LATIN" in name:
        return "LATIN"
    for marker, language in SCRIPT_LANGUAGE.items():
        if marker in name:
            return language.upper()
    return "OTHER"


def _word_sequences(tokens):
    sequences = []
    current = []
    for token in tokens:
        if token.kind == "word":
            current.append(token.normalized)
        elif current:
            sequences.append(current)
            current = []
    if current:
        sequences.append(current)
    return sequences


def _contains_sequence(sequence, phrase):
    size = len(phrase)
    return any(
        sequence[index : index + size] == phrase
        for index in range(len(sequence) - size + 1)
    )


def _lexicon_scores(tokens, words):
    lexicons = load_lexicons()
    scores = {"en": 0, "pt": 0}
    for word in words:
        matches = [
            language
            for language in SUPPORTED_LANGUAGES
            if word in lexicons.words[language]
        ]
        if len(matches) == 1:
            scores[matches[0]] += 1
        if word in PORTUGUESE_HINTS and "pt" not in matches:
            scores["pt"] += 1

    phrase_sequences = _word_sequences(tokens)
    for language in SUPPORTED_LANGUAGES:
        other_language = "pt" if language == "en" else "en"
        other_phrases = lexicons.phrases[other_language]
        for phrase in lexicons.phrases[language]:
            if phrase in other_phrases:
                continue
            phrase_words = phrase.split()
            if any(
                _contains_sequence(sequence, phrase_words)
                for sequence in phrase_sequences
            ):
                scores[language] += 1
    return scores


def identify_language(tokens):
    """Combine script, stopword, and distinctive lexicon evidence."""
    words = [token.normalized for token in tokens if token.kind == "word"]
    scripts = [_letter_script(char) for word in words for char in word if char.isalpha()]
    if not scripts:
        if len(words) <= config.SHORT_TOKEN_LIMIT:
            return "unknown", config.LANG_UNKNOWN_CONFIDENCE, []
        return "unknown", config.LANG_UNKNOWN_CONFIDENCE, ["unsupported_language"]

    script_language = None
    non_latin = [script for script in scripts if script != "LATIN"]
    if non_latin:
        strongest = max(sorted(set(non_latin)), key=non_latin.count)
        script_language = strongest.lower()
        if len(non_latin) < len(scripts) * config.LANG_NONLATIN_FRACTION:
            script_language = None

    shared = STOPWORDS["en"].intersection(STOPWORDS["pt"])
    stopword_scores = {
        language: sum(word in stopwords.difference(shared) for word in words)
        for language, stopwords in STOPWORDS.items()
    }
    lexicon_scores = _lexicon_scores(tokens, words)
    supported_scores = {
        language: stopword_scores[language] + lexicon_scores[language]
        for language in SUPPORTED_LANGUAGES
    }
    short_latin_message = (
        len(words) <= config.SHORT_TOKEN_LIMIT
        and all(script == "LATIN" for script in scripts)
    )
    if short_latin_message and not any(supported_scores.values()):
        return "unknown", config.LANG_UNKNOWN_CONFIDENCE, []

    unsupported_scores = {
        language: sum(word in stopwords for word in words)
        for language, stopwords in UNSUPPORTED_LATIN_STOPWORDS.items()
    }
    unsupported_language = max(unsupported_scores, key=unsupported_scores.get)
    unsupported_hits = unsupported_scores[unsupported_language]
    unsupported_without_supported_language_cues = (
        unsupported_hits > 0
        and stopword_scores["en"] == 0
        and supported_scores["pt"] == 0
    )
    if unsupported_without_supported_language_cues:
        return (
            unsupported_language,
            config.LANG_UNSUPPORTED_LATIN_CONFIDENCE,
            ["unsupported_language"],
        )
    if unsupported_hits > max(supported_scores.values()):
        return (
            unsupported_language,
            config.LANG_UNSUPPORTED_LATIN_CONFIDENCE,
            ["unsupported_language"],
        )

    if not any(stopword_scores.values()) and not any(lexicon_scores.values()):
        if script_language:
            return script_language, config.LANG_UNSUPPORTED_CONFIDENCE, ["unsupported_language"]
        return "unknown", config.LANG_UNSUPPORTED_LATIN_CONFIDENCE, ["unsupported_language"]

    if supported_scores["en"] and supported_scores["pt"]:
        return "mixed", config.LANG_MIXED_CONFIDENCE, ["mixed_language"]

    language = "pt" if supported_scores["pt"] else "en"
    evidence_count = supported_scores[language]
    confidence = min(
        config.LANG_MAX_CONFIDENCE,
        config.LANG_SUPPORTED_BASE_CONFIDENCE
        + config.LANG_STOPWORD_CONFIDENCE_STEP * evidence_count,
    )
    if language == "pt" and any(word in PORTUGUESE_HINTS for word in words):
        confidence = max(confidence, config.LANG_PORTUGUESE_HINT_CONFIDENCE)
    return language, confidence, []
