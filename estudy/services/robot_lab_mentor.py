from __future__ import annotations

from typing import Any

from django.contrib.auth.models import User

from .robot_lab_classifier import classify_robot_lab_typical_error
from .robot_lab_contracts import normalize_robot_lab_payload
from .robot_lab_skill_tracking import (
    record_robot_lab_attempt,
    update_robot_lab_skill_profile,
)

CONCEPT_FOCUS_CHOICES = {"sequencing", "condition", "loop", "function", "debugging"}
TYPICAL_ERROR_TO_CONCEPT = {
    "missing_condition_check": "condition",
    "infinite_loop": "loop",
    "wrong_turn": "sequencing",
    "insufficient_steps": "sequencing",
    "forgot_activate": "condition",
    "forgot_pick": "condition",
    "indentation": "debugging",
    "syntax": "debugging",
    "API_not_allowed": "debugging",
    "unknown": "debugging",
}


def _uses_cardinal_commands(payload: dict[str, Any]) -> bool:
    allowed_api = set(payload.get("level_metadata", {}).get("allowed_api") or [])
    return bool({"up", "down", "left", "right"} & allowed_api)


def _movement_example(payload: dict[str, Any]) -> str:
    if _uses_cardinal_commands(payload):
        return "right()\nright()\ndown()\nright()"
    return "move()\nmove()\nturn_right()\nmove()"


def _trace_summary(trace: list[dict[str, Any]], error_type: str) -> str:
    if error_type == "none":
        if trace:
            steps = max(int(item.get("step") or 0) for item in trace)
            return f"Your robot completed the mission in {steps} steps."
        return "Your robot completed the mission."

    if not trace:
        if error_type == "syntax":
            return "Python could not start the simulation because of a syntax issue."
        return "The simulation stopped before the robot could finish."

    last = trace[-1]
    step = int(last.get("step") or 0)
    action = str(last.get("action") or "").strip()
    error = str(last.get("error") or "").strip()
    position = last.get("position")
    if error:
        where = f" at position {position}" if position else ""
        if action:
            return f"At step {step}, the robot tried to {action}{where} and then got '{error}'."
        return f"At step {step}, the run stopped with '{error}'{where}."
    if action:
        return f"The robot executed '{action}' at step {step}, then the run stopped."
    return "The robot started moving, but the run ended before the goal."


def _pick_concept_focus(payload: dict[str, Any], classification: dict[str, Any]) -> str:
    suggested = str(classification.get("concept_focus") or "").strip().lower()
    if suggested in CONCEPT_FOCUS_CHOICES:
        return suggested
    typical = str(classification.get("typical_error") or "unknown")
    mapped = TYPICAL_ERROR_TO_CONCEPT.get(typical, "")
    if mapped:
        return mapped
    for concept in payload.get("concepts") or []:
        concept_text = str(concept).strip().lower()
        if concept_text in CONCEPT_FOCUS_CHOICES:
            return concept_text
    return "debugging"


def _is_repeated_error(payload: dict[str, Any]) -> bool:
    primary_error = str(payload.get("primary_error") or "")
    if not primary_error:
        return False
    seen = 0
    for item in payload.get("history") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("primary_error") or "") == primary_error:
            seen += 1
    return seen >= 2


