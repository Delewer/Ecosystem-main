from __future__ import annotations

from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def seed_web_and_math_lessons(apps, schema_editor):
    Subject = apps.get_model("estudy", "Subject")
    Lesson = apps.get_model("estudy", "Lesson")
    Test = apps.get_model("estudy", "Test")

    today = timezone.localdate()

    # ------------------------------------------------------------------
    # Bazele Web lessons
    # ------------------------------------------------------------------
    web_subject = Subject.objects.filter(name="Bazele Web").first()
    if web_subject:
        web_lessons = [
            {
                "title": "Primul meu site web",
                "slug": "primul-meu-site-web",
                "age_bracket": "8-10",
                "difficulty": "beginner",
                "excerpt": "Descoperim ce este un site web și scriem primele etichete HTML.",
                "content": (
                    "Bun venit în lumea web-ului!\n\n"
                    "Un site web este ca o carte digitală pe care o poți citi pe orice dispozitiv conectat la internet. "
                    "Fiecare pagină este scrisă într-un limbaj special numit HTML.\n\n"
                    "HTML înseamnă HyperText Markup Language. Nu suna complicat! "
                    "Practic, folosim etichete (tags) pentru a spune browserului ce să afișeze.\n\n"
                    "Structura de bază:\n"
                    "<html>\n"
                    "  <head><title>Titlul paginii</title></head>\n"
                    "  <body>\n"
                    "    <h1>Salut, lume!</h1>\n"
                    "    <p>Acesta este primul meu paragraf.</p>\n"
                    "  </body>\n"
                    "</html>"
                ),
                "xp_reward": 50,
                "offset_days": 0,
                "tests": [
                    {
                        "question": "Ce înseamnă HTML?",
                        "correct_answer": "HyperText Markup Language",
                        "wrong_answers": [
                            "High Tech Modern Language",
                            "HyperText Machine Learning",
                            "Hyperlink and Text Markup",
                        ],
                        "explanation": "HTML = HyperText Markup Language — limbajul standard al paginilor web.",
                    },
                    {
                        "question": "Ce etichetă creează un titlu mare pe pagină?",
                        "correct_answer": "<h1>",
                        "wrong_answers": ["<title>", "<big>", "<head>"],
                        "explanation": "<h1> este cel mai mare titlu; există și <h2>, <h3> pentru subtitluri.",
                    },
                ],
            },
            {
                "title": "Stil și culoare cu CSS",
                "slug": "stil-si-culoare-cu-css",
                "age_bracket": "11-13",
                "difficulty": "beginner",
                "excerpt": "Adăugăm culori, fonturi și spațiere paginilor noastre HTML cu CSS.",
                "content": (
                    "HTML construiește structura paginii — CSS o face frumoasă!\n\n"
                    "CSS (Cascading Style Sheets) este limbajul de stilizare al web-ului. "
                    "Cu CSS putem schimba culori, fonturi, dimensiuni și aranjament.\n\n"
                    "Sintaxa CSS:\n"
                    "selector { proprietate: valoare; }\n\n"
                    "Exemplu:\n"
                    "h1 { color: blue; font-size: 32px; }\n"
                    "p  { color: gray; margin: 10px; }\n\n"
                    "Există trei moduri de a adăuga CSS:\n"
                    "1. Inline: <p style='color:red'>text</p>\n"
                    "2. Intern: <style> ... </style> în <head>\n"
                    "3. Extern: fișier .css separat (recomandat)"
                ),
                "xp_reward": 60,
                "offset_days": 1,
                "tests": [
                    {
                        "question": "Ce limbaj adaugă stiluri vizuale paginilor HTML?",
                        "correct_answer": "CSS",
                        "wrong_answers": ["JavaScript", "Python", "SQL"],
                        "explanation": "CSS (Cascading Style Sheets) controlează aspectul vizual.",
                    },
                    {
                        "question": "Care este sintaxa corectă pentru a colora textul unui paragraf în roșu?",
                        "correct_answer": "p { color: red; }",
                        "wrong_answers": [
                            "p.color = red",
                            "<p color='red'>",
                            "p -> color: red",
                        ],
                        "explanation": "CSS folosește sintaxa selector { proprietate: valoare; }",
                    },
                ],
            },
            {
                "title": "JavaScript: pagini interactive",
                "slug": "javascript-pagini-interactive",
                "age_bracket": "14-16",
                "difficulty": "intermediate",
                "excerpt": "Facem paginile să reacționeze la click-uri și interacțiuni cu JavaScript.",
                "content": (
                    "JavaScript este limbajul care aduce viață paginilor web!\n\n"
                    "Cu JavaScript putem:\n"
                    "- Schimba conținutul paginii fără reload\n"
                    "- Răspunde la click-uri, tastare și alte acțiuni\n"
                    "- Trimite și primi date de la server\n\n"
                    "Primul program:\n"
                    'document.getElementById("demo").innerHTML = "Salut!";\n\n'
                    "Eveniment la click:\n"
                    '<button onclick="saluta()">Click</button>\n'
                    "function saluta() {\n"
                    '    alert("Bună ziua!");\n'
                    "}\n\n"
                    "JavaScript rulează direct în browser — nu ai nevoie de nimic instalat."
                ),
                "xp_reward": 80,
                "offset_days": 2,
                "tests": [
                    {
                        "question": "Ce rol are JavaScript într-o pagină web?",
                        "correct_answer": "Adaugă interactivitate și comportament dinamic",
                        "wrong_answers": [
                            "Definește structura paginii",
                            "Stilizează elementele vizuale",
                            "Stochează datele în baza de date",
                        ],
                        "explanation": "HTML = structură, CSS = aspect, JavaScript = comportament.",
                    },
                    {
                        "question": "Cum afișăm un mesaj popup în JavaScript?",
                        "correct_answer": "alert('mesaj')",
                        "wrong_answers": [
                            "print('mesaj')",
                            "show('mesaj')",
                            "display('mesaj')",
                        ],
                        "explanation": "alert() afișează o casetă de dialog în browser.",
                    },
                ],
            },
        ]

        for entry in web_lessons:
            if Lesson.objects.filter(slug=entry["slug"]).exists():
                continue
            lesson_date = today + timedelta(days=entry["offset_days"])
            lesson = Lesson.objects.create(
                subject=web_subject,
                title=entry["title"],
                slug=entry["slug"],
                age_bracket=entry["age_bracket"],
                difficulty=entry["difficulty"],
                excerpt=entry["excerpt"],
                content=entry["content"],
                xp_reward=entry["xp_reward"],
                date=lesson_date,
            )
            for t in entry["tests"]:
                Test.objects.create(
                    lesson=lesson,
                    question=t["question"],
                    correct_answer=t["correct_answer"],
                    wrong_answers=t["wrong_answers"],
                    explanation=t["explanation"],
                )

    # ------------------------------------------------------------------
    # Matematica pentru coderi lessons
    # ------------------------------------------------------------------
    math_subject = Subject.objects.filter(name="Matematica pentru coderi").first()
    if math_subject:
        math_lessons = [
            {
                "title": "Tipare și secvențe",
                "slug": "tipare-si-secvente",
                "age_bracket": "8-10",
                "difficulty": "beginner",
                "excerpt": "Recunoaștem tipare în numere și le scriem ca programe simple.",
                "content": (
                    "Matemática și programarea sunt prietene bune!\n\n"
                    "Un tipar (pattern) este o regulă care se repetă. "
                    "De exemplu: 2, 4, 6, 8 — fiecare număr este cu 2 mai mare decât cel dinaintea lui.\n\n"
                    "În Python, putem genera astfel de secvențe cu range():\n\n"
                    "for i in range(2, 10, 2):\n"
                    "    print(i)  # afișează: 2, 4, 6, 8\n\n"
                    "range(start, stop, step):\n"
                    "- start = primul număr\n"
                    "- stop = limita (exclusiv)\n"
                    "- step = pasul (cu câte sărim)\n\n"
                    "Exercițiu: Generează numerele 1, 3, 5, 7, 9 folosind range()."
                ),
                "xp_reward": 50,
                "offset_days": 0,
                "tests": [
                    {
                        "question": "Care este pasul (step) din secvența: 5, 10, 15, 20?",
                        "correct_answer": "5",
                        "wrong_answers": ["10", "2", "20"],
                        "explanation": "Fiecare număr este cu 5 mai mare decât cel anterior — deci pasul este 5.",
                    },
                    {
                        "question": "Ce afișează range(1, 6, 2)?",
                        "correct_answer": "1, 3, 5",
                        "wrong_answers": ["1, 2, 3, 4, 5", "2, 4, 6", "1, 3, 5, 7"],
                        "explanation": "range(1, 6, 2) pornește de la 1, merge până la 6 (exclusiv) cu pasul 2: 1, 3, 5.",
                    },
                ],
            },
            {
                "title": "Logică și condiții",
                "slug": "logica-si-conditii",
                "age_bracket": "11-13",
                "difficulty": "beginner",
                "excerpt": "Înțelegem logica booleană și o aplicăm în condiții Python.",
                "content": (
                    "Logica este inima programării!\n\n"
                    "O expresie logică este fie True (adevărat) fie False (fals). "
                    "Acestea se numesc valori booleene (după matematicianul George Boole).\n\n"
                    "Operatori logici principali:\n"
                    "- and: ambele condiții trebuie să fie adevărate\n"
                    "- or:  cel puțin una trebuie să fie adevărată\n"
                    "- not: inversează valoarea\n\n"
                    "Exemplu:\n"
                    "varsta = 12\n"
                    "are_cont = True\n"
                    "if varsta >= 10 and are_cont:\n"
                    "    print('Acces permis!')\n\n"
                    "Tabela de adevăr pentru AND:\n"
                    "True  AND True  = True\n"
                    "True  AND False = False\n"
                    "False AND True  = False\n"
                    "False AND False = False"
                ),
                "xp_reward": 60,
                "offset_days": 1,
                "tests": [
                    {
                        "question": "Care este rezultatul expresiei: True and False?",
                        "correct_answer": "False",
                        "wrong_answers": ["True", "None", "Error"],
                        "explanation": "AND returnează True doar dacă AMBELE valori sunt True.",
                    },
                    {
                        "question": "Ce valoare are: not True?",
                        "correct_answer": "False",
                        "wrong_answers": ["True", "None", "0"],
                        "explanation": "not inversează valoarea: not True = False, not False = True.",
                    },
                ],
            },
            {
                "title": "Algoritmi de sortare",
                "slug": "algoritmi-de-sortare",
                "age_bracket": "14-16",
                "difficulty": "intermediate",
                "excerpt": "Explorăm cum calculatorul sortează o listă și de ce contează eficiența.",
                "content": (
                    "Cum sortează calculatorul o listă?\n\n"
                    "Sortarea este una dintre cele mai fundamentale operații în informatică. "
                    "Există mai mulți algoritmi — diferă prin numărul de operații necesare.\n\n"
                    "Bubble Sort (simplu, dar lent):\n"
                    "Comparăm perechi adiacente și le schimbăm dacă sunt în ordine greșită.\n\n"
                    "def bubble_sort(arr):\n"
                    "    n = len(arr)\n"
                    "    for i in range(n):\n"
                    "        for j in range(n - i - 1):\n"
                    "            if arr[j] > arr[j + 1]:\n"
                    "                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n"
                    "    return arr\n\n"
                    "Complexitate: O(n²) — cu cât lista e mai mare, cu atât mai lent.\n\n"
                    "Python are sort() încorporat (Timsort, O(n log n)) — mult mai eficient!\n"
                    "numere = [5, 2, 8, 1, 9]\n"
                    "numere.sort()\n"
                    "print(numere)  # [1, 2, 5, 8, 9]"
                ),
                "xp_reward": 80,
                "offset_days": 2,
                "tests": [
                    {
                        "question": "Ce algoritm compară perechi adiacente și le schimbă dacă sunt în ordine greșită?",
                        "correct_answer": "Bubble Sort",
                        "wrong_answers": ["Quick Sort", "Merge Sort", "Binary Search"],
                        "explanation": "Bubble Sort parcurge lista de mai multe ori și 'ridică' elementele mari spre final.",
                    },
                    {
                        "question": "Ce metodă Python sortează o listă direct?",
                        "correct_answer": "lista.sort()",
                        "wrong_answers": [
                            "sorted(lista)",
                            "lista.order()",
                            "sort(lista)",
                        ],
                        "explanation": "lista.sort() sortează lista 'in-place'; sorted() returnează o copie nouă.",
                    },
                ],
            },
        ]

        for entry in math_lessons:
            if Lesson.objects.filter(slug=entry["slug"]).exists():
                continue
            lesson_date = today + timedelta(days=entry["offset_days"])
            lesson = Lesson.objects.create(
                subject=math_subject,
                title=entry["title"],
                slug=entry["slug"],
                age_bracket=entry["age_bracket"],
                difficulty=entry["difficulty"],
                excerpt=entry["excerpt"],
                content=entry["content"],
                xp_reward=entry["xp_reward"],
                date=lesson_date,
            )
            for t in entry["tests"]:
                Test.objects.create(
                    lesson=lesson,
                    question=t["question"],
                    correct_answer=t["correct_answer"],
                    wrong_answers=t["wrong_answers"],
                    explanation=t["explanation"],
                )


def reverse_migration(apps, schema_editor):
    Lesson = apps.get_model("estudy", "Lesson")
    slugs = [
        "primul-meu-site-web",
        "stil-si-culoare-cu-css",
        "javascript-pagini-interactive",
        "tipare-si-secvente",
        "logica-si-conditii",
        "algoritmi-de-sortare",
    ]
    Lesson.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0047_fix_subjects_and_add_curriculum"),
    ]

    operations = [
        migrations.RunPython(
            seed_web_and_math_lessons,
            reverse_migration,
        ),
    ]
