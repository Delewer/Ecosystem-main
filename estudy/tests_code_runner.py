from unittest.mock import patch

from django.test import TestCase, override_settings

from .services.code_runner import CODE_RUNNER_DISABLED_MESSAGE, CodeRunner

TEST_CASES = [
    {"input": "", "expected_output": "hi", "description": "simple output"},
]
EXPECTED_TOTAL = 1
EXPECTED_PASSED = 0


class CodeRunnerTests(TestCase):
    @override_settings(ESTUDY_CODE_RUNNER_ENABLED=False)
    def test_code_runner_disabled(self):
        with patch("estudy.services.code_runner.subprocess.run") as run_process:
            result = CodeRunner.run_python_code("print('hi')", TEST_CASES)

            self.assertEqual(result.error, CODE_RUNNER_DISABLED_MESSAGE)
            self.assertEqual(result.total, EXPECTED_TOTAL)
            self.assertEqual(result.passed, EXPECTED_PASSED)
            run_process.assert_not_called()
