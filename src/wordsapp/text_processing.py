"""Helpers for processing user texts into highlighted segments."""

from __future__ import annotations

import re
from typing import TypedDict

import simplemma

from wordsapp.models import Record, StudyLanguage, User

WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)
ENGLISH_CONTRACTION_SUFFIXES = ("n't", "'re", "'ve", "'ll", "'d", "'m")
ENGLISH_S_CONTRACTION_BASES = frozenset(
    {
        "he",
        "here",
        "how",
        "it",
        "she",
        "that",
        "there",
        "what",
        "when",
        "where",
        "who",
        "why",
    }
)
ENGLISH_IRREGULAR_CONTRACTIONS = frozenset({"ain't", "let's", "shan't", "won't"})
ARTICLE_TOKENS_BY_LANGUAGE: dict[str, frozenset[str]] = {
    StudyLanguage.ENGLISH: frozenset({"a", "an", "the"}),
    StudyLanguage.FRENCH: frozenset(
        {"le", "la", "les", "l'", "un", "une", "des", "du", "au", "aux"}
    ),
}
FRENCH_CONTRACTION_PREFIXES = frozenset({"c'", "d'", "j'", "m'", "n'", "qu'", "s'", "t'"})
FRENCH_ELIDED_PREFIXES = tuple(
    sorted({"l'"} | FRENCH_CONTRACTION_PREFIXES, key=len, reverse=True)
)
NUMBER_WORDS_BY_LANGUAGE: dict[str, frozenset[str]] = {
    StudyLanguage.ENGLISH: frozenset(
        {
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
            "twenty",
            "thirty",
            "forty",
            "fifty",
            "sixty",
            "seventy",
            "eighty",
            "ninety",
            "hundred",
            "thousand",
            "million",
        }
    ),
    StudyLanguage.FRENCH: frozenset(
        {
            "zero",
            "zéro",
            "un",
            "deux",
            "trois",
            "quatre",
            "cinq",
            "six",
            "sept",
            "huit",
            "neuf",
            "dix",
            "onze",
            "douze",
            "treize",
            "quatorze",
            "quinze",
            "seize",
            "vingt",
            "trente",
            "quarante",
            "cinquante",
            "soixante",
            "cent",
            "mille",
            "million",
        }
    ),
}


class TextPlainSegment(TypedDict):
    """A plain-text segment."""

    type: str
    value: str


class TextMatchSegment(TypedDict):
    """A highlighted segment."""

    type: str
    value: str
    normalized: str
    match_kind: str
    record_id: int | None


TextSegment = TextPlainSegment | TextMatchSegment


def normalize_token(token: str) -> str:
    """Normalize a token for non-lemma comparisons."""
    return token.casefold().replace("’", "'")


def normalize_word(token: str, language: str) -> str:
    """Return the lemma used for matching stored words."""
    return str(simplemma.lemmatize(token.casefold(), lang=language)).casefold()


def split_french_token(token: str) -> list[str]:
    """Split French elided prefixes from the following word when possible."""
    normalized_token = normalize_token(token)
    for prefix in FRENCH_ELIDED_PREFIXES:
        if normalized_token.startswith(prefix) and len(token) > len(prefix):
            return [token[: len(prefix)], token[len(prefix) :]]
    return [token]


def append_text_segment(segments: list[TextSegment], value: str) -> None:
    """Append or merge a plain-text segment."""
    if not value:
        return
    if segments and segments[-1]["type"] == "text":
        segments[-1]["value"] += value
        return
    segments.append({"type": "text", "value": value})


def build_record_match_index(user: User, language: str) -> dict[str, int]:
    """Map normalized prompt words to record ids for the current user."""
    prompt_field = "word__en" if language == StudyLanguage.ENGLISH else "word__fr"
    prompt_attr = "en" if language == StudyLanguage.ENGLISH else "fr"
    records = (
        Record.objects.filter(user=user)
        .select_related("word")
        .exclude(**{prompt_field: ""})
        .order_by("date_added", "pk")
    )

    record_ids_by_normalized: dict[str, int] = {}
    for record in records:
        normalized = normalize_word(getattr(record.word, prompt_attr), language)
        record_ids_by_normalized.setdefault(normalized, record.pk)
    return record_ids_by_normalized


def english_contraction_match(normalized_token: str) -> str | None:
    """Return an English contraction match when present."""
    if normalized_token in ENGLISH_IRREGULAR_CONTRACTIONS:
        return normalized_token
    if normalized_token.endswith(ENGLISH_CONTRACTION_SUFFIXES):
        return normalized_token
    if normalized_token.endswith("'s"):
        base = normalized_token[: -len("'s")]
        if base in ENGLISH_S_CONTRACTION_BASES:
            return normalized_token
    return None


def french_contraction_match(normalized_token: str) -> str | None:
    """Return a French contraction prefix match when present."""
    if normalized_token in FRENCH_CONTRACTION_PREFIXES:
        return normalized_token
    return None


def number_word_match(token: str, language: str) -> str | None:
    """Return the normalized number-word match when present."""
    normalized_token = normalize_token(token)
    if normalized_token in NUMBER_WORDS_BY_LANGUAGE[language]:
        return normalized_token

    normalized_word = normalize_word(token, language)
    if normalized_word in NUMBER_WORDS_BY_LANGUAGE[language]:
        return normalized_word
    return None


def automatic_match(token: str, language: str) -> tuple[str, str] | None:
    """Return the automatic match kind and normalized value when present."""
    normalized_token = normalize_token(token)
    if normalized_token in ARTICLE_TOKENS_BY_LANGUAGE[language]:
        return ("article", normalized_token)

    if language == StudyLanguage.ENGLISH:
        contraction_match = english_contraction_match(normalized_token)
    else:
        contraction_match = french_contraction_match(normalized_token)
    if contraction_match is not None:
        return ("contraction", contraction_match)

    number_match = number_word_match(token, language)
    if number_match is not None:
        return ("number_word", number_match)

    return None


def append_processed_token(
    segments: list[TextSegment],
    token: str,
    language: str,
    record_ids_by_normalized: dict[str, int],
) -> None:
    """Append a processed token as a match or plain text."""
    automatic = automatic_match(token, language)
    if automatic is not None:
        match_kind, normalized = automatic
        segments.append(
            {
                "type": "match",
                "value": token,
                "normalized": normalized,
                "match_kind": match_kind,
                "record_id": None,
            }
        )
        return

    normalized = normalize_word(token, language)
    record_id = record_ids_by_normalized.get(normalized)
    if record_id is None:
        append_text_segment(segments, token)
        return

    segments.append(
        {
            "type": "match",
            "value": token,
            "normalized": normalized,
            "match_kind": "record",
            "record_id": record_id,
        }
    )


def build_text_segments(content: str, language: str, user: User) -> list[TextSegment]:
    """Return the processed text with matched segments highlighted."""
    record_ids_by_normalized = build_record_match_index(user, language)
    segments: list[TextSegment] = []
    cursor = 0

    for match in WORD_RE.finditer(content):
        append_text_segment(segments, content[cursor : match.start()])
        token = match.group()
        tokens = (
            split_french_token(token)
            if language == StudyLanguage.FRENCH
            else [token]
        )
        for token_part in tokens:
            append_processed_token(segments, token_part, language, record_ids_by_normalized)
        cursor = match.end()

    append_text_segment(segments, content[cursor:])
    return segments
