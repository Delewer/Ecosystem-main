from __future__ import annotations

from typing import Any

from django.contrib.auth.models import User
from django.db import transaction

from ..models import RobotLabLevelProgress, RobotLabSkin, UserRobotLabSkin
from .robot_lab_levels import list_level_entries

WORLD_META: list[dict[str, Any]] = [
    {
        "world_id": 1,
        "name": "Gradina",
        "theme": "garden",
        "description": "Sectorul verde — invata ordinea comenzilor.",
        "unlock_condition": None,
        "skin_reward": None,
    },
    {
        "world_id": 2,
        "name": "Pestera de Gheata",
        "theme": "ice",
        "description": "Pardoseli de gheata — stapaneste buclele!",
        "unlock_condition": "complete_world_1",
        "skin_reward": "blaze",
    },
    {
        "world_id": 3,
        "name": "Vulcanul",
        "theme": "volcano",
        "description": "Lave si cronometre — invata conditiile.",
        "unlock_condition": "complete_world_2",
        "skin_reward": "frosty",
    },
    {
        "world_id": 4,
        "name": "Statia Spatiala",
        "theme": "space",
        "description": "Gravitatie zero — descopera functiile.",
        "unlock_condition": "complete_world_3",
        "skin_reward": "nova",
    },
    {
        "world_id": 5,
        "name": "Nucleul Final",
        "theme": "core",
        "description": "Toate temele combinate — algoritmii.",
        "unlock_condition": "complete_world_4",
        "skin_reward": "omega",
    },
]

SKIN_DEFINITIONS: list[dict[str, Any]] = [
    {
        "key": "zipp",
        "name": "ZIPP",
        "unlock_condition": "",
        "svg_file": "robot_zipp.svg",
        "ordering": 0,
    },
    {
        "key": "blaze",
        "name": "BLAZE",
        "unlock_condition": "complete_world_2",
        "svg_file": "robot_blaze.svg",
        "ordering": 1,
    },
    {
        "key": "frosty",
        "name": "FROSTY",
        "unlock_condition": "complete_world_3",
        "svg_file": "robot_frosty.svg",
        "ordering": 2,
    },
    {
        "key": "nova",
        "name": "NOVA",
        "unlock_condition": "complete_world_4",
        "svg_file": "robot_nova.svg",
        "ordering": 3,
    },
    {
        "key": "omega",
        "name": "OMEGA",
        "unlock_condition": "complete_world_5_perfect",
        "svg_file": "robot_omega.svg",
        "ordering": 4,
    },
]

LEVELS_PER_WORLD = 6


def _world_level_ids(world_id: int) -> list[str]:
    """Return ordered level IDs for a given world."""
    entries = list_level_entries()
    return [str(e["id"]) for e in entries if int(e.get("world", 0)) == world_id]


def _world_completed(user: User, world_id: int) -> bool:
    """Check if user has completed ALL levels in a world."""
    level_ids = _world_level_ids(world_id)
    if not level_ids:
        return False
    completed = RobotLabLevelProgress.objects.filter(
        user=user, level_id__in=level_ids, completed=True
    ).count()
    return completed >= len(level_ids)


def _world_perfect(user: User, world_id: int) -> bool:
    """Check if user has 3 stars on every level in a world."""
    level_ids = _world_level_ids(world_id)
    if not level_ids:
        return False
    perfect = RobotLabLevelProgress.objects.filter(
        user=user, level_id__in=level_ids, completed=True, stars_earned=3
    ).count()
    return perfect >= len(level_ids)


def _world_stars(user: User, world_id: int) -> int:
    level_ids = _world_level_ids(world_id)
    if not level_ids:
        return 0
    rows = RobotLabLevelProgress.objects.filter(user=user, level_id__in=level_ids)
    return sum(row.stars_earned for row in rows)


def is_world_unlocked(user: User, world_id: int) -> bool:
    meta = next((w for w in WORLD_META if w["world_id"] == world_id), None)
    if not meta:
        return False
    condition = meta.get("unlock_condition")
    if not condition:
        return True  # World 1 is always unlocked
    # condition is "complete_world_N"
    try:
        required_world = int(condition.split("_")[-1])
    except (ValueError, IndexError):
        return False
    return _world_completed(user, required_world)


