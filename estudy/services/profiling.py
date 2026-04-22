from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from django.db import connection
from django.http import HttpRequest, HttpResponse

SECONDS_TO_MILLISECONDS = 1000.0
PROFILE_HEADER = "X-Debug-Profile"
PROFILE_QUERY_PARAM = "profile"
PROFILE_ENABLE_VALUE = "1"
PROFILE_SETTING_ALWAYS = "ESTUDY_PROFILE_ALWAYS"
PROFILE_HEADER_PREFIX = "X-Profile-"
HEADER_DURATION = f"{PROFILE_HEADER_PREFIX}Duration-Ms"
HEADER_QUERY_COUNT = f"{PROFILE_HEADER_PREFIX}Query-Count"
HEADER_QUERY_TIME = f"{PROFILE_HEADER_PREFIX}Query-Time-Ms"
ZERO_TIME_MS = 0.0
ZERO_COUNT = 0


@dataclass(frozen=True)
class RequestProfileContext:
    path: str
    method: str
    start_time: float
    query_count: int
    query_time_ms: float


@dataclass(frozen=True)
class ProfileSnapshot:
    path: str
    method: str
    status_code: int
    duration_ms: float
    query_count: int
    query_time_ms: float

    def as_headers(self) -> dict[str, str]:
        return {
            HEADER_DURATION: f"{self.duration_ms:.2f}",
            HEADER_QUERY_COUNT: str(self.query_count),
            HEADER_QUERY_TIME: f"{self.query_time_ms:.2f}",
        }


def _profile_always_enabled() -> bool:
    return bool(getattr(settings, PROFILE_SETTING_ALWAYS, False))


def _has_profile_header(request: HttpRequest) -> bool:
    return request.headers.get(PROFILE_HEADER, "") == PROFILE_ENABLE_VALUE


def _has_profile_query(request: HttpRequest) -> bool:
    return request.GET.get(PROFILE_QUERY_PARAM, "") == PROFILE_ENABLE_VALUE


def should_profile(request: HttpRequest) -> bool:
    if not settings.DEBUG:
        return False
    if _profile_always_enabled():
        return True
    if _has_profile_header(request) or _has_profile_query(request):
        return True
    # In debug mode profile by default for local diagnostics.
    return True


def _query_stats() -> tuple[int, float]:
    try:
        queries = connection.queries
    except Exception:
        return ZERO_COUNT, ZERO_TIME_MS

    total_time_ms = ZERO_TIME_MS
    for entry in queries:
        raw_time = entry.get("time")
        try:
            total_time_ms += float(raw_time) * SECONDS_TO_MILLISECONDS
        except (TypeError, ValueError):
            continue
    return len(queries), total_time_ms


def start_profile(request: HttpRequest) -> Optional[RequestProfileContext]:
    if not should_profile(request):
        return None
    from time import perf_counter

    query_count, query_time_ms = _query_stats()
    return RequestProfileContext(
        path=request.path,
        method=request.method,
        start_time=perf_counter(),
        query_count=query_count,
        query_time_ms=query_time_ms,
    )


def finish_profile(
    context: RequestProfileContext, response: HttpResponse
) -> ProfileSnapshot:
    from time import perf_counter

    end_time = perf_counter()
    total_ms = (end_time - context.start_time) * SECONDS_TO_MILLISECONDS
    end_query_count, end_query_time_ms = _query_stats()
    delta_queries = max(ZERO_COUNT, end_query_count - context.query_count)
    delta_time_ms = max(ZERO_TIME_MS, end_query_time_ms - context.query_time_ms)
    return ProfileSnapshot(
        path=context.path,
        method=context.method,
        status_code=response.status_code,
        duration_ms=total_ms,
        query_count=delta_queries,
        query_time_ms=delta_time_ms,
    )


def apply_profile_headers(response: HttpResponse, snapshot: ProfileSnapshot) -> None:
    for key, value in snapshot.as_headers().items():
        response[key] = value
