from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Set

from django.core.cache import cache
from django.db.models import Count, Max, Prefetch, Q
from django.utils import timezone

from ..models import LearningPath, LearningPathLesson, Lesson, Subject
from .gamification import build_overall_progress, get_badge_summary
from .learner_age import get_registration_profile_age
from .lesson_access import compute_accessibility
from .recommendations import refresh_recommendations


def build_lesson_blocks(
    subjects: List,
    lessons: List[Lesson],
    completed_ids: Set[int],
    accessible_ids: Set[int],
    learning_paths: List[LearningPath],
):
    """Builds lesson blocks (paths + subject blocks) for lessons listing.

    Returns a list of blocks suitable for the templates.
    """
    sequence_lookup: Dict[int, Dict] = {}

    for subject in subjects:
        lesson_sequence = []
        for index, subj_lesson in enumerate(subject.lessons.all(), start=1):
            lesson_sequence.append(
                {
                    "lesson": subj_lesson,
                    "index": index,
                    "completed": subj_lesson.id in completed_ids,
                    "accessible": subj_lesson.id in accessible_ids,
                }
            )
        subject.completed_count = sum(
            1 for item in lesson_sequence if item["completed"]
        )
        subject.total_lessons = len(lesson_sequence)
        for item in lesson_sequence:
            item["total"] = subject.total_lessons
            sequence_lookup[item["lesson"].id] = item
        subject.lesson_sequence = lesson_sequence

    lesson_lookup = {lesson.id: lesson for lesson in lessons}
    assigned_lessons = set()
    path_blocks = []

    for path in learning_paths:
        block_lessons = []
        for item in path.items.all():
            lesson = lesson_lookup.get(item.lesson_id)
            if not lesson:
                continue
            setattr(lesson, "block_order", item.order)
            assigned_lessons.add(lesson.id)
            block_lessons.append(lesson)
        if not block_lessons:
            continue
        block_lessons.sort(key=lambda lesson: getattr(lesson, "block_order", 0))
        total_in_block = len(block_lessons)
        completed_in_block = sum(
            1 for lesson in block_lessons if getattr(lesson, "is_completed", False)
        )
        progress_percent = (
            int(round((completed_in_block / total_in_block) * 100))
            if total_in_block
            else 0
        )
        next_candidate = next(
            (
                lesson
                for lesson in block_lessons
                if getattr(lesson, "is_accessible", False)
                and not getattr(lesson, "is_completed", False)
            ),
            None,
        )
        if next_candidate is None:
            next_candidate = block_lessons[0]
        path_blocks.append(
            {
                "title": path.title,
                "slug": path.slug,
                "description": path.description,
                "theme": path.theme,
                "audience": getattr(path, "audience", "general"),
                "difficulty_label": (
                    path.get_difficulty_display()
                    if hasattr(path, "get_difficulty_display")
                    else path.difficulty
                ),
                "lessons": block_lessons,
                "completed": completed_in_block,
                "total": total_in_block,
                "progress_percent": progress_percent,
                "type": "path",
                "model": path,
                "next_lesson": next_candidate,
            }
        )

    leftover_by_subject = {}
    for lesson in lessons:
        if lesson.id in assigned_lessons:
            continue
        leftover_by_subject.setdefault(lesson.subject, []).append(lesson)

    subject_blocks = []
    for subject, subject_lessons in leftover_by_subject.items():
        subject_lessons.sort(
            key=lambda lesson: (
                (
                    (getattr(lesson, "sequence", {}) or {}).get("index")
                    if isinstance(getattr(lesson, "sequence", {}), dict)
                    else float("inf")
                ),
                lesson.date,
                lesson.id,
            )
        )
        total_in_block = len(subject_lessons)
        completed_in_block = sum(
            1 for lesson in subject_lessons if getattr(lesson, "is_completed", False)
        )
        progress_percent = (
            int(round((completed_in_block / total_in_block) * 100))
            if total_in_block
            else 0
        )
        next_candidate = next(
            (
                lesson
                for lesson in subject_lessons
                if getattr(lesson, "is_accessible", False)
                and not getattr(lesson, "is_completed", False)
            ),
            None,
        )
        if next_candidate is None and subject_lessons:
            next_candidate = subject_lessons[0]
        subject_blocks.append(
            {
                "title": subject.name,
                "slug": f"subject-{subject.id}",
                "description": subject.description,
                "lessons": subject_lessons,
                "completed": completed_in_block,
                "total": total_in_block,
                "progress_percent": progress_percent,
                "type": "subject",
                "subject": subject,
                "next_lesson": next_candidate,
            }
        )

    subject_blocks.sort(key=lambda block: block["title"].lower())
    lesson_blocks = path_blocks + subject_blocks
    return lesson_blocks