def list_worlds_with_status(user: User) -> list[dict[str, Any]]:
    """Return all worlds with unlock status, star counts, and per-level progress."""
    level_entries = list_level_entries()
    entry_by_id = {str(e["id"]): e for e in level_entries}
    progress_rows = {
        row.level_id: row for row in RobotLabLevelProgress.objects.filter(user=user)
    }

    result = []
    for meta in WORLD_META:
        wid = meta["world_id"]
        unlocked = is_world_unlocked(user, wid)
        level_ids = _world_level_ids(wid)
        max_stars = len(level_ids) * 3

        completed_levels = []
        level_stars: dict[str, int] = {}
        level_titles: dict[str, str] = {}
        level_xp: dict[str, int] = {}
        stars = 0
        for lid in level_ids:
            entry = entry_by_id.get(lid, {})
            level_titles[lid] = str(entry.get("title") or lid)
            level_xp[lid] = int(entry.get("xp_reward") or 0)
            row = progress_rows.get(lid)
            if unlocked and row:
                if row.completed:
                    completed_levels.append(lid)
                earned = int(row.stars_earned or 0)
                level_stars[lid] = earned
                stars += earned

        unlock_hint = ""
        condition = meta.get("unlock_condition")
        if condition and not unlocked and condition.startswith("complete_world_"):
            try:
                required_world = int(condition.split("_")[-1])
                required_meta = next(
                    (w for w in WORLD_META if w["world_id"] == required_world), None
                )
                if required_meta:
                    unlock_hint = f"Termina: {required_meta['name']}"
            except (ValueError, IndexError):
                pass

        result.append(
            {
                "world_id": wid,
                "name": meta["name"],
                "theme": meta["theme"],
                "description": meta["description"],
                "unlocked": unlocked,
                "completed": _world_completed(user, wid) if unlocked else False,
                "stars": stars,
                "max_stars": max_stars,
                "level_ids": level_ids,
                "completed_levels": completed_levels,
                "level_stars": level_stars,
                "level_titles": level_titles,
                "level_xp": level_xp,
                "unlock_hint": unlock_hint,
            }
        )
    return result


def ensure_default_skin(user: User) -> None:
    """Ensure user has the default ZIPP skin unlocked and active."""
    zipp = RobotLabSkin.objects.filter(key="zipp").first()
    if not zipp:
        return
    obj, created = UserRobotLabSkin.objects.get_or_create(
        user=user,
        skin=zipp,
        defaults={"is_active": True},
    )
    if created:
        return
    # Ensure at least one skin is active
    if not UserRobotLabSkin.objects.filter(user=user, is_active=True).exists():
        obj.is_active = True
        obj.save(update_fields=["is_active"])


def check_skin_unlocks(user: User) -> list[str]:
    """Check world completions and unlock any newly earned skins. Returns list of newly unlocked skin keys."""
    newly_unlocked = []
    for skin_def in SKIN_DEFINITIONS:
        condition = skin_def["unlock_condition"]
        if not condition:
            continue  # Default skin, handled by ensure_default_skin

        skin = RobotLabSkin.objects.filter(key=skin_def["key"]).first()
        if not skin:
            continue

        # Already unlocked?
        if UserRobotLabSkin.objects.filter(user=user, skin=skin).exists():
            continue

        # Check condition
        earned = False
        if condition.startswith("complete_world_") and not condition.endswith(
            "_perfect"
        ):
            try:
                wid = int(condition.split("_")[-1])
                earned = _world_completed(user, wid)
            except (ValueError, IndexError):
                pass
        elif condition.endswith("_perfect"):
            try:
                wid = int(condition.replace("_perfect", "").split("_")[-1])
                earned = _world_perfect(user, wid)
            except (ValueError, IndexError):
                pass

        if earned:
            UserRobotLabSkin.objects.create(user=user, skin=skin)
            newly_unlocked.append(skin_def["key"])

    return newly_unlocked


def list_skins_with_status(user: User) -> list[dict[str, Any]]:
    """Return all skins with unlock status for the user."""
    ensure_default_skin(user)
    all_skins = RobotLabSkin.objects.all()
    user_skins = {
        us.skin_id: us
        for us in UserRobotLabSkin.objects.filter(user=user).select_related("skin")
    }
    result = []
    for skin in all_skins:
        user_skin = user_skins.get(skin.id)
        result.append(
            {
                "key": skin.key,
                "name": skin.name,
                "svg_file": skin.svg_file,
                "unlock_condition": skin.unlock_condition,
                "unlocked": user_skin is not None,
                "is_active": user_skin.is_active if user_skin else False,
                "unlocked_at": user_skin.unlocked_at.isoformat() if user_skin else None,
            }
        )
    return result


@transaction.atomic
def select_skin(user: User, skin_key: str) -> dict[str, Any]:
    """Set a skin as active for the user. Returns the updated skin info."""
    skin = RobotLabSkin.objects.filter(key=skin_key).first()
    if not skin:
        raise ValueError(f"Skin '{skin_key}' does not exist.")

    user_skin = UserRobotLabSkin.objects.filter(user=user, skin=skin).first()
    if not user_skin:
        raise ValueError(f"Skin '{skin_key}' is locked.")

    # Deactivate all other skins
    UserRobotLabSkin.objects.filter(user=user, is_active=True).update(is_active=False)
    user_skin.is_active = True
    user_skin.save(update_fields=["is_active"])

    return {
        "key": skin.key,
        "name": skin.name,
        "svg_file": skin.svg_file,
        "is_active": True,
    }


def get_active_skin(user: User) -> str:
    """Return the key of the user's active skin, defaulting to 'zipp'."""
    active = (
        UserRobotLabSkin.objects.filter(user=user, is_active=True)
        .select_related("skin")
        .first()
    )
    if active:
        return active.skin.key
    return "zipp"
