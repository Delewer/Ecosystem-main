import re

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST


def index(request):
    return render(request, "unitexapp/index.html")


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _json_or_text(request, payload, *, status=200):
    if _is_ajax(request):
        return JsonResponse(payload, status=status)
    return HttpResponse(payload.get("message", ""), status=status)


@require_POST
def submit_form(request):
    name = (request.POST.get("name") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    message = (request.POST.get("message") or "").strip()

    errors = {}
    if len(name) < 2:
        errors["name"] = "Te rugăm să scrii un nume valid."
    phone_digits = re.sub(r"[^\d+]", "", phone)
    if len(phone_digits) < 7:
        errors["phone"] = "Introdu un număr de telefon valid."

    if errors:
        return _json_or_text(
            request,
            {"success": False, "errors": errors, "message": "Formular incomplet."},
            status=400,
        )

    email_subject = "Cerere nouă de pe UNITEX"
    email_body = f"Nume: {name}\nTelefon: {phone}\nMesaj: {message or '—'}"

    try:
        send_mail(
            email_subject,
            email_body,
            settings.EMAIL_HOST_USER,
            [settings.EMAIL_HOST_USER],
        )
    except Exception:  # pragma: no cover - defensive
        return _json_or_text(
            request,
            {
                "success": False,
                "message": "Nu am putut trimite formularul. Încearcă din nou în câteva minute.",
            },
            status=500,
        )  # noqa: PERF203

    return _json_or_text(
        request,
        {
            "success": True,
            "message": "Mulțumim! Echipa noastră te va contacta în scurt timp.",
        },
    )
