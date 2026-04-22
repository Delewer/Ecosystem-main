from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from .services.profiling import (
    HEADER_DURATION,
    HEADER_QUERY_COUNT,
    HEADER_QUERY_TIME,
    PROFILE_ENABLE_VALUE,
    PROFILE_HEADER,
    PROFILE_QUERY_PARAM,
    apply_profile_headers,
    finish_profile,
    start_profile,
)

DEFAULT_PATH = "/estudy/overview/"
DEFAULT_METHOD = "GET"


class ProfilingServiceTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(DEBUG=False)
    def test_start_profile_disabled_when_not_debug(self):
        request = self.factory.get(DEFAULT_PATH)
        self.assertIsNone(start_profile(request))

    @override_settings(DEBUG=True)
    def test_start_profile_enabled_with_header(self):
        request = self.factory.get(
            DEFAULT_PATH,
            **{
                f"HTTP_{PROFILE_HEADER.upper().replace('-', '_')}": PROFILE_ENABLE_VALUE
            },
        )
        self.assertIsNotNone(start_profile(request))

    @override_settings(DEBUG=True)
    def test_start_profile_enabled_with_query_param(self):
        request = self.factory.get(
            DEFAULT_PATH, {PROFILE_QUERY_PARAM: PROFILE_ENABLE_VALUE}
        )
        self.assertIsNotNone(start_profile(request))

    @override_settings(DEBUG=True)
    def test_apply_profile_headers(self):
        request = self.factory.get(DEFAULT_PATH)
        context = start_profile(request)
        self.assertIsNotNone(context)
        response = HttpResponse()
        snapshot = finish_profile(context, response)
        apply_profile_headers(response, snapshot)

        self.assertIn(HEADER_DURATION, response)
        self.assertIn(HEADER_QUERY_COUNT, response)
        self.assertIn(HEADER_QUERY_TIME, response)
