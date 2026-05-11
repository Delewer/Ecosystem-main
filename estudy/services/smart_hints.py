"""
Smart hints and contextual help system.
"""

from typing import Optional

from ..models import Lesson, LessonHint


class SmartHintSystem:
    """System for providing contextual hints and help."""

    @staticmethod
    def get_contextual_hint(
        user, lesson: Lesson, current_section: str, time_spent: int = 0
    ) -> Optional[str]:
        """Get contextual hint based on user progress and time spent."""
        try:
            personalization = lesson.personalizations.get(user=user)
            if not personalization.show_hints:
                return None
        except Exception:
            pass

        hints = LessonHint.objects.filter(
            lesson=lesson, section=current_section
        ).order_by("hint_level")

        if not hints.exists():
            return None

        for hint in hints:
            if time_spent >= hint.trigger_after_seconds:
                return hint.hint_text

        return None

    @staticmethod
    def get_ai_hint(code: str, error: str, exercise) -> str:
        """Generate a rule-based hint from the submitted code and error."""
        error_lower = error.lower()
        if "syntaxerror" in error_lower:
            return "Verifica sintaxa: toate parantezele sunt inchise si indentarea este corecta?"
        if "nameerror" in error_lower:
            return "Este posibil sa folosesti o variabila care nu este definita. Verifica numele variabilelor."
        if "indentationerror" in error_lower:
            return "Problema de indentare: in Python spatiile de la inceputul liniei conteaza."
        if "typeerror" in error_lower:
            return "Tipurile de date nu se potrivesc. Verifica ce valori trimiti functiei sau operatiei."
        if "indexerror" in error_lower:
            return (
                "Incerci sa accesezi un element din lista cu un index care nu exista."
            )
        if "keyerror" in error_lower:
            return "Cheia nu a fost gasita in dictionar. Verifica scrierea cheii."
        return "Foloseste un indiciu sau revizuieste exemplul din lectie. Continua pas cu pas."

    @staticmethod
    def suggest_related_lessons(
        current_lesson: Lesson, user=None, limit: int = 3
    ) -> list[Lesson]:
        """Suggest related lessons based on subject and difficulty."""
        related = Lesson.objects.filter(subject=current_lesson.subject).exclude(
            id=current_lesson.id
        )

        if user:
            completed_ids = Lesson.objects.filter(
                progress_records__user=user, progress_records__completed=True
            ).values_list("id", flat=True)
            related = related.exclude(id__in=completed_ids)

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
        """Determine if a hint should be shown."""
        try:
            personalization = lesson.personalizations.get(user=user)
            if not personalization.show_hints:
                return False
        except Exception:
            pass

        hints = LessonHint.objects.filter(lesson=lesson, section=section)

        for hint in hints:
            if attempts >= hint.show_after_attempts:
                return True

        return False

    @staticmethod
    def track_hint_usage(user, lesson: Lesson, section: str, hint_text: str) -> None:
        """Track hint usage for analytics."""
        pass
