from __future__ import annotations

import uuid
from typing import Any

from django.contrib.auth.models import User
from django.db import transaction

from ..models import EventLog, RobotLabRun
from .audit_logger import log_event
from .robot_lab_levels import load_level
from .robot_lab_mentor import build_robo_mentor_response
from .robot_lab_progress import (
    apply_robot_lab_run_progress,
    build_robot_lab_progress_summary,
    ensure_robot_lab_progress_rows,
)
from .robot_lab_runner_client import execute_robot_lab_code

ERROR_TYPES = {"runtime", "logic", "timeout", "syntax", "none"}


class RobotLabRunBlockedError(ValueError):
    pass


def _normalize_error_type(value: Any) -> str:
    text = str(value or "logic").strip().lower()
    return text if text in ERROR_TYPES else "logic"


def _extract_primary_error(result: dict[str, Any]) -> str:
    explicit = str(result.get("primary_error") or "").strip()
    if explicit:
        return explicit
    trace = result.get("execution_trace") or []
    if isinstance(trace, list):
        for item in reversed(trace):
            if not isinstance(item, dict):
                continue
            err = str(item.get("error") or "").strip()
            if err:
                return err
    return ""


def _goal_success_label(level: dict[str, Any]) -> str:
    goal_text = str(level.get("goal_text") or "").lower()
    target_tile = str((level.get("goal") or {}).get("target_tile") or "").upper()
    if target_tile == "T" or "terminal" in goal_text:
        return "Bravo! Robotul a ajuns la terminal."
    return "Bravo! Robotul a ajuns la tinta."


def _format_console_step(entry: dict[str, Any]) -> str:
    step = int(entry.get("step") or 0)
    action = str(entry.get("action") or "").strip()
    position = entry.get("position")
    error = str(entry.get("error") or "").strip()
    location = ""
    if isinstance(position, list) and len(position) >= 2:
        location = f" -> [{position[0]}, {position[1]}]"
    line = (
        f"Pasul {step}: {action}(){location}" if action else f"Pasul {step}{location}"
    )
    if error:
        line = f"{line} -> {error}"
    return line


def _allowed_commands_hint(allowed_api: list[str]) -> str:
    commands = [f"{str(item).strip()}()" for item in allowed_api if str(item).strip()]
    if not commands:
        return ""
    return " Comenzi permise: " + ", ".join(commands) + "."


def _humanize_primary_error(
    *,
    primary_error: str,
    error_type: str,
    trace: list[dict[str, Any]],
    allowed_api: list[str],
) -> str:
    if primary_error.startswith("unknown_command:"):
        parts = primary_error.split(":")
        unknown = parts[1] if len(parts) > 1 else "unknown"
        suggestion = parts[2] if len(parts) > 2 else ""
        if suggestion:
            return (
                f"Comanda {unknown}() nu exista aici. Poate ai vrut {suggestion}()."
                f"{_allowed_commands_hint(allowed_api)}"
            )
        return f"Comanda {unknown}() nu este permisa la acest nivel.{_allowed_commands_hint(allowed_api)}"
    if primary_error == "missing_command_placeholder":
        return "Inlocuieste ___ cu o comanda permisa inainte sa rulezi programul."
    if primary_error == "hit_wall":
        failing_step = next(
            (
                int(entry.get("step") or 0)
                for entry in reversed(trace)
                if str(entry.get("error") or "").strip() == "hit_wall"
            ),
            0,
        )
        if failing_step:
            return f"Robotul a lovit peretele la pasul {failing_step}."
        return "Robotul a lovit un perete."
    if primary_error == "not_reached_goal":
        return "Programul s-a terminat, dar robotul nu a ajuns la tinta."
    if primary_error == "step_limit_exceeded":
        return "Programul s-a oprit pentru ca a folosit prea multi pasi."
    if primary_error == "indentation_error":
        return "Indentarea Python nu este corecta. Verifica spatiile si blocurile."
    if primary_error == "syntax_error":
        return "Python nu a putut citi acest cod. Verifica parantezele si liniile."
    if primary_error.startswith("forbidden_syntax:"):
        return "Structura Python folosita nu este permisa in aceasta misiune."
    if primary_error == "forbidden_attribute_access":
        return "Aici poti folosi doar comenzi directe din Robot Lab."
    if primary_error == "code_too_long":
        return "Programul este prea lung pentru aceasta misiune. Pastreaza doar pasii necesari."
    if primary_error.startswith("invalid_action:"):
        return "Programul s-a oprit pentru ca a folosit o actiune Python care nu este acceptata aici."
    if error_type == "syntax":
        return "Simularea nu a pornit fiindca exista o problema de sintaxa."
    if error_type == "timeout":
        return "Programul a rulat prea mult si misiunea a fost oprita."
    if error_type == "runtime":
        return "Misiunea s-a oprit din cauza unei probleme aparute in timpul rularii."
    if error_type == "logic" and {"up", "down", "left", "right"} & set(allowed_api):
        return "Ordinea comenzilor nu se potriveste inca cu harta."
    return "Robotul nu urmeaza inca traseul corect pentru aceasta misiune."


def _build_console_output(
    *,
    level: dict[str, Any],
    solved: bool,
    error_type: str,
    primary_error: str,
    trace: list[dict[str, Any]],
    allowed_api: list[str],
    steps_used: int,
    optimal_steps: int | None,
) -> list[str]:
    lines = ["Program pornit..."]
    lines.extend(
        _format_console_step(entry) for entry in trace if isinstance(entry, dict)
    )

    if solved:
        lines.append(_goal_success_label(level))
        if optimal_steps and steps_used > optimal_steps:
            lines.append(
                f"Ai ajuns la tinta in {steps_used} pasi, iar traseul optim are {optimal_steps}."
            )
        else:
            lines.append(f"Ai rezolvat misiunea in {steps_used} pasi.")
        return lines

    lines.append(
        _humanize_primary_error(
            primary_error=primary_error,
            error_type=error_type,
            trace=trace,
            allowed_api=allowed_api,
        )
    )
    return lines


