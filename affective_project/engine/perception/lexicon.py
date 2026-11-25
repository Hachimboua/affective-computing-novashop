"""Load bundled VAD lexicons and match the longest phrase before single words."""
from dataclasses import dataclass
from functools import lru_cache
import math
from pathlib import Path
import unicodedata

from .. import config


LEXICON_DIR = Path(__file__).resolve().parent / "lexicons"
TIERED_HEADER = ("term", "tier", "v_override", "a_override", "d_override")


@dataclass(frozen=True)
class LexiconEntry:
    """A lexical term's tier-derived VAD values and optional tier name."""

    term: str
    valence: float
    activity: float
    dominance: float
    tier: str = ""


@dataclass(frozen=True)
class LexicalHit:
    """A matched term and its span in a clause's lexical-token sequence."""

    entry: LexiconEntry
    start: int
    end: int
    language: str


@dataclass
class Lexicons:
    words: dict
    phrases: dict
    emojis: dict


def _read_entries(path):
    entries = {}
    with path.open("r", encoding="utf-8") as stream:
        for line_number, raw_line in enumerate(stream, 1):
            line = raw_line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            if "?" in line or "\ufffd" in line:
                raise ValueError(
                    "%s:%d contains a question mark or replacement character."
                    % (path, line_number)
                )
            fields = line.split("\t")
            if len(fields) != 4:
                raise ValueError("%s:%d must contain term and three VAD values." % (path, line_number))
            term = unicodedata.normalize("NFKC", fields[0]).strip().lower()
            if not term or term in entries:
                raise ValueError("%s:%d has an empty or duplicate term." % (path, line_number))
            try:
                values = tuple(float(value) for value in fields[1:])
            except ValueError:
                raise ValueError("%s:%d has a non-numeric VAD value." % (path, line_number))
            if not all(math.isfinite(value) and -1.0 <= value <= 1.0 for value in values):
                raise ValueError("%s:%d VAD values must be finite and in [-1, 1]." % (path, line_number))
            entries[term] = LexiconEntry(term, values[0], values[1], values[2])
    return entries


def _read_tiered_entries(path):
    entries = {}
    with path.open("r", encoding="utf-8") as stream:
        for line_number, raw_line in enumerate(stream, 1):
            line = raw_line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            if "?" in line or "\ufffd" in line:
                raise ValueError(
                    "%s:%d contains a question mark or replacement character."
                    % (path, line_number)
                )
            fields = line.split("\t")
            if tuple(fields) == TIERED_HEADER:
                continue
            if len(fields) != 5:
                raise ValueError(
                    "%s:%d must contain term, tier, and three optional VAD overrides."
                    % (path, line_number)
                )
            term = unicodedata.normalize("NFKC", fields[0]).strip().lower()
            if not term or term in entries:
                raise ValueError("%s:%d has an empty or duplicate term." % (path, line_number))

            tier = fields[1].strip().upper()
            if tier not in config.TIER_VAD:
                raise ValueError("%s:%d has an unknown tier %r." % (path, line_number, tier))
            values = list(config.TIER_VAD[tier])
            for index, override in enumerate(fields[2:]):
                if override.strip():
                    try:
                        values[index] = float(override)
                    except ValueError:
                        raise ValueError(
                            "%s:%d has a non-numeric VAD override."
                            % (path, line_number)
                        )
            if not all(
                math.isfinite(value) and -1.0 <= value <= 1.0
                for value in values
            ):
                raise ValueError(
                    "%s:%d VAD values must be finite and in [-1, 1]."
                    % (path, line_number)
                )
            entries[term] = LexiconEntry(
                term, values[0], values[1], values[2], tier
            )
    return entries


@lru_cache(maxsize=1)
def load_lexicons():
    """Load local data once; no network or optional package is used."""
    words = {
        language: _read_tiered_entries(LEXICON_DIR / (language + ".tsv"))
        for language in ("en", "pt")
    }
    phrases = {
        language: _read_tiered_entries(
            LEXICON_DIR / ("phrases_" + language + ".tsv")
        )
        for language in ("en", "pt")
    }
    emojis = _read_entries(LEXICON_DIR / "emoji.tsv")
    return Lexicons(words=words, phrases=phrases, emojis=emojis)


def _language_choices(language):
    if language == "mixed":
        return ("en", "pt")
    if language in ("en", "pt"):
        return (language,)
    return ()


def match_clause(clause, language, lexicons=None):
    """Return phrase-first matches, preferring the longest phrase at each spot."""
    if lexicons is None:
        lexicons = load_lexicons()
    tokens = [
        token
        for token in clause.tokens
        if token.kind in ("word", "emoji", "emoticon")
    ]
    hits = []
    languages = _language_choices(language)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        phrase_match = None
        for candidate_language in languages:
            for term, entry in lexicons.phrases[candidate_language].items():
                phrase_tokens = term.split()
                end = index + len(phrase_tokens)
                if end <= len(tokens) and [
                    item.normalized for item in tokens[index:end]
                ] == phrase_tokens:
                    if phrase_match is None or len(phrase_tokens) > phrase_match[0]:
                        phrase_match = (len(phrase_tokens), entry, candidate_language)
        if phrase_match is not None:
            length, entry, candidate_language = phrase_match
            hits.append(LexicalHit(entry, index, index + length, candidate_language))
            index += length
            continue

        if token.kind in ("emoji", "emoticon") and token.normalized in lexicons.emojis:
            entry = lexicons.emojis[token.normalized]
            hits.append(LexicalHit(entry, index, index + 1, "emoji"))
        else:
            for candidate_language in languages:
                entry = lexicons.words[candidate_language].get(token.normalized)
                if entry is not None:
                    hits.append(
                        LexicalHit(entry, index, index + 1, candidate_language)
                    )
                    break
        index += 1
    return tokens, hits
