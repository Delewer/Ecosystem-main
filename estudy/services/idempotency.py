from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse

from .service_result import BaseServiceResult

IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_HEADER_META = "HTTP_IDEMPOTENCY_KEY"
IDEMPOTENCY_PREFIX = "estudy:idempotency"
IDEMPOTENCY_RESPONSE_PREFIX = "response"
IDEMPOTENCY_LOCK_PREFIX = "lock"

DEFAULT_METHODS = ("POST",)
DEFAULT_ENABLED = False

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DEFAULT_TTL_SECONDS = SECONDS_PER_MINUTE * MINUTES_PER_HOUR * HOURS_PER_DAY
DEFAULT_LOCK_SECONDS = SECONDS_PER_MINUTE

DEFAULT_STATUS_MIN = 200
DEFAULT_STATUS_MAX = 399

UNKNOWN_IDENTIFIER = "unknown"
DEFAULT_CONTENT_TYPE = "application/json"

ACTION_SKIP = "skip"
ACTION_CACHED = "cached"
ACTION_LOCKED = "locked"
ACTION_CONFLICT = "conflict"
ACTION_PROCEED = "proceed"

HTTP_STATUS_CONFLICT = 409

MESSAGE_CONFLICT = "Idempotency key conflict"
MESSAGE_IN_PROGRESS = "Idempotency request already in progress"

SETTING_ENABLED = "ESTUDY_IDEMPOTENCY_ENABLED"
SETTING_TTL = "ESTUDY_IDEMPOTENCY_TTL_SECONDS"
SETTING_LOCK_TTL = "ESTUDY_IDEMPOTENCY_LOCK_SECONDS"
SETTING_METHODS = "ESTUDY_IDEMPOTENCY_METHODS"
SETTING_PATH_PREFIXES = "ESTUDY_IDEMPOTENCY_PATH_PREFIXES"

CACHED_HEADERS = ("Content-Type",)


@dataclass(frozen=True)
class IdempotencyContext:
    key: str
    identifier: str
    request_hash: str
    response_key: str
    lock_key: str
    ttl_seconds: int
    lock_seconds: int


@dataclass(frozen=True)
class IdempotencyCacheEntry:
    status_code: int
    content: bytes
    content_type: str
    headers: dict[str, str]
    request_hash: str


@dataclass(frozen=True)
class IdempotencyDecision:
    action: str
    context: Optional[IdempotencyContext] = None
    cache_entry: Optional[IdempotencyCacheEntry] = None


def _is_enabled() -> bool:
    return bool(getattr(settings, SETTING_ENABLED, DEFAULT_ENABLED))


def _allowed_methods() -> tuple[str, ...]:
    methods = getattr(settings, SETTING_METHODS, DEFAULT_METHODS)
    if isinstance(methods, (list, tuple)):
        return tuple(str(item).upper() for item in methods if str(item))
    return DEFAULT_METHODS


def _path_prefixes() -> tuple[str, ...]:
    prefixes = getattr(settings, SETTING_PATH_PREFIXES, [])
    if isinstance(prefixes, (list, tuple)):
        return tuple(str(item) for item in prefixes if str(item))
    return tuple()


def _path_allowed(path: str) -> bool:
    prefixes = _path_prefixes()
    if not prefixes:
        return False
    return any(path.startswith(prefix) for prefix in prefixes)


def _ttl_seconds() -> int:
    try:
        ttl = int(getattr(settings, SETTING_TTL, DEFAULT_TTL_SECONDS))
    except (TypeError, ValueError):
        return DEFAULT_TTL_SECONDS
    return max(SECONDS_PER_MINUTE, ttl)


def _lock_seconds() -> int:
    try:
        ttl = int(getattr(settings, SETTING_LOCK_TTL, DEFAULT_LOCK_SECONDS))
    except (TypeError, ValueError):
        return DEFAULT_LOCK_SECONDS
    return max(SECONDS_PER_MINUTE, ttl)


def _client_identifier(request: HttpRequest) -> str:
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return str(getattr(user, "id", UNKNOWN_IDENTIFIER))
    return request.META.get("REMOTE_ADDR") or UNKNOWN_IDENTIFIER


def _request_hash(request: HttpRequest) -> str:
    payload = b"|".join(
        [
            request.method.encode("utf-8"),
            request.path.encode("utf-8"),
            request.body or b"",
        ]
    )
    return hashlib.sha256(payload).hexdigest()


def _response_cache_key(key: str, identifier: str, path: str) -> str:
    return (
        f"{IDEMPOTENCY_PREFIX}:{IDEMPOTENCY_RESPONSE_PREFIX}:{identifier}:{path}:{key}"
    )


