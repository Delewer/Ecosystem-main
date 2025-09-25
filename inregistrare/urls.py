from django.urls import path
from .views import register, login_view, logout, profile, edit_profile

urlpatterns = [
    path('signup/', register, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout, name='logout'),
    path('profile/', profile, name='inregistrare_profile'),
    path('edit_profile/', edit_profile, name='edit_profile')
]
