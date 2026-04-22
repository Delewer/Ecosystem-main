"""
Lesson quality analysis and feedback processing
"""

from typing import Dict, Optional

from django.db.models import Avg

from ..models import Lesson, LessonFeedback


class LessonQualityAnalyzer:
    """Analyze lesson quality based on feedback and usage data"""

    @staticmethod
    def get_lesson_quality_score(lesson: Lesson) -> Dict:
        """Calculate comprehensive quality score for a lesson"""
        feedbacks = LessonFeedback.objects.filter(lesson=lesson)

        if not feedbacks.exists():
            return {"score": 0, "insufficient_data": True, "total_reviews": 0}

        # Calculate averages
        avg_content = (
            feedbacks.aggregate(Avg("content_quality"))["content_quality__avg"] or 0
        )
        avg_difficulty = (
            feedbacks.aggregate(Avg("difficulty_appropriate"))[
                "difficulty_appropriate__avg"
            ]
            or 0
        )
        avg_examples = (
            feedbacks.aggregate(Avg("examples_helpful"))["examples_helpful__avg"] or 0
        )
        avg_overall = (
            feedbacks.aggregate(Avg("overall_rating"))["overall_rating__avg"] or 0
        )

        # Overall quality score (weighted average)
        quality_score = (
            avg_content * 0.25
            + avg_difficulty * 0.25
            + avg_examples * 0.25
            + avg_overall * 0.25
        )

        # Recommendation rate
        recommend_count = feedbacks.filter(would_recommend=True).count()
        recommend_rate = (recommend_count / feedbacks.count()) * 100

        return {
            "score": round(quality_score, 2),
            "content_quality": round(avg_content, 2),
            "difficulty_appropriate": round(avg_difficulty, 2),
            "examples_helpful": round(avg_examples, 2),
            "overall_rating": round(avg_overall, 2),
            "recommendation_rate": round(recommend_rate, 1),
            "total_reviews": feedbacks.count(),
            "insufficient_data": False,
        }

    @staticmethod
    def get_average_completion_time(lesson: Lesson) -> Optional[float]:
        """Get average time to complete the lesson"""
        from ..models import LessonProgress

        completed_progress = LessonProgress.objects.filter(
            lesson=lesson, completed=True, fastest_completion_seconds__gt=0
        )

        if not completed_progress.exists():
            return None

        avg_time = completed_progress.aggregate(Avg("fastest_completion_seconds"))[
            "fastest_completion_seconds__avg"
        ]
        return avg_time / 60 if avg_time else None  # Convert to minutes

    @staticmethod
    def get_lesson_engagement_metrics(lesson: Lesson) -> Dict:
        """Get engagement metrics for a lesson"""
        from ..models import LessonProgress, VideoProgress

        total_views = LessonProgress.objects.filter(lesson=lesson).count()
        completions = LessonProgress.objects.filter(
            lesson=lesson, completed=True
        ).count()

        completion_rate = (completions / total_views * 100) if total_views > 0 else 0

        # Video engagement if applicable (legacy lesson.media or direct field fallback)
        video_completion_rate = 0
        video_url = getattr(lesson, "video_url", None)
        if not video_url:
            media = getattr(lesson, "media", None)
            video_url = getattr(media, "video_url", None) if media else None

        if video_url:
            video_progresses = VideoProgress.objects.filter(lesson=lesson)
            if video_progresses.exists():
                completed_videos = video_progresses.filter(
                    completion_percent__gte=80
                ).count()
                video_completion_rate = (
                    completed_videos / video_progresses.count() * 100
                )

        return {
            "total_views": total_views,
            "completions": completions,
            "completion_rate": round(completion_rate, 1),
            "video_completion_rate": round(video_completion_rate, 1)
            if video_url
            else None,
        }

    @staticmethod
    def generate_quality_report(lesson: Lesson) -> Dict:
        """Generate comprehensive quality report"""
        quality = LessonQualityAnalyzer.get_lesson_quality_score(lesson)
        engagement = LessonQualityAnalyzer.get_lesson_engagement_metrics(lesson)
        avg_time = LessonQualityAnalyzer.get_average_completion_time(lesson)

        # Determine quality tier
        if quality["score"] >= 4.0:
            tier = "excellent"
        elif quality["score"] >= 3.0:
            tier = "good"
        elif quality["score"] >= 2.0:
            tier = "needs_improvement"
        else:
            tier = "poor"

        return {
            "lesson": lesson,
            "quality": quality,
            "engagement": engagement,
            "average_completion_time_minutes": round(avg_time, 1) if avg_time else None,
            "quality_tier": tier,
            "recommendations": LessonQualityAnalyzer._generate_recommendations(
                quality, engagement
            ),
        }

    @staticmethod
    def _generate_recommendations(quality: Dict, engagement: Dict) -> list[str]:
        """Generate improvement recommendations based on metrics"""
        recommendations = []

        if quality["score"] < 3.0:
            recommendations.append(
                "Consider improving content quality based on student feedback"
            )

        if quality.get("content_quality", 0) < 3.0:
            recommendations.append("Focus on improving content clarity and structure")

        if quality.get("examples_helpful", 0) < 3.0:
            recommendations.append("Add more practical examples and exercises")

        if engagement["completion_rate"] < 50:
            recommendations.append(
                "Work on increasing lesson completion rates - consider breaking into smaller modules"
            )

        if (
            engagement.get("video_completion_rate", 100) < 70
            and engagement.get("video_completion_rate") is not None
        ):
            recommendations.append("Improve video content engagement")

        if not recommendations:
            recommendations.append(
                "Lesson is performing well - continue monitoring feedback"
            )

        return recommendations
