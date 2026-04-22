from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from .middleware import RequestRateLimitMiddleware
from .services.rate_limit import (
    DEFAULT_LIMIT,
    DEFAULT_REMAINING,
    DEFAULT_RESET_SECONDS,
    HEADER_RATE_LIMIT_LIMIT,
    HEADER_RATE_LIMIT_REMAINING,
    HEADER_RATE_LIMIT_RESET,
    check_rate_limit,
)

DEFAULT_PATH = "/estudy/overview/"
DEFAULT_METHOD = "GET"
LIMIT_ONE = 1
ALLOWED_TRUE = True
ALLOWED_FALSE = False
EXPECTED_STATUS_TOO_MANY = 429


class RateLimitServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

    @override_settings(ESTUDY_RATE_LIMIT_ENABLED=False)
    def test_rate_limit_disabled(self):
        request = self.factory.get(DEFAULT_PATH)
        result = check_rate_limit(request)

        self.assertTrue(result.success)
        self.assertEqual(result.data["allowed"], ALLOWED_TRUE)
        self.assertEqual(result.data["limit"], DEFAULT_LIMIT)
        self.assertEqual(result.data["remaining"], DEFAULT_REMAINING)
        self.assertEqual(result.data["reset_seconds"], DEFAULT_RESET_SECONDS)

    @override_settings(
        ESTUDY_RATE_LIMIT_ENABLED=True,
        ESTUDY_RATE_LIMIT_RATES={"anon": LIMIT_ONE, "user": LIMIT_ONE},
        ESTUDY_RATE_LIMIT_WINDOW_SECONDS=60,
    )
    def test_anon_rate_limit_blocks_after_limit(self):
        request = self.factory.get(DEFAULT_PATH)

        first = check_rate_limit(request)
        second = check_rate_limit(request)

        self.assertEqual(first.data["allowed"], ALLOWED_TRUE)
        self.assertEqual(second.data["allowed"], ALLOWED_FALSE)

    @override_settings(
        ESTUDY_RATE_LIMIT_ENABLED=True,
        ESTUDY_RATE_LIMIT_RATES={"anon": LIMIT_ONE, "user": LIMIT_ONE},
        ESTUDY_RATE_LIMIT_WINDOW_SECONDS=60,
    )
    def test_user_rate_limit_blocks_after_limit(self):
        user = User.objects.create_user(username="rl-user", password="pass1234")
        request = self.factory.get(DEFAULT_PATH)
        request.user = user

        first = check_rate_limit(request)
        second = check_rate_limit(request)

        self.assertEqual(first.data["allowed"], ALLOWED_TRUE)
        self.assertEqual(second.data["allowed"], ALLOWED_FALSE)

    @override_settings(
        ESTUDY_RATE_LIMIT_ENABLED=True,
        ESTUDY_RATE_LIMIT_RATES={"anon": LIMIT_ONE, "user": LIMIT_ONE},
        ESTUDY_RATE_LIMIT_WINDOW_SECONDS=60,
    )
    def test_middleware_sets_headers(self):
        def view(_request):
            return HttpResponse("ok")

        middleware = RequestRateLimitMiddleware(view)
        request = self.factory.get(DEFAULT_PATH)
        response = middleware(request)

        self.assertIn(HEADER_RATE_LIMIT_LIMIT, response)
        self.assertIn(HEADER_RATE_LIMIT_REMAINING, response)
        self.assertIn(HEADER_RATE_LIMIT_RESET, response)

    @override_settings(
        ESTUDY_RATE_LIMIT_ENABLED=True,
        ESTUDY_RATE_LIMIT_RATES={"anon": LIMIT_ONE, "user": LIMIT_ONE},
        ESTUDY_RATE_LIMIT_WINDOW_SECONDS=60,
    )
    def test_middleware_blocks_when_limited(self):
        def view(_request):
            return HttpResponse("ok")

        middleware = RequestRateLimitMiddleware(view)
        request = self.factory.get(DEFAULT_PATH)

        first = middleware(request)
        second = middleware(request)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, EXPECTED_STATUS_TOO_MANY)