def _lock_cache_key(key: str, identifier: str, path: str) -> str:
    return f"{IDEMPOTENCY_PREFIX}:{IDEMPOTENCY_LOCK_PREFIX}:{identifier}:{path}:{key}"


def _extract_cache_entry(raw: Mapping[str, Any]) -> Optional[IdempotencyCacheEntry]:
    try:
        return IdempotencyCacheEntry(
            status_code=int(raw["status_code"]),
            content=raw["content"],
            content_type=str(raw.get("content_type") or DEFAULT_CONTENT_TYPE),
            headers=dict(raw.get("headers") or {}),
            request_hash=str(raw["request_hash"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _cache_response(context: IdempotencyContext, response: HttpResponse) -> bool:
    if getattr(response, "streaming", False):
        return False
    status_code = getattr(response, "status_code", 0)
    if status_code < DEFAULT_STATUS_MIN or status_code > DEFAULT_STATUS_MAX:
        return False
    headers = {
        name: response.get(name) for name in CACHED_HEADERS if response.get(name)
    }
    entry = IdempotencyCacheEntry(
        status_code=status_code,
        content=bytes(response.content),
        content_type=response.get("Content-Type", DEFAULT_CONTENT_TYPE),
        headers=headers,
        request_hash=context.request_hash,
    )
    cache.set(
        context.response_key,
        entry.__dict__,
        timeout=context.ttl_seconds,
    )
    return True


def _release_lock(context: IdempotencyContext) -> None:
    cache.delete(context.lock_key)


def resolve_idempotency_request(request: HttpRequest) -> BaseServiceResult:
    if not _is_enabled():
        return BaseServiceResult.ok(
            data={"decision": IdempotencyDecision(action=ACTION_SKIP)}
        )
    if request.method.upper() not in _allowed_methods():
        return BaseServiceResult.ok(
            data={"decision": IdempotencyDecision(action=ACTION_SKIP)}
        )
    if not _path_allowed(request.path):
        return BaseServiceResult.ok(
            data={"decision": IdempotencyDecision(action=ACTION_SKIP)}
        )

    key = request.META.get(IDEMPOTENCY_HEADER_META, "").strip()
    if not key:
        return BaseServiceResult.ok(
            data={"decision": IdempotencyDecision(action=ACTION_SKIP)}
        )

    identifier = _client_identifier(request)
    request_hash = _request_hash(request)
    response_key = _response_cache_key(key, identifier, request.path)
    lock_key = _lock_cache_key(key, identifier, request.path)
    context = IdempotencyContext(
        key=key,
        identifier=identifier,
        request_hash=request_hash,
        response_key=response_key,
        lock_key=lock_key,
        ttl_seconds=_ttl_seconds(),
        lock_seconds=_lock_seconds(),
    )

    cached = cache.get(response_key)
    if cached:
        cache_entry = _extract_cache_entry(cached)
        if cache_entry is None:
            cache.delete(response_key)
        elif cache_entry.request_hash != request_hash:
            return BaseServiceResult.ok(
                data={
                    "decision": IdempotencyDecision(
                        action=ACTION_CONFLICT, context=context
                    )
                }
            )
        else:
            return BaseServiceResult.ok(
                data={
                    "decision": IdempotencyDecision(
                        action=ACTION_CACHED, context=context, cache_entry=cache_entry
                    )
                }
            )

    if not cache.add(lock_key, "1", timeout=context.lock_seconds):
        return BaseServiceResult.ok(
            data={
                "decision": IdempotencyDecision(action=ACTION_LOCKED, context=context)
            }
        )

    return BaseServiceResult.ok(
        data={"decision": IdempotencyDecision(action=ACTION_PROCEED, context=context)}
    )


def store_idempotency_response(
    context: IdempotencyContext, response: HttpResponse
) -> BaseServiceResult:
    stored = _cache_response(context, response)
    _release_lock(context)
    return BaseServiceResult.ok(data={"stored": stored})


def release_idempotency_lock(context: IdempotencyContext) -> None:
    _release_lock(context)


def build_cached_response(entry: IdempotencyCacheEntry) -> HttpResponse:
    response = HttpResponse(
        entry.content,
        status=entry.status_code,
        content_type=entry.content_type,
    )
    for name, value in entry.headers.items():
        response[name] = value
    return response


def build_conflict_response() -> HttpResponse:
    return JsonResponse({"error": MESSAGE_CONFLICT}, status=HTTP_STATUS_CONFLICT)


def build_locked_response() -> HttpResponse:
    return JsonResponse({"error": MESSAGE_IN_PROGRESS}, status=HTTP_STATUS_CONFLICT)
