from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.db.models import Prefetch

from ..models import Lesson, LessonProgress, Subject
from .learner_age import split_lessons_for_accessibility


def prefetched_subjects():
    return Subject.objects.prefetch_related(
        Prefetch("lessons", queryset=Lesson.objects.order_by("date", "id"))
    ).order_by("name")


def compute_accessibility(
    user, subjects: Iterable[Subject] | None = None
) -> tuple[set[int], set[int], dict[int, Any]]:
    if subjects is None:
        subjects = prefetched_subjects()

    subject_list = list(subjects)
    completed_ids = set(
        LessonProgress.objects.filter(user=user, completed=True).values_list(
            "lesson_id", flat=True
        )
    )
    accessible_ids = set(completed_ids)
    locked_reasons: dict[int, Any] = {}

    for subject in subject_list:
        lesson_sequences = split_lessons_for_accessibility(
            subject.lessons.all(), user=user
        )
        for lessons in lesson_sequences:
            first_incomplete = next(
                (lesson for lesson in lessons if lesson.id not in completed_ids), None
            )
            if not first_incomplete:
                continue

            accessible_ids.add(first_incomplete.id)
            for lesson in lessons:
                if lesson.id in completed_ids or lesson.id == first_incomplete.id:
                    continue
                locked_reasons[lesson.id] = first_incomplete

    return completed_ids, accessible_ids, locked_reasons
