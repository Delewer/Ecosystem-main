# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import InregistrareFormular, LoginFormular, ProfileForm

def register(request):
    if request.method == "POST":
        form = InregistrareFormular(request.POST)
        if form.is_valid():
            user = form.save()  # Профиль создастся через сигнал
            auth_login(request, user)
            return redirect('index')
    else:
        form = InregistrareFormular()

    return render(request, 'accounts/signup.html', {'register': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginFormular(request, data=request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('index')
    else:
        form = LoginFormular()

    return render(request, 'accounts/login.html', {'loginform': form})

@login_required(login_url="login")
def logout(request):
    auth_logout(request)
    return redirect("login")

@login_required
def profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {'user_profile': user_profile})

@login_required
def edit_profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('inregistrare_profile')
    else:
        form = ProfileForm(instance=user_profile)

    return render(request, 'accounts/edit_profile.html', {'form': form})
