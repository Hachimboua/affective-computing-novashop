"""Shared, cached whole-word phrase matching for local rule lists."""
from functools import lru_cache
import re


def _phrase_key(phrases):
    return tuple(sorted(set(phrases), key=lambda phrase: (-len(phrase), phrase)))


@lru_cache(maxsize=128)
def _compile_phrases(phrases):
    alternatives = "|".join(re.escape(phrase) for phrase in phrases)
    return re.compile(r"(?<!\w)(?:" + alternatives + r")(?!\w)")


def contains_any(text, phrases):
    """Return whether normalized text contains any whole-word phrase."""
    key = _phrase_key(phrases)
    return bool(key and _compile_phrases(key).search(str(text)))


def matching_phrases(text, phrases):
    """Return the whole-word phrases found in normalized text."""
    key = _phrase_key(phrases)
    if not key:
        return set()
    return {match.group(0) for match in _compile_phrases(key).finditer(str(text))}