def _mistake_and_hints(
    *,
    payload: dict[str, Any],
    classification: dict[str, Any],
    concept_focus: str,
) -> tuple[str, str, str]:
    typical = str(classification.get("typical_error") or "unknown")
    attempt = int(payload.get("attempt_number") or 1)
    repeated = _is_repeated_error(payload)

    if payload.get("error_type") == "none":
        return (
            "No mistake now. The robot reached the goal.",
            "Can you describe why your sequence works?",
            "Try a cleaner version: same behavior, fewer repeated lines.",
        )

    if typical == "missing_condition_check":
        return (
            "The robot moved forward without checking if the path was clear.",
            "Before each move, ask a yes/no question about the front cell.",
            "Pattern: if front_is_clear(): move() else: turn_left()",
        )
    if typical == "infinite_loop":
        return (
            "Your loop keeps running because it has no real stop condition.",
            "Think: when exactly should the robot stop?",
            "Use a loop condition tied to the goal, for example: while not at_goal():",
        )
    if typical == "forgot_activate":
        return (
            "The robot reached the terminal area but did not activate it.",
            "Check the goal text: which action finishes the mission?",
            "Add a check near the terminal and call activate() when needed.",
        )
    if typical == "forgot_pick":
        return (
            "The robot needs to pick an item, but pick() was missing or used at the wrong time.",
            "Ask first: is the robot standing on the item tile?",
            "Pattern: if on_item(): pick()",
        )
    if typical == "insufficient_steps":
        return (
            "The robot stopped too early and did not cover enough cells.",
            "Count the cells between start and goal.",
            "Use repetition instead of writing one move only.",
        )
    if typical in {"indentation", "syntax"}:
        primary_error = str(payload.get("primary_error") or "")
        if primary_error.startswith("unknown_command:"):
            parts = primary_error.split(":")
            command = parts[1] if len(parts) > 1 else "unknown"
            suggestion = parts[2] if len(parts) > 2 else ""
            mistake = f"The program uses an unknown command: {command}()."
            hint_2 = (
                f"Try {suggestion}() instead."
                if suggestion
                else "Check the command list for the exact spelling."
            )
            return (
                mistake,
                "Compare the spelling with the allowed commands in this level.",
                hint_2,
            )
        if primary_error == "missing_command_placeholder":
            return (
                "One line still has ___ instead of a real command.",
                "Replace the blank with one allowed command.",
                "Look at the map and choose the direction for the missing step.",
            )
        return (
            "Python could not run the program because of formatting/syntax.",
            "Check indentation and punctuation line by line.",
            "Keep code blocks aligned under if/while/for.",
        )
    if typical == "API_not_allowed":
        return (
            "The code uses functions or syntax that this level does not allow.",
            "Use only the Robot Lab API listed for this level.",
            "Remove forbidden calls and keep only allowed robot commands.",
        )

    if attempt >= 3 or repeated:
        return (
            "The same issue keeps blocking progress.",
            "Focus on one small fix, run, then inspect the next trace step.",
            f"Direct pattern: {_movement_example(payload)}",
        )

    if concept_focus == "loop":
        return (
            "The loop logic is close, but stop behavior is not correct yet.",
            "Which condition changes while the robot moves?",
            "Tie loop control to that changing condition.",
        )
    if concept_focus == "condition":
        return (
            "A decision point is missing or in the wrong place.",
            "Ask a sensor question before risky actions.",
            "Use if/else around move() or mission actions.",
        )
    if concept_focus == "sequencing":
        return (
            "The action order does not match the map flow.",
            "Read the trace and compare step by step with your plan.",
            "Adjust one command order and run again.",
        )
    if concept_focus == "function":
        return (
            "The mission would be easier with a small helper function.",
            "Group repeated commands into one named block.",
            "Call the function where the same mini-task repeats.",
        )
    return (
        "The robot behavior and goal do not fully match yet.",
        "Use the trace: find the first step where behavior diverges from plan.",
        "Fix that first mismatch, then run again.",
    )


def _example_solution(payload: dict[str, Any], concept_focus: str) -> str:
    if _uses_cardinal_commands(payload):
        return _movement_example(payload)
    if concept_focus == "loop":
        return "while not at_goal():\n    if front_is_clear():\n        move()\n    else:\n        turn_right()"
    if concept_focus == "condition":
        return "if front_is_clear():\n    move()\nelse:\n    turn_left()"
    if concept_focus == "function":
        return (
            "def step_forward_safely():\n"
            "    if front_is_clear():\n"
            "        move()\n\n"
            "while not at_goal():\n"
            "    step_forward_safely()"
        )
    if concept_focus == "sequencing":
        return _movement_example(payload)
    return "while not at_goal():\n    if front_is_clear():\n        move()\n    else:\n        turn_left()"


def _encouragement(payload: dict[str, Any], solved: bool) -> str:
    if solved:
        return "Great job! You solved it with real Python thinking."
    if int(payload.get("attempt_number") or 1) >= 3:
        return "You are persistent. One clear fix can unlock this mission."
    return "Nice effort. You are close, keep iterating."


def build_robo_mentor_response(
    raw_payload: dict[str, Any], *, user: User | None = None
) -> dict[str, Any]:
    payload = normalize_robot_lab_payload(raw_payload)
    classification = classify_robot_lab_typical_error(payload)
    concept_focus = _pick_concept_focus(payload, classification)

    solved = payload.get("error_type") == "none"
    what_happened = _trace_summary(
        payload.get("execution_trace") or [], payload["error_type"]
    )
    mistake_explanation, hint_level_1, hint_level_2 = _mistake_and_hints(
        payload=payload,
        classification=classification,
        concept_focus=concept_focus,
    )

    response = {
        "what_happened": what_happened,
        "mistake_explanation": mistake_explanation,
        "hint_level_1": hint_level_1,
        "hint_level_2": hint_level_2,
        "concept_focus": concept_focus,
        "encouragement": _encouragement(payload, solved),
    }

    if payload.get("student_requested_solution"):
        response["example_solution"] = _example_solution(payload, concept_focus)

    if user is not None:
        try:
            record_robot_lab_attempt(
                user=user,
                payload=payload,
                typical_error=str(classification.get("typical_error") or "unknown"),
                concept_focus=concept_focus,
                solved=solved,
            )
            update_robot_lab_skill_profile(
                user=user,
                payload=payload,
                typical_error=str(classification.get("typical_error") or "unknown"),
                solved=solved,
            )
        except Exception:
            # mentor response must still be returned even if tracking failed
            pass

    return response
