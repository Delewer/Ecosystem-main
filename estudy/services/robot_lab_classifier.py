from __future__ import annotations

import ast
import re
from typing import Any

FORBIDDEN_TOKENS = (
    "import ",
    "open(",
    "eval(",
    "exec(",
    "__",
    "os.",
    "sys.",
    "subprocess",
)

SAFE_BUILTIN_CALLS = {"range", "len", "min", "max", "abs", "int", "float", "bool"}
DEFAULT_TYPICAL_ERROR = "unknown"
MOVEMENT_CALLS = ("move", "up", "down", "left", "right")

ERROR_TO_CONCEPT = {
    "missing_condition_check": "condition",
    "infinite_loop": "loop",
    "wrong_turn": "sequencing",
    "insufficient_steps": "sequencing",
    "forgot_activate": "condition",
    "forgot_pick": "condition",
    "indentation": "debugging",
    "syntax": "debugging",
    "API_not_allowed": "debugging",
}


def _uses_call(code: str, name: str) -> bool:
    return bool(re.search(rf"\b{re.escape(name)}\s*\(", code))


def _count_call(code: str, name: str) -> int:
    return len(re.findall(rf"\b{re.escape(name)}\s*\(", code))


def _extract_call_names(code: str) -> set[str]:
    try:
        tree = ast.parse(code or "")
    except SyntaxError:
        return set()

    calls: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            calls.add(node.func.id)
    return calls


def _repeated_primary_error(payload: dict[str, Any], primary_error: str) -> bool:
    if not primary_error:
        return False
    count = 0
    for item in payload.get("history") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("primary_error") or "").strip() == primary_error:
            count += 1
    return count >= 2


def classify_robot_lab_typical_error(payload: dict[str, Any]) -> dict[str, Any]:
    code = payload.get("student_code") or ""
    error_type = payload.get("error_type") or "logic"
    trace = payload.get("execution_trace") or []
    primary_error = str(payload.get("primary_error") or "").strip()
    allowed_api = set(payload.get("level_metadata", {}).get("allowed_api") or [])
    movement_count = sum(_count_call(code, name) for name in MOVEMENT_CALLS)

    for token in FORBIDDEN_TOKENS:
        if token in code:
            return {
                "typical_error": "API_not_allowed",
                "confidence": 0.99,
                "evidence": [f"Forbidden token detected: {token.strip()}"],
                "concept_focus": "debugging",
            }

    call_names = _extract_call_names(code)
    if allowed_api:
        disallowed_calls = sorted(
            name
            for name in call_names
            if name not in allowed_api and name not in SAFE_BUILTIN_CALLS
        )
        if disallowed_calls:
            return {
                "typical_error": "API_not_allowed",
                "confidence": 0.97,
                "evidence": [
                    f"Disallowed function call: {', '.join(disallowed_calls)}"
                ],
                "concept_focus": "debugging",
            }

    if error_type == "syntax":
        if "indent" in primary_error.lower():
            typical = "indentation"
        else:
            typical = "syntax"
        return {
            "typical_error": typical,
            "confidence": 0.95,
            "evidence": [f"syntax error: {primary_error or 'parse failed'}"],
            "concept_focus": "debugging",
        }

    if primary_error == "hit_wall" and "front_is_clear" in allowed_api and not _uses_call(
        code, "front_is_clear"
    ):
        return {
            "typical_error": "missing_condition_check",
            "confidence": 0.9,
            "evidence": [
                "Robot hit a wall",
                "front_is_clear() is not used in student code",
            ],
            "concept_focus": "condition",
        }

    if primary_error == "hit_wall":
        return {
            "typical_error": "wrong_turn",
            "confidence": 0.78,
            "evidence": [
                "Robot collided with a wall",
                "The command order does not match the map",
            ],
            "concept_focus": "sequencing",
        }

    if error_type == "timeout" or primary_error == "step_limit_exceeded":
        if "while True" in code or not _uses_call(code, "at_goal"):
            return {
                "typical_error": "infinite_loop",
                "confidence": 0.92,
                "evidence": [
                    "Step limit exceeded",
                    "Loop has no clear stop condition",
                ],
                "concept_focus": "loop",
            }

    near_terminal_seen = any(
        str(entry.get("action") or "") == "near_terminal"
        for entry in trace
        if isinstance(entry, dict)
    )
    if primary_error in {"missing_activate", "cannot_activate"} or (
        near_terminal_seen and not _uses_call(code, "activate")
    ):
        return {
            "typical_error": "forgot_activate",
            "confidence": 0.88,
            "evidence": ["Terminal interaction expected but activate() missing"],
            "concept_focus": "condition",
        }

    if primary_error in {"missing_pick", "no_item_to_pick"}:
        return {
            "typical_error": "forgot_pick",
            "confidence": 0.86,
            "evidence": ["Item interaction failed"],
            "concept_focus": "condition",
        }

    if error_type == "logic" and primary_error == "not_reached_goal":
        if movement_count <= 2:
            return {
                "typical_error": "insufficient_steps",
                "confidence": 0.8,
                "evidence": [
                    "Robot did not reach goal",
                    "Very few movement actions in code",
                ],
                "concept_focus": "sequencing",
            }

    if _repeated_primary_error(payload, primary_error):
        mapped = ERROR_TO_CONCEPT.get(DEFAULT_TYPICAL_ERROR, "debugging")
        return {
            "typical_error": DEFAULT_TYPICAL_ERROR,
            "confidence": 0.55,
            "evidence": [f"Repeated primary error across attempts: {primary_error}"],
            "concept_focus": mapped,
        }

    return {
        "typical_error": DEFAULT_TYPICAL_ERROR,
        "confidence": 0.4,
        "evidence": ["No strong rule matched"],
        "concept_focus": "debugging",
    }
