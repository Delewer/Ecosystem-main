from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    CommentLike,
    LessonAnalytics,
    LessonComment,
    LessonMedia,
    LessonProgress,
    LessonRating,
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class LessonMediaSerializer(serializers.ModelSerializer):
    """Serializer for lesson media content"""

    class Meta:
        model = LessonMedia
        fields = [
            "video_url",
            "video_platform",
            "video_duration_seconds",
            "video_thumbnail",
            "audio_url",
            "audio_duration_seconds",
            "slides_url",
            "slides_count",
        ]


class LessonCommentSerializer(serializers.ModelSerializer):
    """Serializer for lesson comments"""

    user = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()

    class Meta:
        model = LessonComment
        fields = [
            "id",
            "lesson",
            "user",
            "content",
            "parent",
            "is_approved",
            "is_hidden",
            "likes_count",
            "replies_count",
            "is_liked_by_user",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
            "is_approved",
            "is_hidden",
        ]

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_replies_count(self, obj):
        return obj.replies.count()

    def get_is_liked_by_user(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class CommentLikeSerializer(serializers.ModelSerializer):
    """Serializer for comment likes"""

    user = UserSerializer(read_only=True)

    class Meta:
        model = CommentLike
        fields = ["id", "comment", "user", "created_at"]
        read_only_fields = ["id", "user", "created_at"]


class LessonRatingSerializer(serializers.ModelSerializer):
    """Serializer for lesson ratings"""

    user = UserSerializer(read_only=True)

    class Meta:
        model = LessonRating
        fields = [
            "id",
            "lesson",
            "user",
            "rating",
            "review",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class LessonAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for lesson analytics"""

    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = LessonAnalytics
        fields = [
            "id",
            "lesson",
            "lesson_title",
            "date",
            "views",
            "unique_views",
            "completions",
            "avg_time_spent",
            "median_time_spent",
            "avg_score",
            "completion_rate",
            "drop_off_points",
            "comments_count",
            "ratings_count",
            "avg_rating",
            "error_count",
            "load_time_avg",
        ]
        read_only_fields = ["id"]


class LessonProgressSerializer(serializers.ModelSerializer):
    """Serializer for lesson progress"""

    user = UserSerializer(read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = LessonProgress
        fields = [
            "id",
            "user",
            "lesson",
            "lesson_title",
            "completed",
            "points_earned",
            "fastest_completion_seconds",
            "completed_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "updated_at"]
