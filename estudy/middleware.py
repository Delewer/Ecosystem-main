from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse

from .services.idempotency import (
    ACTION_CACHED,
    ACTION_CONFLICT,
    ACTION_LOCKED,
    ACTION_PROCEED,
    build_cached_response,
    build_conflict_response,
    build_locked_response,
    resolve_idempotency_request,
    store_idempotency_response,
)
from .services.profiling import apply_profile_headers, finish_profile, start_profile
from .services.rate_limit import (
    RateLimitSnapshot,
    apply_rate_limit_headers,
    check_rate_limit,
)

HTTP_STATUS_TOO_MANY_REQUESTS = 429
RATE_LIMIT_ERROR_MESSAGE = "Rate limit exceeded"


class RequestProfilingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        context = start_profile(request)
        response = self.get_response(request)
        if context is None:
            return response
        snapshot = finish_profile(context, response)
        apply_profile_headers(response, snapshot)
        return response


class RequestRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        result = check_rate_limit(request)
        snapshot = RateLimitSnapshot(**result.data)
        if not snapshot.allowed:
            response = JsonResponse(
                {
                    "error": RATE_LIMIT_ERROR_MESSAGE,
                    "limit": snapshot.limit,
                    "remaining": snapshot.remaining,
                    "reset_seconds": snapshot.reset_seconds,
                },
                status=HTTP_STATUS_TOO_MANY_REQUESTS,
            )
            apply_rate_limit_headers(response, snapshot)
            return response

        response = self.get_response(request)
        apply_rate_limit_headers(response, snapshot)
        return response


class RequestIdempotencyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        result = resolve_idempotency_request(request)
        decision = result.data["decision"]
        if decision.action == ACTION_CACHED and decision.cache_entry:
            return build_cached_response(decision.cache_entry)
        if decision.action == ACTION_CONFLICT:
            return build_conflict_response()
        if decision.action == ACTION_LOCKED:
            return build_locked_response()
        if decision.action != ACTION_PROCEED or decision.context is None:
            return self.get_response(request)

        response = self.get_response(request)
        store_idempotency_response(decision.context, response)
        return response
