from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone

from ..models import EventLog, UserProfile
from .audit_logger import log_event
from .service_result import BaseServiceResult

SETTING_ENABLED = "ESTUDY_XP_DECAY_ENABLED"
SETTING_START_DAYS = "ESTUDY_XP_DECAY_START_DAYS"
SETTING_POINTS_PER_DAY = "ESTUDY_XP_DECAY_POINTS_PER_DAY"
SETTING_MIN_XP = "ESTUDY_XP_DECAY_MIN_XP"
SETTING_MIN_LEVEL = "ESTUDY_XP_DECAY_MIN_LEVEL"

DEFAULT_DECAY_ENABLED = False
DEFAULT_DECAY_START_DAYS = 7
DEFAULT_DECAY_POINTS_PER_DAY = 5
DEFAULT_MIN_XP = 0
DEFAULT_MIN_LEVEL = 1

LEVEL_BASE_XP = 100
LEVEL_GROWTH_FACTOR = 25

WARNING_DECAY_DISABLED = "decay_disabled"
WARNING_NO_PROFILE = "no_profile"
WARNING_NO_ACTIVITY = "no_activity"
WARNING_NO_DECAY = "no_decay"


@dataclass(frozen=True)
class XPDecaySnapshot:
    user_id: int
    previous_xp: int
    new_xp: int
    previous_level: int
    new_level: int
    days_inactive: int
    decay_days: int
    decay_points: int


def _get_setting(name: str, default):
    return getattr(settings, name, default)


def _min_xp() -> int:
    return int(_get_setting(SETTING_MIN_XP, DEFAULT_MIN_XP))


def _min_level() -> int:
    return int(_get_setting(SETTING_MIN_LEVEL, DEFAULT_MIN_LEVEL))


def _start_days() -> int:
    return int(_get_setting(SETTING_START_DAYS, DEFAULT_DECAY_START_DAYS))


def _points_per_day() -> int:
    return int(_get_setting(SETTING_POINTS_PER_DAY, DEFAULT_DECAY_POINTS_PER_DAY))


def _decay_enabled() -> bool:
    return bool(_get_setting(SETTING_ENABLED, DEFAULT_DECAY_ENABLED))


def _threshold_for_level(level: int) -> int:
    return LEVEL_BASE_XP + (level**2) * LEVEL_GROWTH_FACTOR


def _normalize_level(*, xp: int, current_level: int) -> int:
    level = max(_min_level(), int(current_level))
    while level > _min_level() and xp < _threshold_for_level(level - 1):
        level -= 1
    while xp >= _threshold_for_level(level):
        level += 1
    return level


def _last_activity(profile: UserProfile):
    return profile.last_activity_at or profile.created_at or profile.user.date_joined


def _days_inactive(last_seen, now) -> int:
    if not last_seen:
        return 0
    delta = now - last_seen
    return max(delta.days, 0)


def _decay_points(*, xp: int, days_inactive: int) -> tuple[int, int]:
    start_days = _start_days()
    if days_inactive <= start_days:
        return 0, 0
    decay_days = days_inactive - start_days
    points = max(decay_days * _points_per_day(), 0)
    max_points = max(xp - _min_xp(), 0)
    return min(points, max_points), decay_days


def apply_xp_decay(
    *, profile: UserProfile, now=None, force: bool = False
) -> BaseServiceResult:
    if not force and not _decay_enabled():
        return BaseServiceResult.ok(
            data={"changed": False},
            warnings=[WARNING_DECAY_DISABLED],
        )
    if profile is None:
        return BaseServiceResult.ok(
            data={"changed": False},
            warnings=[WARNING_NO_PROFILE],
        )

    now = now or timezone.now()
    last_seen = _last_activity(profile)
    if not last_seen:
        return BaseServiceResult.ok(
            data={"changed": False},
            warnings=[WARNING_NO_ACTIVITY],
        )

    days_inactive = _days_inactive(last_seen, now)
    decay_points, decay_days = _decay_points(xp=profile.xp, days_inactive=days_inactive)
    if decay_points <= 0:
        return BaseServiceResult.ok(
            data={"changed": False},
            warnings=[WARNING_NO_DECAY],
        )

    previous_xp = profile.xp
    previous_level = profile.level
    new_xp = max(previous_xp - decay_points, _min_xp())
    new_level = _normalize_level(xp=new_xp, current_level=previous_level)

    profile.xp = new_xp
    profile.level = max(new_level, _min_level())
    profile.save(update_fields=["xp", "level"])

    log_event(
        EventLog.EVENT_XP_DECAY,
        user=profile.user,
        metadata={
            "previous_xp": previous_xp,
            "new_xp": new_xp,
            "previous_level": previous_level,
            "new_level": profile.level,
            "days_inactive": days_inactive,
            "decay_days": decay_days,
            "decay_points": decay_points,
        },
    )

    snapshot = XPDecaySnapshot(
        user_id=profile.user_id,
        previous_xp=previous_xp,
        new_xp=new_xp,
        previous_level=previous_level,
        new_level=profile.level,
        days_inactive=days_inactive,
        decay_days=decay_days,
        decay_points=decay_points,
    )
    return BaseServiceResult.ok(data={"changed": True, "snapshot": snapshot})


def run_xp_decay(*, now=None) -> BaseServiceResult:
    if not _decay_enabled():
        return BaseServiceResult.ok(
            data={"processed": 0, "updated": 0},
            warnings=[WARNING_DECAY_DISABLED],
        )
    now = now or timezone.now()
    processed = 0
    updated = 0
    for profile in UserProfile.objects.select_related("user").all().iterator():
        processed += 1
        result = apply_xp_decay(profile=profile, now=now, force=True)
        if result.success and result.data.get("changed"):
            updated += 1
    return BaseServiceResult.ok(data={"processed": processed, "updated": updated})
