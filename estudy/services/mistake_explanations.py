from __future__ import annotations

from ..models import Lesson, Test
from .code_runner import CodeRunResult
from .service_result import BaseServiceResult

MAX_CONTEXT_LENGTH = 240
MAX_CODE_SNIPPET = 160
MIN_CODE_SNIPPET = 0

DEFAULT_TEST_EXPLANATION = "Review the lesson concept and try again."
DEFAULT_CODE_EXPLANATION = "Compare expected output with your output and adjust."
DEFAULT_RUNTIME_EXPLANATION = "A runtime error occurred. Check the traceback."

NO_MISTAKE_WARNING = "no_mistake"
NO_CONTEXT_WARNING = "no_context"

ERROR_HINTS = [
    ("syntaxerror", "Syntax issue: check brackets, colons, and quotes."),
    ("nameerror", "Undefined name: make sure variables are defined."),
    ("typeerror", "Type mismatch: check the types used in operations."),
    ("indentationerror", "Indentation issue: align blocks consistently."),
    ("indexerror", "Index out of range: verify list or string indices."),
    ("keyerror", "Missing key: confirm the dictionary key exists."),
    ("valueerror", "Invalid value: check conversions and input format."),
    ("timeout", "Code took too long: check loops and recursion."),
]


def _trim(text: str, limit: int) -> str:
    if limit <= MIN_CODE_SNIPPET:
        return ""
    return (text or "")[:limit].strip()


def _first_nonempty(values: list[str]) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def _lesson_context(test: Test) -> str:
    lesson = getattr(test, "lesson", None)
    if lesson is None:
        return ""
    candidates = [
        getattr(test, "theory_summary", "") or "",
        getattr(test, "practice_prompt", "") or "",
        getattr(lesson, "theory_intro", "") or "",
        getattr(lesson, "excerpt", "") or "",
    ]
    return _trim(_first_nonempty(candidates), MAX_CONTEXT_LENGTH)


def build_test_mistake_explanation(
    test: Test, *, selected_answer: str | None = None
) -> BaseServiceResult:
    if test is None:
        return BaseServiceResult.fail("Test is required")

    if test.explanation:
        explanation = test.explanation
        source = "test_explanation"
    else:
        context = _lesson_context(test)
        if context:
            explanation = f"{context} Correct answer: {test.correct_answer}."
            source = "lesson_context"
        else:
            explanation = DEFAULT_TEST_EXPLANATION
            source = "default"

    if selected_answer:
        explanation = f"{explanation} Your answer: {selected_answer}."

    warnings = []
    if source == "default":
        warnings.append(NO_CONTEXT_WARNING)

    return BaseServiceResult.ok(
        data={"explanation": explanation, "source": source},
        warnings=warnings,
    )


def _match_error_hint(error_text: str) -> str | None:
    if not error_text:
        return None
    lowered = error_text.lower()
    for token, hint in ERROR_HINTS:
        if token in lowered:
            return hint
    return None


def build_code_mistake_explanation(
    result: CodeRunResult, *, lesson: Lesson | None = None
) -> BaseServiceResult:
    if result is None:
        return BaseServiceResult.fail("Code run result is required")

    if result.is_correct:
        return BaseServiceResult.ok(
            data={"explanation": None, "source": "none"},
            warnings=[NO_MISTAKE_WARNING],
        )

    if result.error:
        hint = _match_error_hint(result.error)
        explanation = hint or DEFAULT_RUNTIME_EXPLANATION
        if hint is None:
            explanation = (
                f"{explanation} Error: {_trim(result.error, MAX_CODE_SNIPPET)}."
            )
        return BaseServiceResult.ok(
            data={"explanation": explanation, "source": "runtime_error"}
        )

    failed_test = next(
        (test for test in result.test_results if not test.get("passed")),
        None,
    )
    if failed_test:
        expected = _trim(str(failed_test.get("expected", "")), MAX_CODE_SNIPPET)
        actual = _trim(str(failed_test.get("actual", "")), MAX_CODE_SNIPPET)
        stderr = _trim(str(failed_test.get("stderr", "")), MAX_CODE_SNIPPET)

        if stderr:
            hint = _match_error_hint(stderr)
            explanation = hint or DEFAULT_RUNTIME_EXPLANATION
            if hint is None:
                explanation = f"{explanation} Error: {stderr}."
            return BaseServiceResult.ok(
                data={"explanation": explanation, "source": "stderr"}
            )

        explanation = f"Expected output '{expected}', but got '{actual}'. {DEFAULT_CODE_EXPLANATION}"
        return BaseServiceResult.ok(
            data={"explanation": explanation, "source": "test_failure"}
        )

    fallback = DEFAULT_CODE_EXPLANATION
    if lesson is not None:
        fallback = f"{DEFAULT_CODE_EXPLANATION} Review '{lesson.title}'."

    return BaseServiceResult.ok(data={"explanation": fallback, "source": "fallback"})