def prepare_lessons_list(user, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Prepare context for lessons_list view.

    params keys: query, subject, difficulty, upcoming (bool)
    Returns dictionary of context keys used by the template.
    """
    if params is None:
        params = {}

    # optional cache support: pass `_cache_timeout` in params to set TTL (seconds).
    # set to 0 or False to disable caching for this call.
    cache_timeout = params.get("_cache_timeout", 300)
    use_cache = bool(cache_timeout)
    cache_key = None
    if use_cache:
        # build a deterministic key from user id and params (excluding the cache control key)
        params_for_key = {k: v for k, v in params.items() if k != "_cache_timeout"}
        learner_age = get_registration_profile_age(user)
        lesson_signature = Lesson.objects.aggregate(
            total=Count("id"),
            max_updated=Max("updated_at"),
            max_created=Max("created_at"),
        )
        key_payload = json.dumps(
            [user.id, learner_age, params_for_key, lesson_signature],
            sort_keys=True,
            default=str,
        ).encode("utf-8")
        cache_key = "estudy:lessons_list:" + hashlib.md5(key_payload).hexdigest()
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    query = (params.get("query") or "").strip()
    subject_filter = (params.get("subject") or "").strip()
    difficulty_filter = (params.get("difficulty") or "").strip()
    upcoming_only = params.get("upcoming") in (True, "1", 1)

    subjects = list(
        Subject.objects.prefetch_related(
            Prefetch("lessons", queryset=Lesson.objects.order_by("date", "id"))
        ).order_by("name")
    )

    lessons_qs = Lesson.objects.select_related("subject").order_by("date")
    if subject_filter:
        lessons_qs = lessons_qs.filter(subject_id=subject_filter)
    if difficulty_filter:
        lessons_qs = lessons_qs.filter(difficulty=difficulty_filter)
    if query:
        lessons_qs = lessons_qs.filter(
            Q(title__icontains=query)
            | Q(excerpt__icontains=query)
            | Q(content__icontains=query)
            | Q(subject__name__icontains=query)
        )
    if upcoming_only:
        lessons_qs = lessons_qs.filter(date__gte=timezone.localdate())

    completed_ids, accessible_ids, locked_reasons = compute_accessibility(
        user, subjects
    )

    lessons = list(lessons_qs)
    for lesson in lessons:
        lesson.is_completed = lesson.id in completed_ids
        lesson.is_accessible = lesson.id in accessible_ids
        lesson.locked_reason = locked_reasons.get(lesson.id)

    learning_paths = LearningPath.objects.prefetch_related(
        Prefetch(
            "items",
            queryset=LearningPathLesson.objects.select_related(
                "lesson", "lesson__subject"
            ).order_by("order"),
        )
    ).order_by("title")

    lesson_blocks = build_lesson_blocks(
        subjects, lessons, completed_ids, accessible_ids, learning_paths
    )

    recommendations = refresh_recommendations(user)
    badge_summary = get_badge_summary(user)
    progress = build_overall_progress(user)

    filters = {
        "query": query,
        "subject": subject_filter,
        "difficulty": difficulty_filter,
        "upcoming": upcoming_only,
    }

    upcoming_lessons = (
        Lesson.objects.select_related("subject")
        .filter(date__gte=timezone.localdate())
        .order_by("date")[:5]
    )
    latest_lessons = Lesson.objects.select_related("subject").order_by(
        "-updated_at", "-created_at"
    )[:5]

    result = {
        "subjects": subjects,
        "lessons": lessons,
        "completed_ids": completed_ids,
        "accessible_lessons": accessible_ids,
        "locked_reasons": locked_reasons,
        "recommendations": recommendations,
        "badge_summary": badge_summary,
        "highlighted_badges": badge_summary.get("highlighted", []),
        "filters": filters,
        "difficulty_choices": Lesson.DIFFICULTY_CHOICES,
        "upcoming_lessons": upcoming_lessons,
        "latest_lessons": latest_lessons,
        "lesson_blocks": lesson_blocks,
        "progress": progress,
    }

    # cache the result if requested (store Python objects in local memory cache)
    if use_cache and cache_key:
        try:
            cache.set(cache_key, result, timeout=cache_timeout)
        except Exception:
            # cache failures should not break functionality
            pass

    return result
