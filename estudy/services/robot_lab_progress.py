from __future__ import annotations

from typing import Any

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from ..models import RobotLabLevelProgress
from .robot_lab_levels import next_level_id, ordered_level_ids


def _ordered_progress_map(user: User) -> dict[str, RobotLabLevelProgress]:
    rows = RobotLabLevelProgress.objects.filter(user=user)
    return {row.level_id: row for row in rows}


@transaction.atomic
def ensure_robot_lab_progress_rows(user: User) -> dict[str, RobotLabLevelProgress]:
    level_ids = ordered_level_ids()
    if not level_ids:
        return {}

    existing = _ordered_progress_map(user)
    changed = False
    for level_id in level_ids:
        if level_id in existing:
            continue
        existing[level_id] = RobotLabLevelProgress.objects.create(
            user=user,
            level_id=level_id,
            unlocked=False,
        )
        changed = True

    first_id = level_ids[0]
    first_row = existing[first_id]
    if not first_row.unlocked:
        first_row.unlocked = True
        first_row.save(update_fields=["unlocked", "updated_at"])
        changed = True

    # Linear unlock: completing level N unlocks N+1.
    for level_id in level_ids:
        row = existing[level_id]
        nxt = next_level_id(level_id)
        if not nxt:
            continue
        next_row = existing[nxt]
        if row.completed and not next_row.unlocked:
            next_row.unlocked = True
            next_row.save(update_fields=["unlocked", "updated_at"])
            changed = True

    if changed:
        existing = _ordered_progress_map(user)
    return existing


def serialize_robot_lab_levels_with_progress(user: User) -> list[dict[str, Any]]:
    from .robot_lab_levels import list_level_entries

    progress_map = ensure_robot_lab_progress_rows(user)
    rows: list[dict[str, Any]] = []
    for entry in list_level_entries():
        level_id = str(entry.get("id"))
        progress = progress_map.get(level_id)
        rows.append(
            {
                "id": level_id,
                "title": entry.get("title") or level_id,
                "goal": entry.get("goal") or "",
                "concepts": entry.get("concepts") or [],
                "difficulty": entry.get("difficulty") or "easy",
                "difficulty_label": entry.get("difficulty_label")
                or entry.get("difficulty")
                or "easy",
                "world": entry.get("world", 1),
                "order": entry.get("order", 1),
                "xp_reward": int(entry.get("xp_reward") or 0),
                "mode": entry.get("mode") or "code",
                "mode_label": entry.get("mode_label") or "Mod Cod",
                "ui_stage": entry.get("ui_stage") or "code",
                "ui_stage_label": entry.get("ui_stage_label") or "Cod complet",
                "recommended_age": entry.get("recommended_age") or "11+",
                "unlocked": bool(progress.unlocked) if progress else False,
                "completed": bool(progress.completed) if progress else False,
                "concept_labels": entry.get("concept_labels") or entry.get("concepts") or [],
                "best_steps": int(progress.best_steps)
                if progress and progress.best_steps
                else None,
                "attempts_count": int(progress.attempts_count) if progress else 0,
            }
        )
    return rows


def build_robot_lab_progress_summary(user: User) -> dict[str, Any]:
    levels = serialize_robot_lab_levels_with_progress(user)
    total = len(levels)
    completed = sum(1 for row in levels if row.get("completed"))
    unlocked = sum(1 for row in levels if row.get("unlocked"))
    percent = round((completed / total) * 100) if total else 0
    return {
        "total_levels": total,
        "completed_levels": completed,
        "unlocked_levels": unlocked,
        "progress_percent": percent,
        "levels": levels,
    }


@transaction.atomic
def apply_robot_lab_run_progress(
    *,
    user: User,
    level_id: str,
    solved: bool,
    steps_used: int,
    xp_reward: int,
) -> dict[str, Any]:
    progress_map = ensure_robot_lab_progress_rows(user)
    row = progress_map[str(level_id)]
    row.attempts_count += 1
    xp_granted = 0

    if solved:
        if not row.completed:
            row.completed = True
            row.completed_at = timezone.now()
            row.xp_awarded_total += max(0, int(xp_reward))
            xp_granted = max(0, int(xp_reward))
        if steps_used > 0 and (row.best_steps is None or steps_used < row.best_steps):
            row.best_steps = steps_used

    row.save(
        update_fields=[
            "attempts_count",
            "completed",
            "completed_at",
            "best_steps",
            "xp_awarded_total",
            "updated_at",
        ]
    )

    # Recompute unlock chain after potential completion.
    ensure_robot_lab_progress_rows(user)

    return {
        "xp_granted": xp_granted,
        "level_progress": {
            "level_id": row.level_id,
            "unlocked": row.unlocked,
            "completed": row.completed,
            "best_steps": row.best_steps,
            "attempts_count": row.attempts_count,
            "xp_awarded_total": row.xp_awarded_total,
        },
        "summary": build_robot_lab_progress_summary(user),
    }
