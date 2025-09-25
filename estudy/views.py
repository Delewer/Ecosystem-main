import random

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Lesson, LessonProgress, Subject, Test, TestAttempt, UserProfile, check_and_award_rewards


LESSON_ENRICHMENTS = {
    "nivel-1-prieteni-cu-variabilele": {
        "concept_cards": [
            {
                "title": "Cutia magica",
                "emoji": "🧰",
                "description": "O variabila este ca o cutie cu eticheta: ii dai un nume si pui inauntru o valoare pe care o poti folosi ori de cate ori ai nevoie.",
            },
            {
                "title": "Echipa de variabile",
                "emoji": "🤝",
                "description": "Variabilele pot lucra impreuna. Creeaza doua cutii, schimba continutul si compune mesaje prietenoase pentru colegii tai.",
            },
            {
                "title": "Scorul fericit",
                "emoji": "🏆",
                "description": "In jocuri, variabilele tin minte punctajul si nivelul. Daca actualizezi scorul la fiecare moneda colectata, totul devine automat!",
            },
        ],
        "story_steps": [
            {
                "title": "Da un nume",
                "detail": "Alege un nume clar pentru cutia ta digitala, de exemplu `nume_elev`.",
                "tip": "Foloseste snake_case pentru a citi usor numele.",
            },
            {
                "title": "Pastreaza valoarea",
                "detail": "Stocheaza un cuvant, un numar sau chiar o lista cu activitatile tale preferate.",
                "tip": "Poti reatribui variabila oricand vrei sa schimbi povestea.",
            },
            {
                "title": "Foloseste variabila",
                "detail": "Construieste mesaje personalizate prin `print()` sau combina mai multe variabile intre ele.",
                "tip": "Intreaba-te: ce vreau sa se intample daca variabila se schimba?",
            },
        ],
        "code_challenges": [
            {
                "id": "variable-greeting",
                "title": "Salut personalizat",
                "description": "Creeaza o variabila cu numele tau si afiseaza un salut vesel folosind `print`.",
                "starter": "nume = ''\n# adauga salutul aici\n",
                "expected_keywords": ["nume =", "print"],
                "hint": "Gandeste-te cum ai scrie mesajul intr-un caiet digital.",
            },
            {
                "id": "counter-update",
                "title": "Numara pasii",
                "description": "Porneste un contor de pasi la 0 si mareste-l cu 1 dupa fiecare tura a jocului.",
                "starter": "pasi = 0\n# cand jucatorul face un pas:\n",
                "expected_keywords": ["pasi = 0", "pasi = pasi + 1||pasi += 1"],
                "hint": "Foloseste variabila pe post de scor si actualizeaz-o cu expresia potrivita.",
            },
        ],
    },
    "nivel-2-aventuri-cu-buclele": {
        "concept_cards": [
            {
                "title": "Refrenul FOR",
                "emoji": "🔁",
                "description": "Buclele `for` repeta pasii un numar clar de ori. Sunt perfecte pentru liste de provocari si misiuni.",
            },
            {
                "title": "Verificarea WHILE",
                "emoji": "🕵️",
                "description": "`while` verifica mereu o conditie. Atata timp cat raspunsul este adevarat, repetitia continua.",
            },
            {
                "title": "Butonul BREAK",
                "emoji": "⏹️",
                "description": "Uneori vrem sa iesim imediat din bucla: `break` este butonul de pauza pentru robotul tau.",
            },
        ],
        "story_steps": [
            {
                "title": "Planifica pasii",
                "detail": "Scrie pe hartie ce vrei sa repeti si de cate ori.",
                "tip": "Cu cat stii mai bine ritmul, cu atat codul devine mai scurt.",
            },
            {
                "title": "Alege bucla potrivita",
                "detail": "Foloseste `for` cand ai un numar clar de repetari si `while` cand verifici o conditie.",
                "tip": "Cand nu stii cati pasi vor fi, `while` te salveaza.",
            },
            {
                "title": "Controleaza iesirea",
                "detail": "Pregateste o variabila care schimba conditia sau foloseste `break` pentru momente speciale.",
                "tip": "Adauga si `continue` daca vrei sa sari peste pasi anume fara sa opresti bucla.",
            },
        ],
        "code_challenges": [
            {
                "id": "for-collect",
                "title": "Colectia de monede",
                "description": "Foloseste o bucla `for` pentru a adauga 5 monede intr-o lista numita `colectie`.",
                "starter": "colectie = []\n# adauga aici bucla ta\n",
                "expected_keywords": ["for", "range", "append"],
                "hint": "`range(5)` iti ofera exact cei cinci pasi de care ai nevoie.",
            },
            {
                "id": "while-energy",
                "title": "Energia robotului",
                "description": "Seteaza energia la 10 si foloseste o bucla `while` pentru a o scadea pana ajunge la 0. Afiseaza energia la fiecare pas.",
                "starter": "energie = 10\nwhile energie > 0:\n    # completeaza aici\n",
                "expected_keywords": ["while energie > 0", "energie -= 1||energie = energie - 1", "print"],
                "hint": "Nu uita sa actualizezi energia in interiorul buclei, altfel robotul nu se va opri.",
            },
        ],
    },
    "nivel-3-super-puteri-cu-functii": {
        "concept_cards": [
            {
                "title": "Super-putere ambalata",
                "emoji": "🦸",
                "description": "O functie aduna mai multe instructiuni si le ofera un nume. Poti invoca super-puterea oricand ai nevoie.",
            },
            {
                "title": "Bagheta parametrilor",
                "emoji": "🪄",
                "description": "Parametrii primesc valori noi la fiecare apel. Asa personalizam super-puterea functie.",
            },
            {
                "title": "Stralucirea return",
                "emoji": "🌟",
                "description": "`return` trimite rezultatul din interiorul functiei catre codul care a apelat-o.",
            },
        ],
        "story_steps": [
            {
                "title": "Defineste magia",
                "detail": "Scrie `def` urmat de numele functiei si de parametri intre paranteze.",
                "tip": "Un nume clar precum `calculeaza_bonus` este mai prietenos decat `f1`.",
            },
            {
                "title": "Construieste reteta",
                "detail": "Adauga instructiunile in interiorul functiei si foloseste parametrii ca ingrediente.",
                "tip": "Pastreaza functia concentrata pe un singur scop pentru a o testa usor.",
            },
            {
                "title": "Trimite rezultatul",
                "detail": "Foloseste `return` pentru a trimite valoarea calculata catre aventurierul care a chemat functia.",
                "tip": "Poti returna mai multe valori folosind tupluri sau dictionare.",
            },
        ],
        "code_challenges": [
            {
                "id": "def-greeting",
                "title": "Functia salut",
                "description": "Scrie functia `salut(nume)` care intoarce mesajul `Buna, <nume>!` si afiseaza rezultatul.",
                "starter": "# defineste functia aici\n",
                "expected_keywords": ["def salut", "return", "print"],
                "hint": "Functia poate construi mesajul si il poate trimite inapoi cu `return`.",
            },
            {
                "id": "bonus-calculator",
                "title": "Calculator de bonus",
                "description": "Creeaza functia `calculeaza_bonus(puncte, multiplu)` care inmulteste cele doua valori si returneaza rezultatul.",
                "starter": "# completeaza aici\n",
                "expected_keywords": ["def calculeaza_bonus", "return", "print"],
                "hint": "Apeleaza functia cu valori diferite pentru a verifica rezultatele.",
            },
        ],
    },
}


