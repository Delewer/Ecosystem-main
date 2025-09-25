from django.urls import path

from . import views


app_name = "estudy"


urlpatterns = [
    path("", views.lessons_list, name="lessons_list"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("lessons/<slug:slug>/toggle/", views.toggle_lesson_completion, name="toggle_lesson_completion"),
    path("tests/<int:test_id>/submit/", views.submit_test_attempt, name="submit_test_attempt"),
    path("lessons/<slug:slug>/", views.lesson_detail, name="lesson_detail"),
]
