from __future__ import annotations

from copy import deepcopy
from typing import Any

ROBOT_LAB_ERROR_TYPES = {"runtime", "logic", "timeout", "syntax", "none"}
ROBOT_LAB_CONCEPTS = {"sequencing", "condition", "loop", "function", "debugging"}

DEFAULT_ALLOWED_API = [
    "up",
    "down",
    "left",
    "right",
    "move",
    "turn_left",
    "turn_right",
    "pick",
    "activate",
    "front_is_clear",
    "at_goal",
    "on_item",
    "near_terminal",
    "has_item",
]


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_error_type(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in ROBOT_LAB_ERROR_TYPES:
        return text
    return "logic"


def _normalize_concepts(value: Any) -> list[str]:
    concepts: list[str] = []
    for item in value or []:
        concept = str(item or "").strip().lower()
        if concept in ROBOT_LAB_CONCEPTS and concept not in concepts:
            concepts.append(concept)
    if concepts:
        return concepts
    return ["debugging"]


def _normalize_trace(trace: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in trace or []:
        if not isinstance(item, dict):
            continue
        step = _safe_int(item.get("step"), 0)
        action = str(item.get("action") or "").strip()
        error = str(item.get("error") or "").strip()
        entry: dict[str, Any] = {"step": step}
        if action:
            entry["action"] = action
        if error:
            entry["error"] = error
        if "position" in item:
            entry["position"] = item["position"]
        if "dir" in item:
            entry["dir"] = item["dir"]
        normalized.append(entry)
    return normalized


def _derive_primary_error(payload: dict[str, Any], trace: list[dict[str, Any]]) -> str:
    explicit = str(payload.get("primary_error") or "").strip()
    if explicit:
        return explicit
    for entry in reversed(trace):
        candidate = str(entry.get("error") or "").strip()
        if candidate:
            return candidate
    history = payload.get("history") or []
    if isinstance(history, list):
        for item in reversed(history):
            if not isinstance(item, dict):
                continue
            candidate = str(item.get("primary_error") or "").strip()
            if candidate:
                return candidate
    return ""


def normalize_robot_lab_payload(raw_payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_payload, dict):
        raise ValueError("Payload must be an object.")

    payload = deepcopy(raw_payload)
    trace = _normalize_trace(payload.get("execution_trace"))

    level_metadata = payload.get("level_metadata") or {}
    if not isinstance(level_metadata, dict):
        level_metadata = {}
    allowed_api = level_metadata.get("allowed_api")
    if not isinstance(allowed_api, list) or not allowed_api:
        allowed_api = list(DEFAULT_ALLOWED_API)

    normalized = {
        "level_id": str(payload.get("level_id") or "UNKNOWN"),
        "goal": str(payload.get("goal") or "").strip() or "Reach the goal",
        "concepts": _normalize_concepts(payload.get("concepts")),
        "student_code": str(payload.get("student_code") or ""),
        "execution_trace": trace,
        "error_type": _normalize_error_type(payload.get("error_type")),
        "attempt_number": max(1, _safe_int(payload.get("attempt_number"), 1)),
        "student_requested_solution": bool(
            payload.get("student_requested_solution", False)
        ),
        "history": payload.get("history")
        if isinstance(payload.get("history"), list)
        else [],
        "level_metadata": {
            "max_steps": max(1, _safe_int(level_metadata.get("max_steps"), 200)),
            "allowed_api": [str(item) for item in allowed_api],
            "map_size": level_metadata.get("map_size") or [8, 8],
            "difficulty": str(level_metadata.get("difficulty") or "easy"),
        },
        "hints_used": max(0, _safe_int(payload.get("hints_used"), 0)),
    }
    normalized["primary_error"] = _derive_primary_error(payload, trace)
    return normalized
