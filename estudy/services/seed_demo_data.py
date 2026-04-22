from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from ..models import (
    CodeExercise,
    Course,
    CourseGoal,
    LearningPath,
    LearningPathLesson,
    Lesson,
    Module,
    Subject,
    Test,
    TopicTag,
)

ORDER_START = 1
DAY_INCREMENT = 1
DEFAULT_MODULE_ORDER = 1


@dataclass(frozen=True)
class SeedSummary:
    created: dict[str, int]
    totals: dict[str, int]


def _empty_counts(keys: Iterable[str]) -> dict[str, int]:
    return {key: 0 for key in keys}


def _get_or_create_first(model, lookup: dict, defaults: dict):
    instance = model.objects.filter(**lookup).first()
    if instance:
        return instance, False
    return model.objects.create(**lookup, **defaults), True


def _increment(counts: dict[str, int], key: str, created: bool) -> None:
    if created:
        counts[key] += 1


def _build_counts() -> dict[str, int]:
    return _empty_counts(
        (
            "subjects",
            "courses",
            "course_goals",
            "modules",
            "lessons",
            "topic_tags",
            "tests",
            "code_exercises",
            "learning_paths",
            "learning_path_lessons",
        )
    )


def _seed_subject(subject_data: dict, created: dict[str, int]) -> dict:
    subject, subject_created = _get_or_create_first(
        Subject,
        {"name": subject_data["name"]},
        {"description": subject_data.get("description", "")},
    )
    _increment(created, "subjects", subject_created)
    subject_data["instance"] = subject
    return subject_data


def _seed_course(
    subject: Subject, course_data: dict, created: dict[str, int]
) -> Course:
    course, course_created = Course.objects.get_or_create(
        slug=course_data["slug"],
        defaults={
            "title": course_data["title"],
            "description": course_data.get("description", ""),
            "subject": subject,
            "level": course_data.get("level", Course.LEVEL_BEGINNER),
        },
    )
    _increment(created, "courses", course_created)

    for goal in course_data.get("goals", []):
        _, goal_created = _get_or_create_first(
            CourseGoal,
            {"course": course, "description": goal},
            {},
        )
        _increment(created, "course_goals", goal_created)

    return course


def _seed_module(course: Course, module_data: dict, created: dict[str, int]) -> Module:
    module, module_created = Module.objects.get_or_create(
        slug=module_data["slug"],
        defaults={
            "title": module_data["title"],
            "description": module_data.get("description", ""),
            "course": course,
            "order": module_data.get("order", DEFAULT_MODULE_ORDER),
        },
    )
    _increment(created, "modules", module_created)
    return module


def _seed_topics(topic_data: Iterable[dict], created: dict[str, int]) -> list[TopicTag]:
    topic_objs: list[TopicTag] = []
    for entry in topic_data:
        topic, topic_created = TopicTag.objects.get_or_create(
            slug=entry["slug"],
            defaults={"name": entry["name"]},
        )
        _increment(created, "topic_tags", topic_created)
        topic_objs.append(topic)
    return topic_objs


def _seed_tests(
    lesson: Lesson, test_data: Iterable[dict], created: dict[str, int]
) -> None:
    for entry in test_data:
        _, test_created = _get_or_create_first(
            Test,
            {"lesson": lesson, "question": entry["question"]},
            {
                "correct_answer": entry["correct_answer"],
                "wrong_answers": entry["wrong_answers"],
                "explanation": entry.get("explanation", ""),
            },
        )
        _increment(created, "tests", test_created)


def _seed_code_exercise(
    lesson: Lesson, exercise_data: dict | None, created: dict[str, int]
) -> None:
    if not exercise_data:
        return
    _, exercise_created = _get_or_create_first(
        CodeExercise,
        {"lesson": lesson, "title": exercise_data["title"]},
        {
            "description": exercise_data["description"],
            "language": exercise_data.get("language", CodeExercise.LANG_PYTHON),
            "starter_code": exercise_data.get("starter_code", ""),
            "solution": exercise_data.get("solution", ""),
            "test_cases": exercise_data.get("test_cases", []),
        },
    )
    _increment(created, "code_exercises", exercise_created)


def _seed_lessons(
    module: Module,
    lesson_data: Iterable[dict],
    created: dict[str, int],
    base_date,
) -> list[Lesson]:
    lessons: list[Lesson] = []
    for index, entry in enumerate(lesson_data, start=ORDER_START):
        lesson_date = base_date + timedelta(days=(index - ORDER_START) * DAY_INCREMENT)
        lesson, lesson_created = Lesson.objects.get_or_create(
            slug=entry["slug"],
            defaults={
                "subject": module.course.subject,
                "module": module,
                "title": entry["title"],
                "excerpt": entry.get("excerpt", ""),
                "content": entry["content"],
                "date": lesson_date,
                "difficulty": entry.get("difficulty", Lesson.DIFFICULTY_BEGINNER),
                "lesson_type": entry.get("lesson_type", Lesson.LESSON_TYPE_STANDARD),
                "age_bracket": entry.get("age_bracket", Lesson.AGE_11_13),
            },
        )
        _increment(created, "lessons", lesson_created)
        topics = _seed_topics(entry.get("topics", []), created)
        if topics:
            lesson.topics.add(*topics)
        _seed_tests(lesson, entry.get("tests", []), created)
        _seed_code_exercise(lesson, entry.get("code_exercise"), created)
        lessons.append(lesson)
    return lessons


