from __future__ import annotations

import re

from .service_result import BaseServiceResult

MODERATION_ACTION_APPROVE = "approve"
MODERATION_ACTION_REVIEW = "review"
MODERATION_ACTION_HIDE = "hide"

SIGNAL_BANNED_WORD = "banned_word"
SIGNAL_EXCESSIVE_LINKS = "excessive_links"
SIGNAL_EXCESSIVE_CAPS = "excessive_caps"
SIGNAL_REPEATED_CHAR = "repeated_char"
SIGNAL_EXCESSIVE_PUNCT = "excessive_punct"

REVIEW_THRESHOLD = 2
HIDE_THRESHOLD = 5

BANNED_WORD_WEIGHT = 3
LINK_WEIGHT = 2
CAPS_WEIGHT = 2
REPEAT_WEIGHT = 1
PUNCT_WEIGHT = 1

TRUSTED_SCORE_DISCOUNT = 2

MAX_LINKS_ALLOWED = 2
CAPS_RATIO_THRESHOLD = 0.7
CAPS_MIN_ALPHA_CHARS = 20
REPEAT_CHAR_MIN = 6
EXCESS_PUNCT_MIN = 6

BANNED_WORDS = (
    "idiot",
    "stupid",
    "dumb",
    "hate",
    "kill",
    "trash",
)

URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
BANNED_WORD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(word) for word in BANNED_WORDS) + r")\b",
    re.IGNORECASE,
)
REPEAT_CHAR_PATTERN = re.compile(r"(.)\1{" + str(REPEAT_CHAR_MIN - 1) + r",}")


def _alpha_stats(text: str) -> tuple[int, int]:
    alpha_chars = [ch for ch in text if ch.isalpha()]
    uppercase = [ch for ch in alpha_chars if ch.isupper()]
    return len(alpha_chars), len(uppercase)


def _caps_ratio(alpha_count: int, upper_count: int) -> float:
    if alpha_count <= 0:
        return 0.0
    return upper_count / alpha_count


def _count_links(text: str) -> int:
    return len(URL_PATTERN.findall(text))


def _count_excess_punct(text: str) -> int:
    return sum(ch in PUNCTUATION_CHARS for ch in text)


def _score_to_action(score: int) -> str:
    if score >= HIDE_THRESHOLD:
        return MODERATION_ACTION_HIDE
    if score >= REVIEW_THRESHOLD:
        return MODERATION_ACTION_REVIEW
    return MODERATION_ACTION_APPROVE


def moderate_comment_content(
    *,
    content: str,
    is_trusted: bool = False,
) -> BaseServiceResult:
    text = (content or "").strip()
    signals: list[str] = []
    score = 0

    if BANNED_WORD_PATTERN.search(text):
        signals.append(SIGNAL_BANNED_WORD)
        score += BANNED_WORD_WEIGHT

    link_count = _count_links(text)
    if link_count > MAX_LINKS_ALLOWED:
        signals.append(SIGNAL_EXCESSIVE_LINKS)
        score += LINK_WEIGHT

    alpha_count, upper_count = _alpha_stats(text)
    if (
        _caps_ratio(alpha_count, upper_count) >= CAPS_RATIO_THRESHOLD
        and alpha_count >= CAPS_MIN_ALPHA_CHARS
    ):
        signals.append(SIGNAL_EXCESSIVE_CAPS)
        score += CAPS_WEIGHT

    if REPEAT_CHAR_PATTERN.search(text):
        signals.append(SIGNAL_REPEATED_CHAR)
        score += REPEAT_WEIGHT

    if _count_excess_punct(text) >= EXCESS_PUNCT_MIN:
        signals.append(SIGNAL_EXCESSIVE_PUNCT)
        score += PUNCT_WEIGHT

    if is_trusted and score > 0:
        score = max(0, score - TRUSTED_SCORE_DISCOUNT)

    action = _score_to_action(score)
    is_hidden = action == MODERATION_ACTION_HIDE
    is_approved = action == MODERATION_ACTION_APPROVE

    return BaseServiceResult.ok(
        data={
            "action": action,
            "is_hidden": is_hidden,
            "is_approved": is_approved,
            "score": score,
            "signals": signals,
            "link_count": link_count,
        }
    )


PUNCTUATION_CHARS = "!?"
