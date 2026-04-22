from __future__ import annotations

from typing import Any, Dict, List

from ..models import LearningPath, LessonProgress
from .service_result import BaseServiceResult


def build_world_map(user) -> BaseServiceResult:
    """Build a list of learning paths with node state (completed / available / locked)
    for rendering as a world-map.

    A node is *completed* when the user has a completed LessonProgress for it.
    A node is *available* when it is the first uncompleted node in its path.
    Everything else is *locked*.
    """
    paths = LearningPath.objects.prefetch_related("items__lesson").all()

    completed_lesson_ids = set(
        LessonProgress.objects.filter(user=user, completed=True).values_list(
            "lesson_id", flat=True
        )
    )

    result: List[Dict[str, Any]] = []

    for path in paths:
        items = list(path.items.select_related("lesson").order_by("order"))
        first_incomplete_found = False
        nodes: List[Dict[str, Any]] = []

        for item in items:
            lesson = item.lesson
            is_completed = lesson.pk in completed_lesson_ids

            if is_completed:
                state = "completed"
            elif not first_incomplete_found:
                state = "available"
                first_incomplete_found = True
            else:
                state = "locked"

            nodes.append(
                {
                    "lesson": lesson,
                    "order": item.order,
                    "state": state,
                    "xp_reward": lesson.xp_reward,
                    "difficulty": lesson.difficulty,
                    "slug": lesson.slug,
                }
            )

        result.append(
            {
                "path": path,
                "nodes": nodes,
            }
        )

    return BaseServiceResult.ok(data={"paths": result})
