import json

from django.core.cache import cache
from django.http import JsonResponse
from django.test import RequestFactory, TestCase, override_settings

from .middleware import RequestIdempotencyMiddleware
from .services.idempotency import (
    ACTION_CACHED,
    ACTION_CONFLICT,
    ACTION_LOCKED,
    ACTION_PROCEED,
    ACTION_SKIP,
    IDEMPOTENCY_HEADER_META,
    build_cached_response,
    resolve_idempotency_request,
    store_idempotency_response,
)

PATH_PREFIX = "/estudy/tests/"
REQUEST_PATH = "/estudy/tests/1/submit/"
IDEMPOTENCY_KEY = "demo-key"
ALT_IDEMPOTENCY_KEY = "alt-key"
CONTENT_TYPE_JSON = "application/json"
STATUS_BAD_REQUEST = 400
COUNTER_START = 0
COUNTER_INCREMENT = 1
EXPECTED_SINGLE_CALL = 1


class IdempotencyServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

    def _build_request(self, body: dict, key: str | None):
        payload = json.dumps(body)
        request = self.factory.post(
            REQUEST_PATH, data=payload, content_type=CONTENT_TYPE_JSON
        )
        if key:
            request.META[IDEMPOTENCY_HEADER_META] = key
        return request

    @override_settings(
        ESTUDY_IDEMPOTENCY_ENABLED=True, ESTUDY_IDEMPOTENCY_PATH_PREFIXES=[PATH_PREFIX]
    )
    def test_skip_without_key(self):
        request = self._build_request({"value": "a"}, key=None)
        result = resolve_idempotency_request(request)
        decision = result.data["decision"]

        self.assertEqual(decision.action, ACTION_SKIP)

    @override_settings(
        ESTUDY_IDEMPOTENCY_ENABLED=True, ESTUDY_IDEMPOTENCY_PATH_PREFIXES=[PATH_PREFIX]
    )
    def test_cached_response_for_same_key(self):
        request = self._build_request({"value": "a"}, key=IDEMPOTENCY_KEY)
        result = resolve_idempotency_request(request)
        decision = result.data["decision"]
        self.assertEqual(decision.action, ACTION_PROCEED)

        response = JsonResponse({"ok": True})
        store_idempotency_response(decision.context, response)

        repeat = self._build_request({"value": "a"}, key=IDEMPOTENCY_KEY)
        cached = resolve_idempotency_request(repeat).data["decision"]
        self.assertEqual(cached.action, ACTION_CACHED)
        cached_response = build_cached_response(cached.cache_entry)

        self.assertEqual(cached_response.content, response.content)

    @override_settings(
        ESTUDY_IDEMPOTENCY_ENABLED=True, ESTUDY_IDEMPOTENCY_PATH_PREFIXES=[PATH_PREFIX]
    )
    def test_conflict_on_different_body(self):
        request = self._build_request({"value": "a"}, key=IDEMPOTENCY_KEY)
        decision = resolve_idempotency_request(request).data["decision"]
        response = JsonResponse({"ok": True})
        store_idempotency_response(decision.context, response)

        different_request = self._build_request({"value": "b"}, key=IDEMPOTENCY_KEY)
        conflict = resolve_idempotency_request(different_request).data["decision"]
        self.assertEqual(conflict.action, ACTION_CONFLICT)

    @override_settings(
        ESTUDY_IDEMPOTENCY_ENABLED=True, ESTUDY_IDEMPOTENCY_PATH_PREFIXES=[PATH_PREFIX]
    )
    def test_locked_when_inflight(self):
        request = self._build_request({"value": "a"}, key=ALT_IDEMPOTENCY_KEY)
        first = resolve_idempotency_request(request).data["decision"]
        self.assertEqual(first.action, ACTION_PROCEED)

        second_request = self._build_request({"value": "a"}, key=ALT_IDEMPOTENCY_KEY)
        locked = resolve_idempotency_request(second_request).data["decision"]
        self.assertEqual(locked.action, ACTION_LOCKED)

        response = JsonResponse({"ok": True})
        store_idempotency_response(first.context, response)

    @override_settings(
        ESTUDY_IDEMPOTENCY_ENABLED=True, ESTUDY_IDEMPOTENCY_PATH_PREFIXES=[PATH_PREFIX]
    )
    def test_error_response_not_cached(self):
        request = self._build_request({"value": "a"}, key=IDEMPOTENCY_KEY)
        decision = resolve_idempotency_request(request).data["decision"]
        response = JsonResponse({"error": "bad"}, status=STATUS_BAD_REQUEST)
        store_idempotency_response(decision.context, response)

        repeat = self._build_request({"value": "a"}, key=IDEMPOTENCY_KEY)
        follow_up = resolve_idempotency_request(repeat).data["decision"]
        self.assertEqual(follow_up.action, ACTION_PROCEED)


class RequestIdempotencyMiddlewareTests(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

    @override_settings(
        ESTUDY_IDEMPOTENCY_ENABLED=True, ESTUDY_IDEMPOTENCY_PATH_PREFIXES=[PATH_PREFIX]
    )
    def test_middleware_returns_cached_response(self):
        counter = {"count": COUNTER_START}

        def view(_request):
            counter["count"] += COUNTER_INCREMENT
            return JsonResponse({"count": counter["count"]})

        middleware = RequestIdempotencyMiddleware(view)
        first_request = self.factory.post(
            REQUEST_PATH,
            data=json.dumps({"value": "a"}),
            content_type=CONTENT_TYPE_JSON,
        )
        first_request.META[IDEMPOTENCY_HEADER_META] = IDEMPOTENCY_KEY
        second_request = self.factory.post(
            REQUEST_PATH,
            data=json.dumps({"value": "a"}),
            content_type=CONTENT_TYPE_JSON,
        )
        second_request.META[IDEMPOTENCY_HEADER_META] = IDEMPOTENCY_KEY

        first_response = middleware(first_request)
        second_response = middleware(second_request)

        self.assertEqual(first_response.content, second_response.content)
        self.assertEqual(counter["count"], EXPECTED_SINGLE_CALL)
