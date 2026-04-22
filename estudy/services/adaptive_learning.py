"""
Adaptive learning engine for personalized lesson recommendations
"""

from typing import Dict, List, Optional

from django.db.models import Q

from ..models import Lesson, LessonPersonalization, LessonProgress, TestAttempt


class AdaptiveLearningEngine:
    """Engine for adaptive learning and personalization"""

    @staticmethod
    def get_next_lesson_recommendation(user) -> Optional[Lesson]:
        """Recommend next lesson based on user's performance"""
        analytics = AdaptiveLearningEngine.get_student_performance_analytics(user)

        # Determine preferred difficulty
        if analytics["success_rate"] >= 85:
            preferred_difficulty = "advanced"
        elif analytics["success_rate"] >= 65:
            preferred_difficulty = "intermediate"
        else:
            preferred_difficulty = "beginner"

        # Find uncompleted lessons of preferred difficulty
        completed_lesson_ids = LessonProgress.objects.filter(
            user=user, completed=True
        ).values_list("lesson_id", flat=True)

        lesson = (
            Lesson.objects.exclude(id__in=completed_lesson_ids)
            .filter(difficulty=preferred_difficulty)
            .first()
        )

        return lesson

    @staticmethod
    def should_skip_basics(user) -> bool:
        """Determine if user should skip basic lessons"""
        # Check performance on basic lessons
        basic_lessons = Lesson.objects.filter(difficulty="beginner")[:3]

        if not basic_lessons:
            return False

        correct_answers = 0
        total_questions = 0

        for lesson in basic_lessons:
            # Check test attempts for this lesson
            tests = lesson.tests.all()[:2]  # First 2 tests per lesson
            for test in tests:
                attempts = TestAttempt.objects.filter(
                    user=user, test=test, is_correct=True
                )
                if attempts.exists():
                    correct_answers += 1
                total_questions += 1

        # Skip if >80% correct
        return (
            (correct_answers / total_questions) >= 0.8 if total_questions > 0 else False
        )

    @staticmethod
    def get_student_performance_analytics(user) -> Dict:
        """Get comprehensive performance analytics for a student"""
        # Get all test attempts
        attempts = TestAttempt.objects.filter(user=user)
        total_attempts = attempts.count()
        correct_attempts = attempts.filter(is_correct=True).count()

        success_rate = (
            (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        )

        # Get lesson completion stats
        completed_lessons = LessonProgress.objects.filter(
            user=user, completed=True
        ).count()
        total_lessons = Lesson.objects.count()

        # Find weak topics (lessons with low success rates)
        weak_topics = []
        lessons = Lesson.objects.all()
        for lesson in lessons:
            lesson_attempts = TestAttempt.objects.filter(user=user, test__lesson=lesson)
            if lesson_attempts.exists():
                lesson_correct = lesson_attempts.filter(is_correct=True).count()
                lesson_total = lesson_attempts.count()
                lesson_rate = (
                    (lesson_correct / lesson_total * 100) if lesson_total > 0 else 0
                )

                if lesson_rate < 70:  # Consider <70% as weak
                    weak_topics.append(
                        {
                            "lesson": lesson,
                            "success_rate": lesson_rate,
                            "attempts": lesson_total,
                        }
                    )

        # Sort by success rate (worst first)
        weak_topics.sort(key=lambda x: x["success_rate"])

        return {
            "success_rate": success_rate,
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "completed_lessons": completed_lessons,
            "total_lessons": total_lessons,
            "completion_rate": (completed_lessons / total_lessons * 100)
            if total_lessons > 0
            else 0,
            "weak_topics": weak_topics[:5],  # Top 5 weak topics
        }

    @staticmethod
    def generate_personalized_content(user, lesson: Lesson) -> Dict:
        """Generate personalized content for a lesson"""
        analytics = AdaptiveLearningEngine.get_student_performance_analytics(user)

        # Get or create personalization
        personalization, created = LessonPersonalization.objects.get_or_create(
            user=user,
            lesson=lesson,
            defaults={
                "content_difficulty": lesson.difficulty,
                "preferred_media": "mixed",
            },
        )

        content = {
            "lesson": lesson,
            "personalization": personalization,
            "show_extra_examples": analytics["success_rate"] < 70,
            "show_advanced_topics": analytics["success_rate"] > 85,
            "recommended_pace": "slow" if analytics["success_rate"] < 60 else "normal",
            "extra_practice": [],
        }

        # Add extra practice for weak topics
        for topic in analytics["weak_topics"][:3]:
            if topic["lesson"] != lesson:  # Don't recommend the same lesson
                content["extra_practice"].append(topic["lesson"])

        return content

    @staticmethod
    def update_personalization(user, lesson: Lesson, **updates) -> None:
        """Update personalization settings for a user-lesson pair"""
        personalization, created = LessonPersonalization.objects.get_or_create(
            user=user, lesson=lesson
        )

        for key, value in updates.items():
            if hasattr(personalization, key):
                setattr(personalization, key, value)

        personalization.save()

    @staticmethod
    def get_learning_path_recommendation(user, subject=None) -> List[Lesson]:
        """Generate a personalized learning path"""
        # Base query
        query = Q()
        if subject:
            query &= Q(subject=subject)

        # Determine starting difficulty
        if AdaptiveLearningEngine.should_skip_basics(user):
            difficulties = ["intermediate", "advanced", "beginner"]
        else:
            difficulties = ["beginner", "intermediate", "advanced"]

        # Get uncompleted lessons
        completed_ids = LessonProgress.objects.filter(
            user=user, completed=True
        ).values_list("lesson_id", flat=True)

        recommended_lessons = []
        for difficulty in difficulties:
            lessons = Lesson.objects.filter(query & Q(difficulty=difficulty)).exclude(
                id__in=completed_ids
            )[
                :5
            ]  # Max 5 per difficulty

            recommended_lessons.extend(lessons)

        return recommended_lessons[:10]  # Return top 10
