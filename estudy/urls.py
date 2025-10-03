from django.urls import path

from . import views


app_name = "estudy"


urlpatterns = [
    path("", views.dashboard_router, name="dashboard"),
    path("dashboard/student/", views.student_dashboard, name="student_dashboard"),
    path("dashboard/teacher/", views.teacher_dashboard, name="teacher_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/parent/", views.parent_dashboard, name="parent_dashboard"),
    path("lessons/", views.lessons_list, name="lessons_list"),
    path("lessons/<slug:slug>/", views.lesson_detail, name="lesson_detail"),
    path("lessons/<slug:slug>/toggle/", views.toggle_lesson_completion, name="toggle_lesson_completion"),
    path("lessons/<slug:slug>/ai-hint/", views.ai_hint, name="ai_hint"),
    path("tests/<int:test_id>/submit/", views.submit_test_attempt, name="submit_test_attempt"),
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
]
