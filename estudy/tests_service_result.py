from django.test import TestCase

from .services.service_result import BaseServiceResult

DEFAULT_KEY = "value"
DEFAULT_VALUE = "ok"
DEFAULT_ERROR = "boom"
WARNING_ONE = "warn-one"
WARNING_TWO = "warn-two"
EXPECTED_WARNING_COUNT = 2


class BaseServiceResultTests(TestCase):
    def test_ok_result(self):
        result = BaseServiceResult.ok(data={DEFAULT_KEY: DEFAULT_VALUE})

        self.assertTrue(result.success)
        self.assertEqual(result.data[DEFAULT_KEY], DEFAULT_VALUE)

    def test_fail_result(self):
        result = BaseServiceResult.fail(DEFAULT_ERROR)

        self.assertFalse(result.success)
        self.assertEqual(result.error, DEFAULT_ERROR)

    def test_require_success_raises(self):
        result = BaseServiceResult.fail(DEFAULT_ERROR)

        with self.assertRaises(ValueError):
            result.require_success()

    def test_warning_normalization(self):
        result = BaseServiceResult.ok(warnings=[WARNING_ONE, WARNING_TWO])

        self.assertEqual(len(result.warnings), EXPECTED_WARNING_COUNT)
