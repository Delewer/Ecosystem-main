from __future__ import annotations

from collections.abc import Iterable

from django.core.exceptions import ObjectDoesNotExist

from ..models import Lesson

OLDER_AGE_BRACKETS = {
    Lesson.AGE_11_13,
    Lesson.AGE_14_16,
    Lesson.AGE_16_PLUS,
}
JUNIOR_TRACK = "junior"
OLDER_TRACK = "older"


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


def lesson_track_key(lesson_or_bracket) -> str:
    bracket = getattr(lesson_or_bracket, "age_bracket", lesson_or_bracket)
    return JUNIOR_TRACK if bracket == Lesson.AGE_8_10 else OLDER_TRACK


def filter_lessons_for_track(
    lessons: Iterable[Lesson],
    *,
    user=None,
    anchor_lesson: Lesson | None = None,
) -> list[Lesson]:
    lesson_list = list(lessons)
    if not lesson_list:
        return lesson_list

    available_tracks = {lesson_track_key(lesson) for lesson in lesson_list}
    if len(available_tracks) <= 1:
        return lesson_list

    if anchor_lesson is not None:
        preferred_track = lesson_track_key(anchor_lesson)
    else:
        preferred_bracket = resolve_learning_age_bracket(user)
        if preferred_bracket is None:
            return lesson_list
        preferred_track = lesson_track_key(preferred_bracket)

    filtered = [
        lesson for lesson in lesson_list if lesson_track_key(lesson) == preferred_track
    ]
    return filtered or lesson_list


def split_lessons_for_accessibility(
    lessons: Iterable[Lesson], user=None
) -> list[list[Lesson]]:
    lesson_list = list(lessons)
    if not lesson_list:
        return []

    preferred_bracket = resolve_learning_age_bracket(user)
    if preferred_bracket is not None:
        return [filter_lessons_for_track(lesson_list, user=user)]

    available_tracks = {lesson_track_key(lesson) for lesson in lesson_list}
    if len(available_tracks) <= 1:
        return [lesson_list]

    buckets: list[list[Lesson]] = []
    for track in (JUNIOR_TRACK, OLDER_TRACK):
        bucket = [lesson for lesson in lesson_list if lesson_track_key(lesson) == track]
        if bucket:
            buckets.append(bucket)
    return buckets


def filter_lessons_for_user_age(lessons: Iterable[Lesson], user) -> list[Lesson]:
    return filter_lessons_for_track(lessons, user=user)
