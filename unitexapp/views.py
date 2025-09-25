from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings

def index(request):
    return render(request, 'unitexapp/index.html')


from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings

def submit_form(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        
        subject = "Новая заявка с сайта"
        message = f"Имя: {name}\nНомер телефона: {phone}"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = ['recipient_email@example.com']

        try:
            # Отправка письма
            sent_count = send_mail(subject, message, from_email, recipient_list)
            
            if sent_count > 0:
                return HttpResponse(f"Данные получены и отправлены на почту: {name}, {phone}")
            else:
                return HttpResponse("Ошибка отправки письма.")
        except Exception as e:
            return HttpResponse(f"Ошибка при отправке письма: {str(e)}")
    
    return HttpResponse("Ошибка запроса")