def is_admin(user):
    return user.is_staff


def _build_filters(request):
    return {
        "query": request.GET.get("q", "").strip(),
        "difficulty": request.GET.get("difficulty", ""),
        "subject": request.GET.get("subject", ""),
        "upcoming": request.GET.get("upcoming") == "1",
    }


@login_required
def lessons_list(request):
    profile = getattr(request.user, "userprofile", None)
    if profile and profile.status != "student" and not request.user.is_staff:
        return HttpResponseForbidden("You do not have access to this page.")

    filters = _build_filters(request)
    today = timezone.localdate()

    lessons_qs = (
        Lesson.objects.select_related("subject")
        .prefetch_related("materials")
        .annotate(
            is_completed=Exists(
                LessonProgress.objects.filter(
                    user=request.user,
                    lesson_id=OuterRef("pk"),
                    completed=True,
                )
            )
        )
    )

    if filters["query"]:
        query = filters["query"]
        lessons_qs = lessons_qs.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(subject__name__icontains=query)
        )

    if filters["difficulty"] in dict(Lesson.DIFFICULTY_CHOICES):
        lessons_qs = lessons_qs.filter(difficulty=filters["difficulty"])

    if filters["subject"].isdigit():
        lessons_qs = lessons_qs.filter(subject_id=int(filters["subject"]))

    if filters["upcoming"]:
        lessons_qs = lessons_qs.filter(date__gte=today)

    lessons = lessons_qs.order_by("date")
    total_lessons = Lesson.objects.count()
    completed_count = LessonProgress.objects.filter(user=request.user, completed=True).count()
    progress_percent = round((completed_count / total_lessons) * 100) if total_lessons else 0

    upcoming_lessons = lessons_qs.filter(date__gte=today).order_by("date")[:5]
    latest_resources = lessons_qs.order_by("-updated_at")[:4]

    subjects = Subject.objects.annotate(lesson_total=Count("lessons"))
    user_rewards = request.user.rewards.select_related("reward")

    context = {
        "lessons": lessons,
        "subjects": subjects,
        "filters": filters,
        "progress": {
            "completed": completed_count,
            "total": total_lessons,
            "percent": progress_percent,
        },
        "upcoming_lessons": upcoming_lessons,
        "latest_resources": latest_resources,
        "rewards": [relation.reward for relation in user_rewards],
        "difficulty_choices": Lesson.DIFFICULTY_CHOICES,
    }

    return render(request, "estudy/lessons_list.html", context)


