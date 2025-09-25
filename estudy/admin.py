from django.contrib import admin

from .models import (
    Lesson,
    LessonProgress,
    Reward,
    Subject,
    Test,
    TestAttempt,
    UserReward,
)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "date", "difficulty", "age_bracket", "duration_minutes")
    list_filter = ("subject", "difficulty", "age_bracket", "date")
    search_fields = ("title", "subject__name", "content")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "completed", "updated_at")
    list_filter = ("completed", "lesson__subject")
    search_fields = ("user__username", "lesson__title")


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(UserReward)
class UserRewardAdmin(admin.ModelAdmin):
    list_display = ("user", "reward", "date_awarded")
    search_fields = ("user__username", "reward__name")


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("question", "lesson")
    search_fields = ("question", "lesson__title")


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "test", "is_correct", "created_at")
    list_filter = ("is_correct",)
    search_fields = ("user__username", "test__question")
