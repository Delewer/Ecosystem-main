from __future__ import annotations

import re
from difflib import SequenceMatcher


def tokenize_code(code: str) -> list[str]:
    """Lightweight tokenizer to normalize variable names and spacing."""
    return re.findall(r"[A-Za-z_][\\w]*|\\d+|==|!=|<=|>=|\\S", code or "")


def similarity_score(code_a: str, code_b: str) -> float:
    """Return a percent similarity score between two code snippets."""
    tokens_a = tokenize_code(code_a)
    tokens_b = tokenize_code(code_b)
    if not tokens_a or not tokens_b:
        return 0.0
    ratio = SequenceMatcher(None, tokens_a, tokens_b).ratio()
    return round(ratio * 100, 2)


def is_suspicious_similarity(code_a: str, code_b: str, threshold: float = 80.0) -> bool:
    """Detect if two snippets are suspiciously similar based on a threshold percent."""
    return similarity_score(code_a, code_b) >= threshold