@login_required
def lesson_detail(request, slug):
    lesson = get_object_or_404(
        Lesson.objects.select_related("subject", "practice").prefetch_related("materials", "tests"),
        slug=slug,
    )

    progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)

    attempts = TestAttempt.objects.filter(user=request.user, test__lesson=lesson).select_related("test")
    attempts_by_test = {attempt.test_id: attempt for attempt in attempts}

    related_lessons = (
        Lesson.objects.filter(subject=lesson.subject)
        .exclude(pk=lesson.pk)
        .order_by("date")[:3]
    )

    tests = []
    for test in lesson.tests.all():
        answers = [test.correct_answer, *test.wrong_answers]
        random.shuffle(answers)
        tests.append({
            "instance": test,
            "answers": answers,
            "attempt": attempts_by_test.get(test.id),
        })

    total_lessons = Lesson.objects.count()
    completed_count = LessonProgress.objects.filter(user=request.user, completed=True).count()
    progress_percent = round((completed_count / total_lessons) * 100) if total_lessons else 0

    enrichment = LESSON_ENRICHMENTS.get(lesson.slug, {})

    context = {
        "lesson": lesson,
        "progress": progress,
        "related_lessons": related_lessons,
        "tests": tests,
        "overall_progress": {
            "completed": completed_count,
            "total": total_lessons,
            "percent": progress_percent,
        },
        "practice": getattr(lesson, "practice", None),
        "enrichment": enrichment,
    }
    return render(request, "estudy/lesson_detail.html", context)


@require_POST
@login_required
def toggle_lesson_completion(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    progress.toggle()
    if progress.completed:
        check_and_award_rewards(request.user)

    total_lessons = Lesson.objects.count()
    completed_count = LessonProgress.objects.filter(user=request.user, completed=True).count()
    progress_percent = round((completed_count / total_lessons) * 100) if total_lessons else 0

    return JsonResponse(
        {
            "completed": progress.completed,
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
            "progress_percent": progress_percent,
            "completed_count": completed_count,
            "total_lessons": total_lessons,
        }
    )


@require_POST
@login_required
def submit_test_attempt(request, test_id):
    test = get_object_or_404(Test.objects.select_related("lesson"), pk=test_id)
    answer = request.POST.get("answer", "").strip()
    if not answer:
        return JsonResponse({"error": "Answer is required."}, status=400)

    is_correct = answer == test.correct_answer
    attempt, _ = TestAttempt.objects.update_or_create(
        test=test,
        user=request.user,
        defaults={"selected_answer": answer, "is_correct": is_correct},
    )

    response = {
        "is_correct": is_correct,
        "correct_answer": test.correct_answer,
        "explanation": test.explanation,
    }

    if is_correct:
        progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=test.lesson)
        if not progress.completed:
            progress.mark_completed()
            check_and_award_rewards(request.user)
        completed_count = LessonProgress.objects.filter(user=request.user, completed=True).count()
        total_lessons = Lesson.objects.count()
        progress_percent = round((completed_count / total_lessons) * 100) if total_lessons else 0
        response.update(
            {
                "lesson_completed": True,
                "progress_percent": progress_percent,
                "completed_count": completed_count,
                "total_lessons": total_lessons,
            }
        )
    else:
        response["lesson_completed"] = False

    return JsonResponse(response)


@login_required
def edit_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("inregistrare_profile")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "accounts/edit_profile.html", {"form": form})


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    lessons = Lesson.objects.select_related("subject").annotate(student_count=Count("progress_records"))
    top_subjects = Subject.objects.annotate(total=Count("lessons")).order_by("-total")[:5]
    total_students = UserProfile.objects.filter(status="student").count()

    context = {
        "lessons": lessons,
        "top_subjects": top_subjects,
        "total_students": total_students,
    }
    return render(request, "estudy/admin_dashboard.html", context)


@login_required
def user_progress(request):
    total_lessons = Lesson.objects.count()
    completed = LessonProgress.objects.filter(user=request.user, completed=True).count()
    progress_percent = (completed / total_lessons * 100) if total_lessons else 0
    return JsonResponse({"progress_percent": round(progress_percent, 2)})


@login_required
def estudy_view(request):
    subjects = Subject.objects.prefetch_related("lessons")
    total_lessons = Lesson.objects.count()
    completed = LessonProgress.objects.filter(user=request.user, completed=True).count()
    progress_percent = (completed / total_lessons * 100) if total_lessons else 0

    return render(
        request,
        "estudy/overview.html",
        {
            "subjects": subjects,
            "progress_percent": round(progress_percent, 2),
        },
    )
