﻿"""unitex_school URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from estudy import views
from inregistrare import views as account_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', account_views.login_view, name='login'),
    path('logout/', account_views.logout, name='logout'),
    path('accounts/login/', account_views.login_view),
    path('accounts/logout/', account_views.logout),
    path('admin/', admin.site.urls),
    path('estudy/', include('estudy.urls')),
    path('auth/', include('inregistrare.urls')),
    path('', include('unitexapp.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
