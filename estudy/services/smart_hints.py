"""
Smart hints and contextual help system
"""

from typing import Optional

from ..models import Lesson, LessonHint


class SmartHintSystem:
    """System for providing contextual hints and help"""

    @staticmethod
    def get_contextual_hint(
        user, lesson: Lesson, current_section: str, time_spent: int = 0
    ) -> Optional[str]:
        """Get contextual hint based on user progress and time spent"""
        # Check if user needs hints
        try:
            personalization = lesson.personalizations.get(user=user)
            if not personalization.show_hints:
                return None
        except Exception:
            pass  # Default to showing hints

        # Get hints for this section
        hints = LessonHint.objects.filter(
            lesson=lesson, section=current_section
        ).order_by("hint_level")

        if not hints.exists():
            return None

        # Determine which hint to show based on time spent
        for hint in hints:
            if time_spent >= hint.trigger_after_seconds:
                return hint.hint_text

        return None

    @staticmethod
    def get_ai_hint(code: str, error: str, exercise) -> str:
        """Generate AI-powered hint based on code and error"""
        # Simple rule-based hint system (can be enhanced with actual AI)
        if "SyntaxError" in error.lower():
            return "Проверьте синтаксис: все скобки закрыты? Правильные отступы?"
        elif "NameError" in error.lower():
            return "Возможно, вы используете переменную, которая не определена. Проверьте названия переменных."
        elif "IndentationError" in error.lower():
            return "Проблема с отступами - в Python это важно! Убедитесь, что отступы consistent."
        elif "TypeError" in error.lower():
            return (
                "Типы данных не совпадают. Проверьте, что вы передаете правильные типы."
            )
        elif "IndexError" in error.lower():
            return (
                "Вы пытаетесь обратиться к элементу списка по несуществующему индексу."
            )
        elif "KeyError" in error.lower():
            return "Ключ не найден в словаре. Проверьте правильность написания ключей."
        else:
            return "Попробуйте использовать подсказку или посмотрите пример решения. Не сдавайтесь!"

    @staticmethod
    def suggest_related_lessons(
        current_lesson: Lesson, user=None, limit: int = 3
    ) -> list[Lesson]:
        """Suggest related lessons based on subject and difficulty"""
        related = Lesson.objects.filter(subject=current_lesson.subject).exclude(
            id=current_lesson.id
        )

        # If user provided, consider their progress
        if user:
            completed_ids = Lesson.objects.filter(
                progress_records__user=user, progress_records__completed=True
            ).values_list("id", flat=True)
            related = related.exclude(id__in=completed_ids)

        # Prefer same or slightly higher difficulty
        difficulty_order = {"beginner": 1, "intermediate": 2, "advanced": 3}
        current_level = difficulty_order.get(current_lesson.difficulty, 2)

        related = related.filter(
            difficulty__in=[
                diff
                for diff, level in difficulty_order.items()
                if abs(level - current_level) <= 1
            ]
        )

        return list(related[:limit])

    @staticmethod
    def should_show_hint(user, lesson: Lesson, section: str, attempts: int = 0) -> bool:
        """Determine if a hint should be shown"""
        # Check personalization
        try:
            personalization = lesson.personalizations.get(user=user)
            if not personalization.show_hints:
                return False
        except Exception:
            pass

        # Check hint triggers
        hints = LessonHint.objects.filter(lesson=lesson, section=section)

        for hint in hints:
            if attempts >= hint.show_after_attempts:
                return True

        return False

    @staticmethod
    def track_hint_usage(user, lesson: Lesson, section: str, hint_text: str) -> None:
        """Track hint usage for analytics (placeholder for future implementation)"""
        # Could be used to improve hint system based on usage patterns
        pass
