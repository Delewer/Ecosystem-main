from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from django.db import transaction
from django.utils import timezone

from ..models import EventLog, StreakFreezeBalance, UserProfile
from .audit_logger import log_event
from .service_result import BaseServiceResult

ERROR_MISSING_USER = "User is required"
ERROR_INVALID_AMOUNT = "Amount must be positive"
ERROR_INSUFFICIENT_TOKENS = "Not enough tokens"

WARNING_NO_PROFILE = "no_profile"
WARNING_NO_ACTION = "no_action"

ACTION_STREAK_START = "start"
ACTION_STREAK_INCREMENT = "increment"
ACTION_STREAK_RESET = "reset"
ACTION_STREAK_FREEZE_USED = "freeze_used"
ACTION_STREAK_NO_CHANGE = "no_change"

STREAK_START_VALUE = 1

MILESTONE_WEEK = 7
MILESTONE_TWO_WEEKS = 14
MILESTONE_MONTH = 30

REWARD_WEEK = 1
REWARD_TWO_WEEKS = 1
REWARD_MONTH = 2

STREAK_MILESTONE_REWARDS = (
    (MILESTONE_WEEK, REWARD_WEEK),
    (MILESTONE_TWO_WEEKS, REWARD_TWO_WEEKS),
    (MILESTONE_MONTH, REWARD_MONTH),
)

SOURCE_MILESTONE = "streak_milestone"


@dataclass(frozen=True)
class StreakUpdateSnapshot:
    action: str
    streak: int
    missed_days: int
    tokens_used: int
    tokens_awarded: int
    available_tokens: int


def _get_profile(user) -> Optional[UserProfile]:
    return getattr(user, "userprofile", None)


def _normalize_amount(amount) -> int:
    try:
        value = int(amount)
    except (TypeError, ValueError):
        return 0
    return value


def _local_date(value) -> Optional[date]:
    if value is None:
        return None
    return timezone.localdate(value)


def _last_activity_date(profile: UserProfile, *, user) -> Optional[date]:
    last_seen = profile.last_activity_at or profile.created_at or user.date_joined
    return _local_date(last_seen)


def _next_milestone_reward(*, streak: int, last_awarded: int) -> tuple[int, int]:
    for threshold, reward in STREAK_MILESTONE_REWARDS:
        if streak >= threshold and threshold > last_awarded:
            return threshold, reward
    return 0, 0


def _log_freeze_event(*, event_type: str, user, amount: int, metadata: dict) -> None:
    payload = {"amount": amount}
    payload.update(metadata)
    log_event(event_type, user=user, metadata=payload)


def grant_streak_freeze_tokens(
    *,
    user,
    amount: int,
    reason: str,
    awarded_streak: Optional[int] = None,
) -> BaseServiceResult:
    if user is None:
        return BaseServiceResult.fail(ERROR_MISSING_USER)
    amount_value = _normalize_amount(amount)
    if amount_value <= 0:
        return BaseServiceResult.fail(ERROR_INVALID_AMOUNT)

    with transaction.atomic():
        balance, _ = StreakFreezeBalance.objects.select_for_update().get_or_create(
            user=user
        )
        balance.available_tokens += amount_value
        if awarded_streak is not None:
            balance.last_awarded_streak = max(
                balance.last_awarded_streak, int(awarded_streak)
            )
        balance.save(update_fields=["available_tokens", "last_awarded_streak"])

    _log_freeze_event(
        event_type=EventLog.EVENT_STREAK_FREEZE_GRANT,
        user=user,
        amount=amount_value,
        metadata={
            "reason": reason,
            "available_tokens": balance.available_tokens,
            "last_awarded_streak": balance.last_awarded_streak,
        },
    )
    return BaseServiceResult.ok(
        data={
            "available_tokens": balance.available_tokens,
            "last_awarded_streak": balance.last_awarded_streak,
        }
    )


