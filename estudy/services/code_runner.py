from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.conf import settings

SAFE_TIMEOUT_SECONDS = 5
CODE_RUNNER_SETTING = "ESTUDY_CODE_RUNNER_ENABLED"
CODE_RUNNER_DISABLED_MESSAGE = "Code execution is disabled."
DEFAULT_EXECUTION_TIME_MS = 0


@dataclass
class CodeRunResult:
    passed: int
    total: int
    test_results: List[Dict[str, Any]]
    is_correct: bool
    error: Optional[str] = None
    execution_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "total": self.total,
            "test_results": self.test_results,
            "is_correct": self.is_correct,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }


class CodeRunner:
    """Very basic code runner intended for development/testing.

    WARNING: This implementation uses subprocess without sandboxing and should
    NOT be exposed in production as-is. For production, execute code inside a
    hardened container (e.g., Docker) with resource limits and no network.
    """

    @staticmethod
    def run_python_code(code: str, test_cases: List[Dict[str, Any]]) -> CodeRunResult:
        if not getattr(settings, CODE_RUNNER_SETTING, False):
            return CodeRunResult(
                passed=0,
                total=len(test_cases),
                test_results=[],
                is_correct=False,
                error=CODE_RUNNER_DISABLED_MESSAGE,
                execution_time_ms=DEFAULT_EXECUTION_TIME_MS,
            )
        start = time.perf_counter()
        results: List[Dict[str, Any]] = []
        passed = 0
        total = len(test_cases)
        error: Optional[str] = None

        # Ensure code prints result based on stdin; we can't enforce structure
        for test in test_cases:
            try:
                proc = subprocess.run(
                    [sys.executable, "-I", "-c", code],
                    input=str(test.get("input", "")),
                    capture_output=True,
                    text=True,
                    timeout=SAFE_TIMEOUT_SECONDS,
                )
                stdout = (proc.stdout or "").strip()
                expected = str(test.get("expected_output", "")).strip()
                ok = stdout == expected
                if ok:
                    passed += 1
                results.append(
                    {
                        "description": test.get("description") or "",
                        "input": test.get("input", ""),
                        "expected": expected,
                        "actual": stdout,
                        "passed": ok,
                        "returncode": proc.returncode,
                        "stderr": (proc.stderr or "").strip(),
                    }
                )
            except subprocess.TimeoutExpired:
                error = "Timeout: code took too long to run"
                break
            except Exception as exc:  # pragma: no cover
                error = f"Execution error: {exc}"
                break

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return CodeRunResult(
            passed=passed,
            total=total,
            test_results=results,
            is_correct=passed == total and total > 0,
            error=error,
            execution_time_ms=elapsed_ms,
        )

    @staticmethod
    def get_basic_hint(code: str, error: Optional[str]) -> str:
        if not error:
            return ""
        if "SyntaxError" in error:
            return "Проверьте синтаксис: скобки, кавычки и отступы."
        if "NameError" in error:
            return "Похоже, вы используете имя, которое не определено."
        if "IndentationError" in error:
            return "В Python важно соблюдать отступы."
        if "Timeout" in error:
            return "Ваш код работает слишком долго — проверьте циклы и условия."
        return "Попробуйте упростить решение и вывести только требуемый результат."
