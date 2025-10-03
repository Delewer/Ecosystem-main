from django.contrib import admin

from .models import (
    AIHintRequest,
    AssignmentSubmission,
    Badge,
    ClassAssignment,
    Classroom,
    ClassroomMembership,
    CommunityReply,
    CommunityThread,
    DailyChallenge,
    LeaderboardSnapshot,
    Lesson,
    LessonProgress,
    LearningPath,
    LearningPathLesson,
    LearningRecommendation,
    Mission,
    Notification,
    ParentChildLink,
    Project,
    ProjectSubmission,
    Reward,
    Subject,
    Test,
    TestAttempt,
    UserBadge,
    UserMission,
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
    list_display = ("user", "lesson", "completed", "points_earned", "updated_at")
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
    list_display = ("question", "lesson", "difficulty", "points")
    search_fields = ("question", "lesson__title")


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "test", "is_correct", "awarded_points", "created_at")
    list_filter = ("is_correct",)
    search_fields = ("user__username", "test__question")


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "rule", "threshold", "xp_reward")
    search_fields = ("name", "description")


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "awarded_at")
    search_fields = ("user__username", "badge__name")


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ("title", "frequency", "target_value", "reward_points", "is_active")
    list_filter = ("frequency", "is_active")
    search_fields = ("title", "description")


@admin.register(UserMission)
class UserMissionAdmin(admin.ModelAdmin):
    list_display = ("user", "mission", "progress", "completed")
    list_filter = ("completed", "mission__frequency")
    search_fields = ("user__username", "mission__title")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "title", "category", "created_at", "read_at")
    list_filter = ("category", "created_at")
    search_fields = ("recipient__username", "title")


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "invite_code", "created_at", "archived")
    search_fields = ("name", "invite_code", "owner__username")


@admin.register(ClassroomMembership)
class ClassroomMembershipAdmin(admin.ModelAdmin):
    list_display = ("classroom", "user", "role", "points")
    list_filter = ("role",)
    search_fields = ("classroom__name", "user__username")


@admin.register(ClassAssignment)
class ClassAssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "classroom", "assignment_type", "due_date")
    list_filter = ("assignment_type", "due_date")
    search_fields = ("title", "classroom__name")


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "status", "submitted_at")
    list_filter = ("status",)
    search_fields = ("assignment__title", "student__username")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "points_reward", "estimated_minutes")
    list_filter = ("level",)
    search_fields = ("title", "summary")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(ProjectSubmission)
class ProjectSubmissionAdmin(admin.ModelAdmin):
    list_display = ("project", "student", "status", "uploaded_at")
    list_filter = ("status",)
    search_fields = ("project__title", "student__username")


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ("title", "difficulty", "audience", "is_featured")
    list_filter = ("difficulty", "is_featured")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(LearningPathLesson)
class LearningPathLessonAdmin(admin.ModelAdmin):
    list_display = ("path", "lesson", "order")
    list_filter = ("path",)
    search_fields = ("path__title", "lesson__title")


@admin.register(LearningRecommendation)
class LearningRecommendationAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "score", "created_at", "consumed")
    list_filter = ("consumed",)
    search_fields = ("user__username", "lesson__title")


@admin.register(ParentChildLink)
class ParentChildLinkAdmin(admin.ModelAdmin):
    list_display = ("parent", "child", "created_at")
    search_fields = ("parent__username", "child__username")


@admin.register(CommunityThread)
class CommunityThreadAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "is_pinned", "is_locked", "created_at")
    list_filter = ("is_pinned", "is_locked")
    search_fields = ("title", "created_by__username")


@admin.register(CommunityReply)
class CommunityReplyAdmin(admin.ModelAdmin):
    list_display = ("thread", "created_by", "created_at", "is_flagged")
    list_filter = ("is_flagged",)
    search_fields = ("thread__title", "created_by__username")


@admin.register(DailyChallenge)
class DailyChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date", "points")
    list_filter = ("start_date", "end_date")
    search_fields = ("title",)


@admin.register(AIHintRequest)
class AIHintRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "created_at", "resolved_at")
    list_filter = ("resolved_at",)
    search_fields = ("user__username", "lesson__title")


@admin.register(LeaderboardSnapshot)
class LeaderboardSnapshotAdmin(admin.ModelAdmin):
    list_display = ("period", "classroom", "generated_at")
    list_filter = ("period",)

