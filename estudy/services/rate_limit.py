from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse

from .service_result import BaseServiceResult

SCOPE_ANON = "anon"
SCOPE_USER = "user"
UNKNOWN_IDENTIFIER = "unknown"

DEFAULT_RATE_LIMITS = {
    SCOPE_ANON: 60,
    SCOPE_USER: 120,
}
DEFAULT_WINDOW_SECONDS = 60
DEFAULT_LIMIT = 0
DEFAULT_REMAINING = 0
DEFAULT_RESET_SECONDS = 0
DEFAULT_COUNT = 1

RATE_LIMIT_SETTING_ENABLED = "ESTUDY_RATE_LIMIT_ENABLED"
RATE_LIMIT_SETTING_RATES = "ESTUDY_RATE_LIMIT_RATES"
RATE_LIMIT_SETTING_WINDOW = "ESTUDY_RATE_LIMIT_WINDOW_SECONDS"
RATE_LIMIT_SETTING_EXEMPT_PREFIXES = "ESTUDY_RATE_LIMIT_EXEMPT_PREFIXES"
TRUST_PROXY_SETTING = "ESTUDY_TRUST_PROXY_HEADERS"

HEADER_RATE_LIMIT_LIMIT = "X-RateLimit-Limit"
HEADER_RATE_LIMIT_REMAINING = "X-RateLimit-Remaining"
HEADER_RATE_LIMIT_RESET = "X-RateLimit-Reset"
HEADER_RETRY_AFTER = "Retry-After"

META_RATE_LIMITED = "rate_limited"

KEY_PREFIX = "estudy:rate-limit"


@dataclass(frozen=True)
class RateLimitSnapshot:
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int
    scope: str
    identifier: str
    cache_key: str

    def headers(self) -> dict[str, str]:
        return {
            HEADER_RATE_LIMIT_LIMIT: str(self.limit),
            HEADER_RATE_LIMIT_REMAINING: str(self.remaining),
            HEADER_RATE_LIMIT_RESET: str(self.reset_seconds),
        }


def _is_enabled() -> bool:
    return bool(getattr(settings, RATE_LIMIT_SETTING_ENABLED, False))


def _get_window_seconds() -> int:
    window = getattr(settings, RATE_LIMIT_SETTING_WINDOW, DEFAULT_WINDOW_SECONDS)
    try:
        value = int(window)
    except (TypeError, ValueError):
        return DEFAULT_WINDOW_SECONDS
    return value if value > 0 else DEFAULT_WINDOW_SECONDS


def _get_rate_limits() -> Mapping[str, int]:
    limits = getattr(settings, RATE_LIMIT_SETTING_RATES, None)
    if not isinstance(limits, Mapping):
        return DEFAULT_RATE_LIMITS
    return limits


def _normalize_limit(value: Any) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return max(DEFAULT_LIMIT, limit)


def _now_epoch() -> int:
    return int(time.time())


def _build_cache_key(scope: str, identifier: str, window_bucket: int) -> str:
    return f"{KEY_PREFIX}:{scope}:{identifier}:{window_bucket}"


def _window_bucket(now_epoch: int, window_seconds: int) -> int:
    return now_epoch // window_seconds


def _reset_seconds(now_epoch: int, window_seconds: int) -> int:
    elapsed = now_epoch % window_seconds
    remaining = window_seconds - elapsed
    return max(DEFAULT_RESET_SECONDS, remaining)


def _exempt_prefixes() -> tuple[str, ...]:
    prefixes = []
    static_url = getattr(settings, "STATIC_URL", "")
    if static_url:
        prefixes.append(static_url)
    media_url = getattr(settings, "MEDIA_URL", "")
    if media_url:
        prefixes.append(media_url)
    extra = getattr(settings, RATE_LIMIT_SETTING_EXEMPT_PREFIXES, [])
    if isinstance(extra, (list, tuple)):
        prefixes.extend(str(item) for item in extra if str(item))
    return tuple(prefixes)


def _is_exempt_path(path: str) -> bool:
    for prefix in _exempt_prefixes():
        if prefix and path.startswith(prefix):
            return True
    return False


def _client_ip(request: HttpRequest) -> str:
    if getattr(settings, TRUST_PROXY_SETTING, False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or UNKNOWN_IDENTIFIER
    return request.META.get("REMOTE_ADDR") or UNKNOWN_IDENTIFIER


def _scope_and_identifier(request: HttpRequest) -> tuple[str, str]:
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return SCOPE_USER, str(getattr(user, "id", UNKNOWN_IDENTIFIER))
    return SCOPE_ANON, _client_ip(request)


def _increment_counter(key: str, window_seconds: int) -> int:
    try:
        if cache.add(key, DEFAULT_COUNT, timeout=window_seconds):
            return DEFAULT_COUNT
        return int(cache.incr(key))
    except ValueError:
        cache.add(key, DEFAULT_COUNT, timeout=window_seconds)
        return DEFAULT_COUNT
    except Exception:
        return DEFAULT_COUNT


def check_rate_limit(request: HttpRequest) -> BaseServiceResult:
    if not _is_enabled():
        return BaseServiceResult.ok(
            data={
                "allowed": True,
                "limit": DEFAULT_LIMIT,
                "remaining": DEFAULT_REMAINING,
                "reset_seconds": DEFAULT_RESET_SECONDS,
                "scope": SCOPE_ANON,
                "identifier": UNKNOWN_IDENTIFIER,
                "cache_key": "",
            },
            meta={META_RATE_LIMITED: False},
        )

    if _is_exempt_path(request.path):
        return BaseServiceResult.ok(
            data={
                "allowed": True,
                "limit": DEFAULT_LIMIT,
                "remaining": DEFAULT_REMAINING,
                "reset_seconds": DEFAULT_RESET_SECONDS,
                "scope": SCOPE_ANON,
                "identifier": UNKNOWN_IDENTIFIER,
                "cache_key": "",
            },
            meta={META_RATE_LIMITED: False},
        )

    scope, identifier = _scope_and_identifier(request)
    limit = _normalize_limit(_get_rate_limits().get(scope, DEFAULT_LIMIT))
    if limit == DEFAULT_LIMIT:
        return BaseServiceResult.ok(
            data={
                "allowed": True,
                "limit": DEFAULT_LIMIT,
                "remaining": DEFAULT_REMAINING,
                "reset_seconds": DEFAULT_RESET_SECONDS,
                "scope": scope,
                "identifier": identifier,
                "cache_key": "",
            },
            meta={META_RATE_LIMITED: False},
        )

    window_seconds = _get_window_seconds()
    now_epoch = _now_epoch()
    bucket = _window_bucket(now_epoch, window_seconds)
    cache_key = _build_cache_key(scope, identifier, bucket)
    count = _increment_counter(cache_key, window_seconds)
    allowed = count <= limit
    remaining = max(DEFAULT_REMAINING, limit - count)
    reset_seconds = _reset_seconds(now_epoch, window_seconds)

    snapshot = RateLimitSnapshot(
        allowed=allowed,
        limit=limit,
        remaining=remaining,
        reset_seconds=reset_seconds,
        scope=scope,
        identifier=identifier,
        cache_key=cache_key,
    )
    return BaseServiceResult.ok(
        data=snapshot.__dict__, meta={META_RATE_LIMITED: not allowed}
    )


def apply_rate_limit_headers(
    response: HttpResponse, snapshot: RateLimitSnapshot
) -> None:
    for key, value in snapshot.headers().items():
        response[key] = value
    if not snapshot.allowed:
        response[HEADER_RETRY_AFTER] = str(snapshot.reset_seconds)
