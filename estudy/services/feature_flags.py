from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from django.conf import settings

from ..models import FeatureFlag
from .service_result import BaseServiceResult

MIN_ROLLOUT_PERCENT = 0
MAX_ROLLOUT_PERCENT = 100
ROLLOUT_BUCKETS = 100
DEFAULT_ROLLOUT_PERCENT = MAX_ROLLOUT_PERCENT
SETTINGS_KEY = "ESTUDY_FEATURE_FLAGS"
SOURCE_DEFAULT = "default"
META_DEFAULTED = "defaulted"
META_USER_ID = "user_id"
META_BUCKET = "bucket"


@dataclass(frozen=True)
class FeatureFlagSnapshot:
    key: str
    enabled: bool
    rollout_percentage: int
    source: str


def _normalize_rollout(value: Any) -> int:
    if value is None:
        return DEFAULT_ROLLOUT_PERCENT
    try:
        rollout = int(value)
    except (TypeError, ValueError):
        return MIN_ROLLOUT_PERCENT
    return max(MIN_ROLLOUT_PERCENT, min(MAX_ROLLOUT_PERCENT, rollout))


def _get_flag_from_db(key: str) -> Optional[FeatureFlagSnapshot]:
    flag = FeatureFlag.objects.filter(key=key).first()
    if not flag:
        return None
    return FeatureFlagSnapshot(
        key=flag.key,
        enabled=flag.enabled,
        rollout_percentage=_normalize_rollout(flag.rollout_percentage),
        source="database",
    )


def _get_flag_from_settings(key: str) -> Optional[FeatureFlagSnapshot]:
    flags = getattr(settings, SETTINGS_KEY, None)
    if not isinstance(flags, Mapping) or key not in flags:
        return None
    entry = flags[key]
    if isinstance(entry, Mapping):
        enabled = bool(entry.get("enabled", False))
        rollout = _normalize_rollout(entry.get("rollout_percentage"))
    else:
        enabled = bool(entry)
        rollout = DEFAULT_ROLLOUT_PERCENT if enabled else MIN_ROLLOUT_PERCENT
    return FeatureFlagSnapshot(
        key=key,
        enabled=enabled,
        rollout_percentage=rollout,
        source="settings",
    )


def get_flag_snapshot(key: str) -> Optional[FeatureFlagSnapshot]:
    return _get_flag_from_db(key) or _get_flag_from_settings(key)


def _bucket_for_user(flag_key: str, user_id: int) -> int:
    payload = f"{flag_key}:{user_id}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest, 16) % ROLLOUT_BUCKETS


def _normalize_user_id(user) -> Optional[int]:
    user_id = getattr(user, "id", None)
    try:
        return int(user_id) if user_id else None
    except (TypeError, ValueError):
        return None


def _build_result(
    *,
    flag_key: str,
    enabled: bool,
    rollout_percentage: int,
    source: str,
    defaulted: bool,
    user_id: Optional[int] = None,
    bucket: Optional[int] = None,
) -> BaseServiceResult:
    meta = {META_DEFAULTED: defaulted}
    if user_id is not None:
        meta[META_USER_ID] = user_id
    if bucket is not None:
        meta[META_BUCKET] = bucket
    return BaseServiceResult.ok(
        data={
            "key": flag_key,
            "enabled": enabled,
            "rollout_percentage": rollout_percentage,
            "source": source,
        },
        meta=meta,
    )


def evaluate_flag(
    flag_key: str, *, user=None, default: bool = False
) -> BaseServiceResult:
    snapshot = get_flag_snapshot(flag_key)
    if snapshot is None:
        enabled = bool(default)
        rollout_percentage = DEFAULT_ROLLOUT_PERCENT if enabled else MIN_ROLLOUT_PERCENT
        return _build_result(
            flag_key=flag_key,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            source=SOURCE_DEFAULT,
            defaulted=True,
        )

    if not snapshot.enabled:
        return _build_result(
            flag_key=flag_key,
            enabled=False,
            rollout_percentage=snapshot.rollout_percentage,
            source=snapshot.source,
            defaulted=False,
        )

    rollout = snapshot.rollout_percentage
    if rollout >= MAX_ROLLOUT_PERCENT:
        return _build_result(
            flag_key=flag_key,
            enabled=True,
            rollout_percentage=rollout,
            source=snapshot.source,
            defaulted=False,
        )
    if rollout <= MIN_ROLLOUT_PERCENT:
        return _build_result(
            flag_key=flag_key,
            enabled=False,
            rollout_percentage=rollout,
            source=snapshot.source,
            defaulted=False,
        )

    user_id = _normalize_user_id(user)
    if user_id is None:
        return _build_result(
            flag_key=flag_key,
            enabled=False,
            rollout_percentage=rollout,
            source=snapshot.source,
            defaulted=False,
        )

    bucket = _bucket_for_user(flag_key, user_id)
    enabled = bucket < rollout
    return _build_result(
        flag_key=flag_key,
        enabled=enabled,
        rollout_percentage=rollout,
        source=snapshot.source,
        defaulted=False,
        user_id=user_id,
        bucket=bucket,
    )


def is_enabled(flag_key: str, *, user=None, default: bool = False) -> bool:
    result = evaluate_flag(flag_key, user=user, default=default)
    return bool(result.data.get("enabled", default))
