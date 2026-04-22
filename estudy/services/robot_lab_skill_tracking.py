from __future__ import annotations

from typing import Any

from django.contrib.auth.models import User

from ..models import RobotLabAttemptLog, RobotLabSkillProfile

CONCEPT_TO_FIELD = {
    "sequencing": "sequencing_score",
    "loop": "loop_score",
    "condition": "condition_score",
    "function": "function_score",
    "debugging": "debugging_score",
}

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


def _clamp_score(value: int) -> int:
    return max(0, min(100, int(value)))


def _adjust(profile: RobotLabSkillProfile, concept: str, delta: int) -> None:
    field = CONCEPT_TO_FIELD.get(concept)
    if not field or delta == 0:
        return
    current = int(getattr(profile, field, 0))
    setattr(profile, field, _clamp_score(current + delta))


def record_robot_lab_attempt(
    *,
    user: User,
    payload: dict[str, Any],
    typical_error: str,
    concept_focus: str,
    solved: bool,
) -> RobotLabAttemptLog:
    return RobotLabAttemptLog.objects.create(
        user=user,
        level_id=str(payload.get("level_id") or "UNKNOWN"),
        attempt_number=max(1, int(payload.get("attempt_number") or 1)),
        error_type=str(payload.get("error_type") or "logic"),
        primary_error=str(payload.get("primary_error") or ""),
        typical_error=typical_error,
        solved=bool(solved),
        hints_used=max(0, int(payload.get("hints_used") or 0)),
        requested_solution=bool(payload.get("student_requested_solution", False)),
        concept_focus=concept_focus
        if concept_focus in CONCEPT_TO_FIELD
        else "debugging",
        metadata={
            "goal": payload.get("goal"),
            "concepts": payload.get("concepts") or [],
            "level_metadata": payload.get("level_metadata") or {},
        },
    )


def update_robot_lab_skill_profile(
    *,
    user: User,
    payload: dict[str, Any],
    typical_error: str,
    solved: bool,
) -> RobotLabSkillProfile:
    profile, _ = RobotLabSkillProfile.objects.get_or_create(user=user)
    attempt_number = max(1, int(payload.get("attempt_number") or 1))
    hints_used = max(0, int(payload.get("hints_used") or 0))

    if solved:
        base_gain = max(1, int(round(10 / attempt_number)))
        if hints_used >= 2:
            base_gain = max(1, int(round(base_gain * 0.8)))
        for concept in payload.get("concepts") or []:
            _adjust(profile, str(concept), base_gain)

        if attempt_number > 1:
            _adjust(profile, "debugging", 2)

        had_fixable_error = any(
            str(item.get("error_type") or "") in {"syntax", "runtime"}
            for item in payload.get("history") or []
            if isinstance(item, dict)
        )
        if had_fixable_error:
            _adjust(profile, "debugging", 1)
    else:
        mapped_concept = ERROR_TO_CONCEPT.get(typical_error)
        if mapped_concept:
            _adjust(profile, mapped_concept, -2)

    profile.save(
        update_fields=[
            "sequencing_score",
            "loop_score",
            "condition_score",
            "function_score",
            "debugging_score",
            "updated_at",
        ]
    )
    return profile