@transaction.atomic
def run_robot_lab_attempt(
    *,
    user: User,
    level_id: str,
    student_code: str,
    student_requested_solution: bool = False,
    hints_used: int = 0,
) -> dict[str, Any]:
    level = load_level(level_id)
    progress_map = ensure_robot_lab_progress_rows(user)
    level_progress = progress_map.get(level_id)
    if not level_progress or not level_progress.unlocked:
        raise RobotLabRunBlockedError("Level is locked for this user")

    attempt_number = int(level_progress.attempts_count or 0) + 1
    run_id = str(uuid.uuid4())
    allowed_api = list(level.get("allowed_api") or [])
    max_steps = int(level.get("max_steps") or 200)
    time_limit_ms = int(level.get("time_limit_ms") or 800)

    runner_result = execute_robot_lab_code(
        level_id=level_id,
        student_code=student_code,
        level_spec=level,
        allowed_api=allowed_api,
        max_steps=max_steps,
        time_limit_ms=time_limit_ms,
        run_id=run_id,
    )

    error_type = _normalize_error_type(runner_result.get("error_type"))
    primary_error = _extract_primary_error(runner_result)
    trace = (
        runner_result.get("execution_trace")
        if isinstance(runner_result.get("execution_trace"), list)
        else []
    )
    final_state = (
        runner_result.get("final_state")
        if isinstance(runner_result.get("final_state"), dict)
        else {}
    )
    steps_used = int(runner_result.get("steps_used") or 0)
    duration_ms = int(runner_result.get("duration_ms") or 0)
    optimal_steps_raw = runner_result.get("optimal_steps")
    optimal_steps = (
        int(optimal_steps_raw)
        if isinstance(optimal_steps_raw, int) or str(optimal_steps_raw).isdigit()
        else None
    )
    solved = error_type == "none"

    mentor_payload = {
        "level_id": level_id,
        "goal": level.get("goal_text")
        or level.get("goal", {}).get("type", "Reach the goal"),
        "concepts": level.get("concepts") or [],
        "student_code": student_code,
        "execution_trace": trace,
        "error_type": error_type,
        "primary_error": primary_error,
        "attempt_number": attempt_number,
        "student_requested_solution": bool(student_requested_solution),
        "hints_used": max(0, int(hints_used or 0)),
        "history": list(
            user.robot_lab_attempt_logs.order_by("-id").values(
                "attempt_number", "error_type", "primary_error"
            )[:5]
        ),
        "level_metadata": {
            "max_steps": max_steps,
            "allowed_api": allowed_api,
            "map_size": level.get("map_size")
            or [len(level.get("grid") or []), len((level.get("grid") or [""])[0])],
            "difficulty": level.get("difficulty") or "easy",
        },
    }
    mentor_response = build_robo_mentor_response(mentor_payload, user=user)

    run = RobotLabRun.objects.create(
        user=user,
        level_id=level_id,
        attempt_number=attempt_number,
        code=student_code,
        error_type=error_type,
        primary_error=primary_error,
        execution_trace=trace,
        final_state=final_state,
        level_snapshot=level,
        steps_used=max(0, steps_used),
        duration_ms=max(0, duration_ms),
        solved=solved,
    )

    progress_result = apply_robot_lab_run_progress(
        user=user,
        level_id=level_id,
        solved=solved,
        steps_used=max(0, steps_used),
        xp_reward=int(level.get("xp_reward") or 0),
        level_spec=level,
        optimal_steps=optimal_steps,
    )

    xp_granted = int(progress_result.get("xp_granted") or 0)
    if xp_granted > 0:
        profile = getattr(user, "userprofile", None)
        if profile is not None:
            profile.add_xp(xp_granted, reason=f"Robot Lab {level_id}")

    console_output = _build_console_output(
        level=level,
        solved=solved,
        error_type=error_type,
        primary_error=primary_error,
        trace=trace,
        allowed_api=allowed_api,
        steps_used=max(0, steps_used),
        optimal_steps=optimal_steps,
    )
    status_message = console_output[-1] if console_output else "Programul s-a terminat."
    status_kind = (
        "success"
        if solved
        else "error"
        if error_type in {"runtime", "syntax", "timeout"}
        else "warning"
    )

    log_event(
        EventLog.EVENT_TEST_SUBMIT,
        user=user,
        metadata={
            "robot_lab": True,
            "run_id": run.id,
            "level_id": level_id,
            "attempt_number": attempt_number,
            "error_type": error_type,
            "primary_error": primary_error,
            "solved": solved,
            "steps_used": max(0, steps_used),
            "duration_ms": max(0, duration_ms),
            "xp_granted": xp_granted,
        },
    )

    return {
        "run_id": run.id,
        "level_id": level_id,
        "attempt_number": attempt_number,
        "error_type": error_type,
        "primary_error": primary_error,
        "execution_trace": trace,
        "final_state": final_state,
        "steps_used": max(0, steps_used),
        "duration_ms": max(0, duration_ms),
        "optimal_steps": optimal_steps,
        "solved": solved,
        "stars_earned": progress_result.get("stars_earned", 0),
        "status_kind": status_kind,
        "status_message": status_message,
        "console_output": console_output,
        "mentor": mentor_response,
        "progress": progress_result.get("summary")
        or build_robot_lab_progress_summary(user),
        "level_progress": progress_result.get("level_progress") or {},
        "xp_granted": xp_granted,
    }
