"""Unicode text normalization, tokenization, elongation, and clause splitting."""
from dataclasses import dataclass
import re
import unicodedata

from .. import config


_TOKEN_RE = re.compile(
    r"(?:[:;=8][-^']?[)(/DPp]|[xX][dD])"
    r"|[\U0001F300-\U0001FAFF\u2600-\u27BF](?:\uFE0F)?"
    r"|[^\W\d_]+(?:['’][^\W\d_]+)*"
    r"|\d+"
    r"|[!?.,;:]+"
    r"|[^\s]",
    re.UNICODE,
)
_ELONGATION_RE = re.compile(r"([^\W\d_])\1{2,}", re.UNICODE | re.IGNORECASE)
_WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*\Z", re.UNICODE)
_EMOTICON_RE = re.compile(r"(?:[:;=8][-^']?[)(/DPp]|[xX][dD])\Z")


@dataclass
class Token:
    """One visible token and the normalized form used for lexicon lookup."""

    text: str
    normalized: str
    kind: str
    is_upper: bool
    elongated: bool


@dataclass
class Clause:
    """A token group separated by sentence punctuation or contrast."""

    tokens: list
    follows_contrast: bool


@dataclass
class ProcessedText:
    """Preprocessed message plus cues preserved from the original form."""

    original: str
    normalized: str
    tokens: list
    clauses: list
    flags: list


def _collapse_elongation(text):
    return _ELONGATION_RE.sub(r"\1", text)


def _make_token(match):
    text = match.group(0)
    lowered = text.lower().replace("’", "'")
    normalized = _collapse_elongation(lowered)
    if _EMOTICON_RE.fullmatch(text):
        kind = "emoticon"
    elif any(ord(char) >= 0x1F300 or 0x2600 <= ord(char) <= 0x27BF for char in text):
        kind = "emoji"
    elif _WORD_RE.fullmatch(text):
        kind = "word"
    elif text.isdigit():
        kind = "number"
    elif all(char in "!?.,;:" for char in text):
        kind = "punctuation"
    else:
        kind = "symbol"
    letters = [char for char in text if char.isalpha()]
    return Token(
        text=text,
        normalized=normalized,
        kind=kind,
        is_upper=bool(letters) and text.isupper(),
        elongated=_ELONGATION_RE.search(text) is not None,
    )


def _split_clauses(tokens):
    clauses = []
    current = []
    follows_contrast = False
    index = 0

    def finish():
        nonlocal current, follows_contrast
        if current:
            clauses.append(Clause(current, follows_contrast))
            current = []

    while index < len(tokens):
        token = tokens[index]
        if token.kind == "punctuation" and any(char in token.text for char in ".!?;"):
            finish()
            index += 1
            continue
        if token.kind == "word":
            word = token.normalized
            if word == "no" and index + 1 < len(tokens):
                if tokens[index + 1].normalized == "entanto":
                    finish()
                    follows_contrast = True
                    index += 2
                    continue
            if word in config.CONTRAST_WORDS:
                finish()
                follows_contrast = True
                index += 1
                continue
        current.append(token)
        index += 1
    finish()
    return clauses


def preprocess(text):
    """Normalize text while retaining original cues needed for affect rules."""
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    original = unicodedata.normalize("NFKC", text)
    matches = list(_TOKEN_RE.finditer(original))
    tokens = [_make_token(match) for match in matches]
    normalized = _collapse_elongation(original.lower())
    word_count = sum(token.kind == "word" for token in tokens)
    flags = []
    if any(token.elongated for token in tokens):
        flags.append("elongation")
    if word_count <= config.SHORT_TOKEN_LIMIT:
        flags.append("short_message")
    if not original.strip():
        flags.append("empty")
    return ProcessedText(
        original=original,
        normalized=normalized,
        tokens=tokens,
        clauses=_split_clauses(tokens),
        flags=flags,
    )
