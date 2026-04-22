from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.authtoken.views import obtain_auth_token

from . import api_views, views

app_name = "estudy"


urlpatterns = [
    path("", views.dashboard_router, name="dashboard"),
    path("dashboard/student/", views.student_dashboard, name="student_dashboard"),
    path("dashboard/teacher/", views.teacher_dashboard, name="teacher_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/parent/", views.parent_dashboard, name="parent_dashboard"),
    path("lessons/", views.lessons_list, name="lessons_list"),
    path("typing-game/", views.typing_game, name="typing_game"),
    path("world-map/", views.world_map_view, name="world_map"),
    path(
        "lessons/modul-1-alfabetizare-digitala/",
        views.lesson_module_digital_literacy,
        name="lesson_module_digital_literacy",
    ),
    path("lessons/<slug:slug>/", views.lesson_detail, name="lesson_detail"),
    path(
        "lessons/<slug:slug>/share-card/",
        views.share_card_view,
        name="share_card",
    ),
    path(
        "lessons/<slug:slug>/toggle/",
        views.toggle_lesson_completion,
        name="toggle_lesson_completion",
    ),
    path("lessons/<slug:slug>/ai-hint/", views.ai_hint, name="ai_hint"),
    path(
        "tests/<int:test_id>/submit/",
        views.submit_test_attempt,
        name="submit_test_attempt",
    ),
    path("missions/", views.missions_view, name="missions"),
    path("leaderboard/", views.leaderboard_view, name="leaderboard"),
    path("notifications/", views.notifications_center, name="notifications"),
    path("classrooms/", views.classroom_hub, name="classrooms"),
    path("classrooms/<int:pk>/", views.classroom_detail, name="classroom_detail"),
    path("projects/", views.projects_view, name="projects"),
    path("projects/<slug:slug>/submit/", views.submit_project, name="project_submit"),
    path("community/", views.community_forum, name="community"),
    path("community/<int:pk>/", views.community_thread, name="community_thread"),
    path("overview/", views.study_overview, name="overview"),
    path("progress/", views.user_progress, name="user_progress"),
    path(
        "onboarding/complete/",
        views.mark_onboarding_complete,
        name="mark_onboarding_complete",
    ),
    path(
        "robot-lab/",
        RedirectView.as_view(
            pattern_name="estudy:robot_lab_world_map", permanent=False
        ),
        name="robot_lab_hub",
    ),
    path(
        "robot-lab/level/<str:level_id>/",
        RedirectView.as_view(pattern_name="estudy:robot_lab_game", permanent=False),
        name="robot_lab_play",
    ),
    path("robot-lab/teacher/", views.robot_lab_teacher, name="robot_lab_teacher"),
    path("robot-lab/worlds/", views.robot_lab_world_map, name="robot_lab_world_map"),
    path(
        "robot-lab/game/<str:level_id>/",
        views.robot_lab_game,
        name="robot_lab_game",
    ),
    path("api/run-code/", views.run_code_api, name="run_code_api"),
    path("code-exercise/<int:pk>/", views.code_exercise_view, name="code_exercise"),
    # Cooperative sessions
    path("coop/create/", views.coop_create, name="coop_create"),
    path("coop/join/", views.coop_join, name="coop_join"),
    # Streak leaderboard per subject
    path(
        "leaderboard/streaks/<slug:subject_slug>/",
        views.streak_leaderboard_view,
        name="streak_leaderboard",
    ),
    # Moderation
    path("moderate/comments/", views.moderate_comments, name="moderate_comments"),
    # API endpoints for new features
    path("api/token/", obtain_auth_token, name="api_token"),
]

api_patterns = [
    path(
        "lessons/<slug:lesson_slug>/comments/",
        api_views.LessonCommentsListCreateView.as_view(),
        name="lesson_comments_api",
    ),
    path(
        "comments/<int:pk>/",
        api_views.LessonCommentDetailView.as_view(),
        name="lesson_comment_detail_api",
    ),
    path(
        "comments/<int:comment_id>/replies/",
        api_views.CommentRepliesView.as_view(),
        name="comment_replies_api",
    ),
    path(
        "comments/<int:comment_id>/like/",
        api_views.toggle_comment_like,
        name="toggle_comment_like_api",
    ),
    path(
        "lessons/<slug:lesson_slug>/rate/",
        api_views.LessonRatingCreateView.as_view(),
        name="lesson_rating_api",
    ),
    path(
        "ratings/<int:pk>/",
        api_views.LessonRatingDetailView.as_view(),
        name="lesson_rating_detail_api",
    ),
    path(
        "lessons/<slug:lesson_slug>/stats/",
        api_views.lesson_stats,
        name="lesson_stats_api",
    ),
    path(
        "analytics/",
        api_views.LessonAnalyticsView.as_view(),
        name="lesson_analytics_api",
    ),
    path(
        "analytics/<slug:lesson_slug>/",
        api_views.LessonAnalyticsView.as_view(),
        name="lesson_analytics_detail_api",
    ),
    path(
        "progress/",
        api_views.LessonProgressListView.as_view(),
        name="lesson_progress_api",
    ),
    path(
        "robot-lab/mentor/",
        api_views.robot_lab_mentor_feedback,
        name="robot_lab_mentor_api",
    ),
    path(
        "robot-lab/levels/",
        api_views.robot_lab_levels,
        name="robot_lab_levels_api",
    ),
    path(
        "robot-lab/levels/<str:level_id>/",
        api_views.robot_lab_level_detail,
        name="robot_lab_level_detail_api",
    ),
    path(
        "robot-lab/runs/",
        api_views.robot_lab_run,
        name="robot_lab_run_api",
    ),
    path(
        "robot-lab/progress/",
        api_views.robot_lab_progress,
        name="robot_lab_progress_api",
    ),
    path(
        "robot-lab/worlds/",
        api_views.robot_lab_worlds,
        name="robot_lab_worlds_api",
    ),
    path(
        "robot-lab/skins/",
        api_views.robot_lab_skins,
        name="robot_lab_skins_api",
    ),
    path(
        "robot-lab/skins/select/",
        api_views.robot_lab_skin_select,
        name="robot_lab_skin_select_api",
    ),
]

urlpatterns += [
    path("api/", include(api_patterns)),
    path("api/v1/", include(api_patterns)),
]
