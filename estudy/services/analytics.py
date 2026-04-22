"""
Analytics service for lesson performance tracking
"""

from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone

from ..models import (
    Lesson,
    LessonAnalytics,
    LessonComment,
    LessonProgress,
    LessonRating,
    TestAttempt,
)


class LessonAnalyticsService:
    """Service for generating and managing lesson analytics"""

    @staticmethod
    def update_lesson_analytics(lesson, date=None):
        """Update analytics for a specific lesson and date"""
        if date is None:
            date = timezone.now().date()

        # Get data for the date
        start_date = timezone.datetime.combine(date, timezone.datetime.min.time())
        end_date = start_date + timedelta(days=1)

        # Basic engagement metrics
        progress_records = LessonProgress.objects.filter(
            lesson=lesson, updated_at__range=(start_date, end_date)
        )

        views = progress_records.count()
        unique_views = progress_records.values("user").distinct().count()
        completions = progress_records.filter(completed=True).count()

        # Time metrics
        completed_progress = progress_records.filter(
            completed=True, completed_at__isnull=False
        )

        if completed_progress.exists():
            avg_time = (
                completed_progress.aggregate(
                    avg_time=Avg("fastest_completion_seconds")
                )["avg_time"]
                or 0
            )
            times = list(
                completed_progress.values_list("fastest_completion_seconds", flat=True)
            )
            times.sort()
            median_time = times[len(times) // 2] if times else 0
        else:
            avg_time = 0
            median_time = 0

        # Performance metrics
        test_attempts = TestAttempt.objects.filter(
            test__lesson=lesson, created_at__range=(start_date, end_date)
        )

        if test_attempts.exists():
            avg_score = (
                test_attempts.aggregate(avg_score=Avg("awarded_points"))["avg_score"]
                or 0
            )
        else:
            avg_score = 0

        completion_rate = (completions / views * 100) if views > 0 else 0

        # Social metrics
        comments = LessonComment.objects.filter(
            lesson=lesson,
            created_at__range=(start_date, end_date),
            is_approved=True,
            is_hidden=False,
        )
        comments_count = comments.count()

        ratings = LessonRating.objects.filter(
            lesson=lesson, created_at__range=(start_date, end_date)
        )
        ratings_count = ratings.count()

        if ratings.exists():
            avg_rating = ratings.aggregate(avg_rating=Avg("rating"))["avg_rating"] or 0
        else:
            avg_rating = 0

        # Create or update analytics record
        analytics, created = LessonAnalytics.objects.update_or_create(
            lesson=lesson,
            date=date,
            defaults={
                "views": views,
                "unique_views": unique_views,
                "completions": completions,
                "avg_time_spent": int(avg_time),
                "median_time_spent": int(median_time),
                "avg_score": avg_score,
                "completion_rate": completion_rate,
                "comments_count": comments_count,
                "ratings_count": ratings_count,
                "avg_rating": avg_rating,
                "drop_off_points": {},  # TODO: implement drop-off analysis
                "error_count": 0,  # TODO: implement error tracking
                "load_time_avg": 0,  # TODO: implement load time tracking
            },
        )

        return analytics

    @staticmethod
    def get_lesson_overview_stats(teacher_user):
        """Get overview statistics for all lessons (for teachers)"""
        # Get all lessons (assuming teacher can see all for now)
        lessons = Lesson.objects.all()

        total_lessons = lessons.count()
        total_views = LessonProgress.objects.filter(lesson__in=lessons).count()

        total_completions = LessonProgress.objects.filter(
            lesson__in=lessons, completed=True
        ).count()

        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_views = LessonProgress.objects.filter(
            lesson__in=lessons, updated_at__gte=week_ago
        ).count()

        recent_completions = LessonProgress.objects.filter(
            lesson__in=lessons, completed=True, completed_at__gte=week_ago
        ).count()

        # Ratings and comments
        total_ratings = LessonRating.objects.filter(lesson__in=lessons).count()
        total_comments = LessonComment.objects.filter(
            lesson__in=lessons, is_approved=True, is_hidden=False
        ).count()

        avg_rating = (
            LessonRating.objects.filter(lesson__in=lessons).aggregate(
                avg=Avg("rating")
            )["avg"]
            or 0
        )

        return {
            "total_lessons": total_lessons,
            "total_views": total_views,
            "total_completions": total_completions,
            "completion_rate": (total_completions / total_views * 100)
            if total_views > 0
            else 0,
            "recent_views": recent_views,
            "recent_completions": recent_completions,
            "total_ratings": total_ratings,
            "total_comments": total_comments,
            "avg_rating": round(avg_rating, 1),
        }

    @staticmethod
    def get_top_performing_lessons(teacher_user, limit=5):
        """Get top performing lessons by completion rate"""
        lessons = Lesson.objects.annotate(
            total_views=Count("progress_records"),
            completions=Count(
                "progress_records", filter=Q(progress_records__completed=True)
            ),
            avg_rating=Avg("ratings__rating"),
        ).filter(total_views__gt=0)

        # Calculate completion rate
        top_lessons = []
        for lesson in lessons:
            completion_rate = (
                (lesson.completions / lesson.total_views * 100)
                if lesson.total_views > 0
                else 0
            )
            top_lessons.append(
                {
                    "lesson": lesson,
                    "completion_rate": completion_rate,
                    "total_views": lesson.total_views,
                    "completions": lesson.completions,
                    "avg_rating": lesson.avg_rating or 0,
                }
            )

        # Sort by completion rate
        top_lessons.sort(key=lambda x: x["completion_rate"], reverse=True)
        return top_lessons[:limit]

    @staticmethod
    def get_lesson_engagement_trends(lesson, days=30):
        """Get engagement trends for a lesson over time"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        analytics = LessonAnalytics.objects.filter(
            lesson=lesson, date__range=(start_date, end_date)
        ).order_by("date")

        return list(
            analytics.values(
                "date", "views", "completions", "comments_count", "ratings_count"
            )
        )
