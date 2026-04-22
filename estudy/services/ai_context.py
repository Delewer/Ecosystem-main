from __future__ import annotations

from typing import Iterable

MAX_CLUES = 4


def _clean_snippets(items: Iterable[str]) -> list[str]:
    return [item.strip() for item in items if item and item.strip()]


def build_lesson_clues(lesson) -> list[str]:
    if not lesson:
        return []

    clues: list[str] = []

    intro = (lesson.theory_intro or lesson.excerpt or "").strip()
    if intro:
        clues.append(intro)

    theory_takeaways = _clean_snippets(getattr(lesson, "theory_takeaways", []))
    method_takeaways = _clean_snippets(lesson.theory_points())
    clues.extend(theory_takeaways or method_takeaways)

    practice = getattr(lesson, "practice", None)
    if practice:
        clues.extend(_clean_snippets([practice.instructions, practice.intro]))

    return clues[:MAX_CLUES]