def _seed_learning_path(path_data: dict, created: dict[str, int]) -> None:
    path, path_created = LearningPath.objects.get_or_create(
        slug=path_data["slug"],
        defaults={
            "title": path_data["title"],
            "description": path_data["description"],
            "theme": path_data.get("theme", "rainbow"),
            "difficulty": path_data.get("difficulty", Lesson.DIFFICULTY_BEGINNER),
            "audience": path_data.get("audience", "general"),
            "is_featured": path_data.get("is_featured", False),
        },
    )
    _increment(created, "learning_paths", path_created)
    for index, lesson_slug in enumerate(
        path_data.get("lesson_slugs", []), start=ORDER_START
    ):
        lesson = Lesson.objects.filter(slug=lesson_slug).first()
        if not lesson:
            continue
        _, link_created = LearningPathLesson.objects.get_or_create(
            path=path,
            lesson=lesson,
            defaults={"order": index},
        )
        _increment(created, "learning_path_lessons", link_created)


def seed_demo_data() -> SeedSummary:
    created = _build_counts()

    subject_data = [
        {
            "name": "Python Fundamentals",
            "description": "Core Python concepts through short, focused lessons.",
            "courses": [
                {
                    "title": "Python Starter",
                    "slug": "python-starter",
                    "description": "Learn the foundations of Python programming.",
                    "level": Course.LEVEL_BEGINNER,
                    "goals": [
                        "Understand variables and data types",
                        "Write loops with confidence",
                    ],
                    "modules": [
                        {
                            "title": "Python Basics",
                            "slug": "python-basics",
                            "order": DEFAULT_MODULE_ORDER,
                            "lessons": [
                                {
                                    "title": "Variables and Types",
                                    "slug": "python-variables-types",
                                    "excerpt": "Learn how Python stores values.",
                                    "content": "We explore variables, types, and naming rules.",
                                    "difficulty": Lesson.DIFFICULTY_BEGINNER,
                                    "lesson_type": Lesson.LESSON_TYPE_STANDARD,
                                    "topics": [
                                        {"name": "Variables", "slug": "variables"},
                                        {"name": "Data Types", "slug": "data-types"},
                                    ],
                                    "tests": [
                                        {
                                            "question": "Which keyword creates a variable in Python?",
                                            "correct_answer": "Python assigns on first use",
                                            "wrong_answers": [
                                                "var",
                                                "let",
                                                "define",
                                            ],
                                            "explanation": "Python does not require a keyword; assignment creates it.",
                                        },
                                        {
                                            "question": "What type is the value 3.14?",
                                            "correct_answer": "float",
                                            "wrong_answers": [
                                                "int",
                                                "str",
                                                "bool",
                                            ],
                                            "explanation": "Decimals in Python are floats.",
                                        },
                                    ],
                                    "code_exercise": {
                                        "title": "Store a Greeting",
                                        "description": "Create a variable called greeting and print it.",
                                        "language": CodeExercise.LANG_PYTHON,
                                        "starter_code": 'greeting = "Hello"\nprint(greeting)\n',
                                        "solution": 'greeting = "Hello"\nprint(greeting)\n',
                                        "test_cases": [
                                            {
                                                "input": "",
                                                "expected_output": "Hello",
                                                "description": "Prints the greeting.",
                                            }
                                        ],
                                    },
                                },
                                {
                                    "title": "Loops and Iteration",
                                    "slug": "python-loops",
                                    "excerpt": "Repeat tasks with for/while.",
                                    "content": "We practice looping over ranges and lists.",
                                    "difficulty": Lesson.DIFFICULTY_BEGINNER,
                                    "lesson_type": Lesson.LESSON_TYPE_STANDARD,
                                    "topics": [
                                        {"name": "Loops", "slug": "loops"},
                                        {
                                            "name": "Control Flow",
                                            "slug": "control-flow",
                                        },
                                    ],
                                    "tests": [
                                        {
                                            "question": "Which loop is ideal for a known count?",
                                            "correct_answer": "for",
                                            "wrong_answers": [
                                                "while",
                                                "repeat",
                                                "loop",
                                            ],
                                            "explanation": "For loops are commonly used with ranges.",
                                        },
                                        {
                                            "question": "What stops a while loop?",
                                            "correct_answer": "A false condition",
                                            "wrong_answers": [
                                                "A variable name",
                                                "A print statement",
                                                "A comment",
                                            ],
                                            "explanation": "While loops stop when the condition becomes false.",
                                        },
                                    ],
                                    "code_exercise": {
                                        "title": "Count to Three",
                                        "description": "Print the numbers 1 to 3 using a loop.",
                                        "language": CodeExercise.LANG_PYTHON,
                                        "starter_code": "for number in range(1, 4):\n    print(number)\n",
                                        "solution": "for number in range(1, 4):\n    print(number)\n",
                                        "test_cases": [
                                            {
                                                "input": "",
                                                "expected_output": "1\n2\n3",
                                                "description": "Outputs three lines.",
                                            }
                                        ],
                                    },
                                },
                            ],
                        }
                    ],
                }
            ],
        },
        {
            "name": "Web Foundations",
            "description": "Learn how to build and style web pages.",
            "courses": [
                {
                    "title": "Web Starter",
                    "slug": "web-starter",
                    "description": "HTML and CSS essentials for beginners.",
                    "level": Course.LEVEL_BEGINNER,
                    "goals": [
                        "Structure a basic HTML document",
                        "Style layouts with CSS",
                    ],
                    "modules": [
                        {
                            "title": "HTML & CSS",
                            "slug": "web-html-css",
                            "order": DEFAULT_MODULE_ORDER,
                            "lessons": [
                                {
                                    "title": "HTML Structure",
                                    "slug": "html-structure",
                                    "excerpt": "Build the skeleton of a page.",
                                    "content": "Learn the core tags that shape an HTML page.",
                                    "difficulty": Lesson.DIFFICULTY_BEGINNER,
                                    "lesson_type": Lesson.LESSON_TYPE_STANDARD,
                                    "topics": [
                                        {"name": "HTML", "slug": "html"},
                                        {"name": "Semantics", "slug": "semantics"},
                                    ],
                                    "tests": [
                                        {
                                            "question": "Which tag wraps the main page content?",
                                            "correct_answer": "<main>",
                                            "wrong_answers": [
                                                "<header>",
                                                "<footer>",
                                                "<section>",
                                            ],
                                            "explanation": "<main> is used for primary content.",
                                        },
                                        {
                                            "question": "Which tag defines a hyperlink?",
                                            "correct_answer": "<a>",
                                            "wrong_answers": [
                                                "<link>",
                                                "<nav>",
                                                "<href>",
                                            ],
                                            "explanation": "Links are created with the <a> tag.",
                                        },
                                    ],
                                },
                                {
                                    "title": "CSS Basics",
                                    "slug": "css-basics",
                                    "excerpt": "Style text, color, and layout.",
                                    "content": "Learn selectors, properties, and the box model.",
                                    "difficulty": Lesson.DIFFICULTY_BEGINNER,
                                    "lesson_type": Lesson.LESSON_TYPE_STANDARD,
                                    "topics": [
                                        {"name": "CSS", "slug": "css"},
                                        {"name": "Layout", "slug": "layout"},
                                    ],
                                    "tests": [
                                        {
                                            "question": "Which property changes text color?",
                                            "correct_answer": "color",
                                            "wrong_answers": [
                                                "font-size",
                                                "background",
                                                "align",
                                            ],
                                            "explanation": "The color property sets text color.",
                                        },
                                        {
                                            "question": "What does margin control?",
                                            "correct_answer": "Space outside the element",
                                            "wrong_answers": [
                                                "Space inside the element",
                                                "Text alignment",
                                                "Border thickness",
                                            ],
                                            "explanation": "Margins add space around an element.",
                                        },
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ],
        },
    ]

    learning_paths = [
        {
            "title": "Python Beginner Path",
            "slug": "path-python-beginner",
            "description": "A quick start path for Python newcomers.",
            "theme": "sky",
            "difficulty": Lesson.DIFFICULTY_BEGINNER,
            "audience": "students",
            "lesson_slugs": [
                "python-variables-types",
                "python-loops",
            ],
        },
        {
            "title": "Web Beginner Path",
            "slug": "path-web-beginner",
            "description": "Start building web pages with HTML and CSS.",
            "theme": "sunset",
            "difficulty": Lesson.DIFFICULTY_BEGINNER,
            "audience": "students",
            "lesson_slugs": [
                "html-structure",
                "css-basics",
            ],
        },
    ]

    with transaction.atomic():
        base_date = timezone.localdate()
        for subject in subject_data:
            subject = _seed_subject(subject, created)
            subject_instance = subject["instance"]
            for course_data in subject.get("courses", []):
                course = _seed_course(subject_instance, course_data, created)
                for module_data in course_data.get("modules", []):
                    module = _seed_module(course, module_data, created)
                    _seed_lessons(
                        module,
                        module_data.get("lessons", []),
                        created,
                        base_date,
                    )

        for path_data in learning_paths:
            _seed_learning_path(path_data, created)

    totals = {
        "subjects": Subject.objects.count(),
        "courses": Course.objects.count(),
        "course_goals": CourseGoal.objects.count(),
        "modules": Module.objects.count(),
        "lessons": Lesson.objects.count(),
        "topic_tags": TopicTag.objects.count(),
        "tests": Test.objects.count(),
        "code_exercises": CodeExercise.objects.count(),
        "learning_paths": LearningPath.objects.count(),
        "learning_path_lessons": LearningPathLesson.objects.count(),
    }

    return SeedSummary(created=created, totals=totals)
