from django.contrib import admin

from .models import (
    AIUsageCost,
    AuditTrailEntry,
    CodeExercise,
    CommunityCuratedAnswer,
    CosmeticPerk,
    Course,
    CourseGoal,
    DiagnosticAttempt,
    DiagnosticTest,
    EventLog,
    FeatureFlag,
    LearningPlan,
    LearningPlanItem,
    Lesson,
    LessonHealthScore,
    Module,
    OfflineProgressQueue,
    PeerReview,
    Project,
    ProjectEvaluation,
    ProjectSubmission,
    RobotLabAttemptLog,
    RobotLabLevelProgress,
    RobotLabRun,
    RobotLabSkillProfile,
    Rubric,
    RubricCriterion,
    SeasonalEvent,
    StreakFreezeBalance,
    Subject,
    Test,
    TopicTag,
    UserCosmeticPerk,
    UserSeasonalProgress,
)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "subject",
        "date",
        "difficulty",
        "age_bracket",
        "duration_minutes",
    )
    list_filter = ("subject", "difficulty", "age_bracket", "date")
    search_fields = ("title", "subject__name", "content")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(CodeExercise)
class CodeExerciseAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "language", "difficulty_level", "points")
    list_filter = ("language", "difficulty_level")
    search_fields = ("title", "lesson__title")


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("question", "lesson", "difficulty", "points")
    list_filter = ("difficulty",)
    search_fields = ("question", "lesson__title")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "duration_weeks", "subject")
    list_filter = ("level", "subject")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(CourseGoal)
class CourseGoalAdmin(admin.ModelAdmin):
    list_display = ("course", "description")
    search_fields = ("description", "course__title")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(TopicTag)
class TopicTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ("key", "enabled", "rollout_percentage", "updated_at")
    list_filter = ("enabled",)
    search_fields = ("key", "description")


@admin.register(LearningPlan)
class LearningPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "plan_type", "status", "start_date")
    list_filter = ("status", "plan_type")
    search_fields = ("user__username", "course__title")


@admin.register(LearningPlanItem)
class LearningPlanItemAdmin(admin.ModelAdmin):
    list_display = ("plan", "lesson", "status", "order", "due_date")
    list_filter = ("status",)
    search_fields = ("plan__user__username", "lesson__title")


@admin.register(LessonHealthScore)
class LessonHealthScoreAdmin(admin.ModelAdmin):
    list_display = (
        "lesson",
        "score",
        "quality_score",
        "completion_rate",
        "avg_rating",
        "computed_at",
    )
    list_filter = ("computed_at",)
    search_fields = ("lesson__title",)


@admin.register(AIUsageCost)
class AIUsageCostAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "model_name",
        "provider",
        "total_tokens",
        "cost",
        "currency",
        "created_at",
    )
    list_filter = ("provider", "model_name", "currency")
    search_fields = ("user__username", "request__question")


@admin.register(DiagnosticTest)
class DiagnosticTestAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "module", "recommended_level")
    list_filter = ("recommended_level", "course")
    search_fields = ("title", "description")


@admin.register(DiagnosticAttempt)
class DiagnosticAttemptAdmin(admin.ModelAdmin):
    list_display = ("test", "user", "score", "recommended_level", "taken_at")
    list_filter = ("recommended_level",)
    search_fields = ("user__username", "test__title")


@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title",)


@admin.register(RubricCriterion)
class RubricCriterionAdmin(admin.ModelAdmin):
    list_display = ("rubric", "name", "weight", "max_score", "order")
    list_filter = ("rubric",)
    search_fields = ("name", "rubric__title")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "level", "rubric")
    list_filter = ("status", "level")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(ProjectSubmission)
class ProjectSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "student",
        "attempt_no",
        "status",
        "uploaded_at",
        "score",
    )
    list_filter = ("status",)
    search_fields = ("project__title", "student__username")


@admin.register(ProjectEvaluation)
class ProjectEvaluationAdmin(admin.ModelAdmin):
    list_display = ("submission", "evaluator", "total_score", "created_at")
    list_filter = ("evaluator",)
    search_fields = ("submission__project__title", "evaluator__username")


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "user", "created_at")
    list_filter = ("event_type",)
    search_fields = ("user__username",)


@admin.register(RobotLabSkillProfile)
class RobotLabSkillProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "sequencing_score",
        "loop_score",
        "condition_score",
        "function_score",
        "debugging_score",
        "updated_at",
    )
    search_fields = ("user__username",)


@admin.register(RobotLabAttemptLog)
class RobotLabAttemptLogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "level_id",
        "attempt_number",
        "error_type",
        "primary_error",
        "typical_error",
        "solved",
        "created_at",
    )
    list_filter = ("error_type", "typical_error", "solved")
    search_fields = ("user__username", "level_id", "primary_error")


@admin.register(RobotLabRun)
class RobotLabRunAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "level_id",
        "attempt_number",
        "error_type",
        "primary_error",
        "solved",
        "steps_used",
        "duration_ms",
        "created_at",
    )
    list_filter = ("error_type", "solved")
    search_fields = ("user__username", "level_id", "primary_error")


@admin.register(RobotLabLevelProgress)
class RobotLabLevelProgressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "level_id",
        "unlocked",
        "completed",
        "attempts_count",
        "best_steps",
        "xp_awarded_total",
        "updated_at",
    )
    list_filter = ("unlocked", "completed")
    search_fields = ("user__username", "level_id")


@admin.register(CommunityCuratedAnswer)
class CommunityCuratedAnswerAdmin(admin.ModelAdmin):
    list_display = ("thread", "reply", "curated_by", "curated_at")
    list_filter = ("curated_at",)
    search_fields = ("thread__title", "reply__body", "curated_by__username")


@admin.register(CosmeticPerk)
class CosmeticPerkAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "rarity", "unlock_min_level", "is_active")
    list_filter = ("category", "rarity", "is_active")
    search_fields = ("title", "slug")


@admin.register(UserCosmeticPerk)
class UserCosmeticPerkAdmin(admin.ModelAdmin):
    list_display = ("user", "perk", "source", "is_equipped", "unlocked_at")
    list_filter = ("is_equipped",)
    search_fields = ("user__username", "perk__title", "perk__slug")


@admin.register(StreakFreezeBalance)
class StreakFreezeBalanceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "available_tokens",
        "used_tokens",
        "last_awarded_streak",
        "updated_at",
    )
    list_filter = ("updated_at",)
    search_fields = ("user__username",)


@admin.register(SeasonalEvent)
class SeasonalEventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "start_date",
        "end_date",
        "points_goal",
        "reward_xp",
        "is_active",
    )
    list_filter = ("is_active", "start_date", "end_date")
    search_fields = ("title", "slug")


@admin.register(UserSeasonalProgress)
class UserSeasonalProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "points", "completed_at", "updated_at")
    list_filter = ("event", "completed_at")
    search_fields = ("user__username", "event__title", "event__slug")


@admin.register(AuditTrailEntry)
class AuditTrailEntryAdmin(admin.ModelAdmin):
    list_display = ("event_type", "user", "source", "created_at", "record_hash")
    list_filter = ("event_type", "source", "hash_algorithm")
    search_fields = ("user__username", "record_hash")


@admin.register(OfflineProgressQueue)
class OfflineProgressQueueAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "synced", "created_at", "synced_at")
    list_filter = ("synced",)
    search_fields = ("user__username", "lesson__title")


@admin.register(PeerReview)
class PeerReviewAdmin(admin.ModelAdmin):
    list_display = ("submission", "reviewer", "score", "created_at")
    search_fields = ("submission__project__title", "reviewer__username")
