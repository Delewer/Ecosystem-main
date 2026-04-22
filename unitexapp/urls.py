from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("estudy/", views.index, name="estudy"),
    path("submit-form", views.submit_form, name="submit_form"),
]
