from __future__ import annotations

from collections.abc import Iterable

from django.core.exceptions import ObjectDoesNotExist

from ..models import Lesson

OLDER_AGE_BRACKETS = {
    Lesson.AGE_11_13,
    Lesson.AGE_14_16,
    Lesson.AGE_16_PLUS,
}


def get_registration_profile_age(user) -> int | None:
    if not getattr(user, "is_authenticated", False):
        return None

    try:
        profile = user.profile
    except (AttributeError, ObjectDoesNotExist):
        return None
    age = getattr(profile, "age", None)
    if age in (None, ""):
        return None
    try:
        normalized = int(age)
    except (TypeError, ValueError):
        return None
    return normalized if normalized > 0 else None


def map_age_to_lesson_bracket(age: int | None) -> str | None:
    if age is None:
        return None
    if age <= 10:
        return Lesson.AGE_8_10
    if age <= 13:
        return Lesson.AGE_11_13
    if age <= 16:
        return Lesson.AGE_14_16
    return Lesson.AGE_16_PLUS


def resolve_learning_age_bracket(user, fallback: str | None = None) -> str | None:
    return map_age_to_lesson_bracket(get_registration_profile_age(user)) or fallback


def user_prefers_junior_track(user) -> bool | None:
    bracket = resolve_learning_age_bracket(user)
    if bracket is None:
        return None
    return bracket == Lesson.AGE_8_10


def filter_lessons_for_user_age(lessons: Iterable[Lesson], user) -> list[Lesson]:
    lesson_list = list(lessons)
    preferred = resolve_learning_age_bracket(user)
    if preferred is None:
        return lesson_list

    if preferred == Lesson.AGE_8_10:
        filtered = [
            lesson for lesson in lesson_list if lesson.age_bracket == Lesson.AGE_8_10
        ]
    else:
        filtered = [
            lesson for lesson in lesson_list if lesson.age_bracket in OLDER_AGE_BRACKETS
        ]

    return filtered or lesson_list