def consume_streak_freeze_tokens(
    *,
    user,
    amount: int,
    reason: str,
    missed_days: int,
) -> BaseServiceResult:
    if user is None:
        return BaseServiceResult.fail(ERROR_MISSING_USER)
    amount_value = _normalize_amount(amount)
    if amount_value <= 0:
        return BaseServiceResult.fail(ERROR_INVALID_AMOUNT)

    with transaction.atomic():
        balance, _ = StreakFreezeBalance.objects.select_for_update().get_or_create(
            user=user
        )
        if balance.available_tokens < amount_value:
            return BaseServiceResult.fail(ERROR_INSUFFICIENT_TOKENS)
        balance.available_tokens -= amount_value
        balance.used_tokens += amount_value
        balance.last_used_at = timezone.now()
        balance.save(update_fields=["available_tokens", "used_tokens", "last_used_at"])

    _log_freeze_event(
        event_type=EventLog.EVENT_STREAK_FREEZE_USE,
        user=user,
        amount=amount_value,
        metadata={
            "reason": reason,
            "missed_days": missed_days,
            "available_tokens": balance.available_tokens,
        },
    )
    return BaseServiceResult.ok(
        data={
            "available_tokens": balance.available_tokens,
            "used_tokens": balance.used_tokens,
        }
    )


def update_streak_on_activity(*, user, now=None) -> BaseServiceResult:
    if user is None:
        return BaseServiceResult.fail(ERROR_MISSING_USER)
    profile = _get_profile(user)
    if profile is None:
        return BaseServiceResult.ok(
            data={"action": ACTION_STREAK_NO_CHANGE}, warnings=[WARNING_NO_PROFILE]
        )

    now = now or timezone.now()
    today = _local_date(now)

    with transaction.atomic():
        profile = UserProfile.objects.select_for_update().get(pk=profile.pk)
        balance, _ = StreakFreezeBalance.objects.select_for_update().get_or_create(
            user=user
        )

        last_date = _last_activity_date(profile, user=user)
        if last_date is None or today is None:
            new_streak = max(profile.streak, STREAK_START_VALUE)
            action = ACTION_STREAK_START
            missed_days = 0
            tokens_used = 0
        elif today <= last_date:
            if profile.streak <= 0:
                new_streak = STREAK_START_VALUE
                action = ACTION_STREAK_START
            else:
                new_streak = profile.streak
                action = ACTION_STREAK_NO_CHANGE
            missed_days = 0
            tokens_used = 0
        else:
            day_delta = (today - last_date).days
            if day_delta == 1:
                new_streak = profile.streak + 1
                action = ACTION_STREAK_INCREMENT
                missed_days = 0
                tokens_used = 0
            else:
                missed_days = max(day_delta - 1, 0)
                if profile.streak > 0 and balance.available_tokens >= missed_days:
                    balance.available_tokens -= missed_days
                    balance.used_tokens += missed_days
                    balance.last_used_at = now
                    balance.save(
                        update_fields=[
                            "available_tokens",
                            "used_tokens",
                            "last_used_at",
                        ]
                    )
                    _log_freeze_event(
                        event_type=EventLog.EVENT_STREAK_FREEZE_USE,
                        user=user,
                        amount=missed_days,
                        metadata={
                            "reason": "streak_freeze",
                            "missed_days": missed_days,
                            "available_tokens": balance.available_tokens,
                        },
                    )
                    new_streak = profile.streak + 1
                    action = ACTION_STREAK_FREEZE_USED
                    tokens_used = missed_days
                else:
                    new_streak = STREAK_START_VALUE
                    action = ACTION_STREAK_RESET
                    tokens_used = 0

        tokens_awarded = 0
        milestone, reward = _next_milestone_reward(
            streak=new_streak, last_awarded=balance.last_awarded_streak
        )
        if reward > 0:
            balance.available_tokens += reward
            balance.last_awarded_streak = milestone
            balance.save(update_fields=["available_tokens", "last_awarded_streak"])
            _log_freeze_event(
                event_type=EventLog.EVENT_STREAK_FREEZE_GRANT,
                user=user,
                amount=reward,
                metadata={
                    "reason": SOURCE_MILESTONE,
                    "available_tokens": balance.available_tokens,
                    "milestone": milestone,
                },
            )
            tokens_awarded = reward

        update_fields = ["last_activity_at"]
        profile.last_activity_at = now
        if new_streak != profile.streak:
            profile.streak = new_streak
            update_fields.append("streak")
        profile.save(update_fields=update_fields)

    snapshot = StreakUpdateSnapshot(
        action=action,
        streak=profile.streak,
        missed_days=missed_days,
        tokens_used=tokens_used,
        tokens_awarded=tokens_awarded,
        available_tokens=balance.available_tokens,
    )
    return BaseServiceResult.ok(data={"snapshot": snapshot})
