from django.urls import path

from .views import (
    edit_profile,
    login_view,
    logout,
    politica_cookie,
    profile,
    register,
    termeni_si_conditii,
)

urlpatterns = [
    path("signup/", register, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout, name="logout"),
    path("profile/", profile, name="inregistrare_profile"),
    path("edit_profile/", edit_profile, name="edit_profile"),
    path("termeni-si-conditii/", termeni_si_conditii, name="termeni_si_conditii"),
    path("politica-cookie/", politica_cookie, name="politica_cookie"),
]
