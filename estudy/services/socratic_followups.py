from __future__ import annotations

from ..models import Lesson, Test
from .code_runner import CodeRunResult
from .service_result import BaseServiceResult

MAX_QUESTIONS = 3

MAX_SNIPPET_LENGTH = 120

NO_MISTAKE_WARNING = "no_mistake"

TEST_QUESTIONS = [
    "What concept from the lesson does this question test?",
    "What in the prompt led you to choose your answer?",
    "How would you justify the correct answer in one sentence?",
    "Can you restate the rule in your own words?",
    "What example would help you verify the rule?",
]

CODE_ERROR_QUESTIONS = [
    "Which line triggers the error message?",
    "What does the error say about the expected type or syntax?",
    "Which value should you inspect with a print statement?",
]

CODE_TEST_QUESTIONS = [
    "What do you expect the code to output for this input?",
    "Where does the actual output first diverge from the expected output?",
    "Which step in your logic might be missing or incorrect?",
]


def _trim(text: str | None, limit: int) -> str:
    if not text:
        return ""
    return text.strip()[:limit]


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _pick_questions(candidates: list[str]) -> list[str]:
    return candidates[:MAX_QUESTIONS]


def build_test_socratic_followups(
    test: Test,
    *,
    selected_answer: str | None = None,
) -> BaseServiceResult:
    if test is None:
        return BaseServiceResult.fail("Test is required")

    questions = list(TEST_QUESTIONS)
    if selected_answer:
        questions.insert(
            0,
            f"What made '{_trim(selected_answer, MAX_SNIPPET_LENGTH)}' feel correct?",
        )
    if test.explanation:
        questions.append("Which part of the explanation changes your thinking?")

    questions = _pick_questions(_dedupe(questions))
    return BaseServiceResult.ok(
        data={
            "questions": questions,
        }
    )


def build_code_socratic_followups(
    result: CodeRunResult,
    *,
    lesson: Lesson | None = None,
) -> BaseServiceResult:
    if result is None:
        return BaseServiceResult.fail("Code run result is required")

    if result.is_correct:
        return BaseServiceResult.ok(
            data={"questions": []},
            warnings=[NO_MISTAKE_WARNING],
        )

    if result.error:
        questions = _pick_questions(_dedupe(list(CODE_ERROR_QUESTIONS)))
        return BaseServiceResult.ok(data={"questions": questions})

    failed_test = next(
        (test for test in result.test_results if not test.get("passed")),
        None,
    )
    if failed_test:
        expected = _trim(str(failed_test.get("expected", "")), MAX_SNIPPET_LENGTH)
        actual = _trim(str(failed_test.get("actual", "")), MAX_SNIPPET_LENGTH)
        questions = list(CODE_TEST_QUESTIONS)
        if expected and actual:
            questions.insert(
                0,
                f"What should happen when output is '{expected}' instead of '{actual}'?",
            )
        questions = _pick_questions(_dedupe(questions))
        return BaseServiceResult.ok(data={"questions": questions})

    fallback = list(CODE_TEST_QUESTIONS)
    if lesson is not None:
        fallback.insert(
            0,
            f"Which concept from '{lesson.title}' would you revisit first?",
        )
    questions = _pick_questions(_dedupe(fallback))
    return BaseServiceResult.ok(data={"questions": questions})
