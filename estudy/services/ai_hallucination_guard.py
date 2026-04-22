from __future__ import annotations

import re

from .ai_context import build_lesson_clues
from .service_result import BaseServiceResult

GUARD_SIGNAL_TOO_LONG = "too_long"
GUARD_SIGNAL_UNGROUNDED = "ungrounded"
GUARD_SIGNAL_FORBIDDEN = "forbidden"
GUARD_SIGNAL_EMPTY = "empty_answer"

MAX_HINT_CHARS = 700
MAX_CONTEXT_SNIPPETS = 6
MIN_TOKEN_LENGTH = 3
MIN_OVERLAP_TOKENS = 1

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")
FORBIDDEN_PATTERNS = (
    re.compile(r"```"),
    re.compile(r"\bfinal\s+answer\b", re.IGNORECASE),
    re.compile(r"\banswer\s*:\b", re.IGNORECASE),
    re.compile(r"\bsolution\b", re.IGNORECASE),
    re.compile(r"\bhere(?:'s| is)\s+the\s+code\b", re.IGNORECASE),
    re.compile(r"\bdef\s+[A-Za-z_][A-Za-z0-9_]*\s*\("),
    re.compile(r"\bclass\s+[A-Za-z_][A-Za-z0-9_]*\b"),
)

SAFE_HINT_TEMPLATE = (
    "I can offer a hint instead of a full answer. "
    "Restate the question in your own words and verify one small step at a time "
    "using the lesson examples."
)


def _normalize_text(value: str | None) -> str:
    return str(value or "").strip()


def _tokenize(text: str) -> list[str]:
    raw_tokens = TOKEN_PATTERN.findall(text.lower())
    tokens: list[str] = []
    for token in raw_tokens:
        if len(token) < MIN_TOKEN_LENGTH:
            continue
        tokens.append(token)
        # Keep a tiny plural-to-singular fallback so "loops" and "loop" overlap.
        if token.endswith("s") and not token.endswith("ss"):
            singular = token[:-1]
            if len(singular) >= MIN_TOKEN_LENGTH:
                tokens.append(singular)
    return tokens


def _context_tokens(question: str, lesson) -> set[str]:
    parts: list[str] = []
    if question:
        parts.append(question)
    if lesson and getattr(lesson, "title", None):
        parts.append(lesson.title)
    if lesson:
        parts.extend(build_lesson_clues(lesson))
    if len(parts) > MAX_CONTEXT_SNIPPETS:
        parts = parts[:MAX_CONTEXT_SNIPPETS]
    tokens: set[str] = set()
    for part in parts:
        tokens.update(_tokenize(part))
    return tokens


def _has_forbidden_patterns(text: str) -> bool:
    return any(pattern.search(text) for pattern in FORBIDDEN_PATTERNS)


def _is_grounded(answer: str, context_tokens: set[str]) -> bool:
    if not context_tokens:
        return True
    answer_tokens = set(_tokenize(answer))
    if not answer_tokens:
        return False
    overlap = context_tokens.intersection(answer_tokens)
    return len(overlap) >= MIN_OVERLAP_TOKENS


def _truncate(text: str) -> str:
    if len(text) <= MAX_HINT_CHARS:
        return text
    return text[:MAX_HINT_CHARS].rstrip()


def _build_safe_hint(question: str, lesson) -> str:
    if lesson and getattr(lesson, "title", None):
        return SAFE_HINT_TEMPLATE + f" Focus on the key ideas from '{lesson.title}'."
    if question:
        return SAFE_HINT_TEMPLATE + " Focus on the specific part you find hardest."
    return SAFE_HINT_TEMPLATE


def guard_hint_response(
    *,
    question: str,
    answer: str,
    lesson=None,
) -> BaseServiceResult:
    signals: list[str] = []
    original = _normalize_text(answer)
    if not original:
        signals.append(GUARD_SIGNAL_EMPTY)
        guarded = _build_safe_hint(question, lesson)
        return BaseServiceResult.ok(
            data={
                "answer": guarded,
                "signals": signals,
                "modified": True,
                "original_length": 0,
                "final_length": len(guarded),
            }
        )

    guarded = original
    modified = False

    truncated = _truncate(guarded)
    if truncated != guarded:
        guarded = truncated
        signals.append(GUARD_SIGNAL_TOO_LONG)
        modified = True

    if _has_forbidden_patterns(guarded):
        signals.append(GUARD_SIGNAL_FORBIDDEN)
    context_tokens = _context_tokens(question, lesson)
    if not _is_grounded(guarded, context_tokens):
        signals.append(GUARD_SIGNAL_UNGROUNDED)

    if GUARD_SIGNAL_FORBIDDEN in signals or GUARD_SIGNAL_UNGROUNDED in signals:
        guarded = _build_safe_hint(question, lesson)
        modified = True

    return BaseServiceResult.ok(
        data={
            "answer": guarded,
            "signals": signals,
            "modified": modified,
            "original_length": len(original),
            "final_length": len(guarded),
        }
    )
