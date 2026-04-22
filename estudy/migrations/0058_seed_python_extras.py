from datetime import date

from django.db import migrations

SCALE_LABELS = [
    "Am nevoie de putin ajutor",
    "Ma descurc bine",
    "Pot explica si altora",
]


def _content(*paragraphs):
    return "\n\n".join(paragraphs)


def _objective(description, focus_area, success_criteria):
    return {
        "description": description,
        "focus_area": focus_area,
        "success_criteria": success_criteria,
    }


def _practice(intro, instructions, success_message, draggables, targets):
    return {
        "intro": intro,
        "instructions": instructions,
        "success_message": success_message,
        "data": {
            "draggables": [
                {"id": item_id, "label": label} for item_id, label in draggables
            ],
            "targets": [
                {"prompt": prompt, "accepts": accepts} for prompt, accepts in targets
            ],
        },
    }


def _test(
    question,
    correct_answer,
    wrong_answers,
    theory_summary,
    practice_prompt,
    explanation,
):
    return {
        "question": question,
        "correct_answer": correct_answer,
        "wrong_answers": wrong_answers,
        "theory_summary": theory_summary,
        "practice_prompt": practice_prompt,
        "explanation": explanation,
    }


def _reflection(prompt, format_="text", scale_labels=None):
    payload = {"prompt": prompt, "format": format_}
    if scale_labels is not None:
        payload["scale_labels"] = scale_labels
    return payload


def _default_reflections(title, open_prompt):
    return [
        _reflection("Cum te-ai descurcat la aceasta lectie?", "scale", SCALE_LABELS),
        _reflection(open_prompt or f"Ce ai retinut din lectia «{title}»?"),
    ]


LESSON_BLUEPRINTS = [
    {
        "slug": "code-7-dictionare-pereche-cheie-valoare",
        "legacy_slugs": [],
        "title": "Code 7 · Dictionare — perechi cheie-valoare",
        "date": date(2025, 10, 28),
        "age_bracket": "11-13",
        "difficulty": "intermediate",
        "duration_minutes": 35,
        "xp_reward": 60,
        "excerpt": "Inveti sa organizezi date ca intr-un dictionar real: cauti o cheie si gasesti o valoare.",
        "theory_intro": "Un dictionar in Python este ca un dictionar de cuvinte: cauti o CHEIE si primesti o VALOARE. Perfect pentru a grupa informatii legate intre ele.",
        "content": _content(
            'Creezi un dictionar cu acolade si perechi cheie: valoare. Exemplu: `robot = {"nume": "Robo", "baterie": 80, "activ": True}`. Avem 3 perechi — nume, baterie, activ — fiecare cu propria valoare.',
            'Accesezi o valoare prin cheie: `robot["nume"]` returneaza `"Robo"`. Daca cheia nu exista, Python arunca o eroare. Pentru siguranta, poti folosi `robot.get("culoare", "necunoscut")` — returneaza a doua valoare daca cheia lipseste.',
            'Modifici sau adaugi simplu: `robot["baterie"] = 95` actualizeaza, iar `robot["culoare"] = "albastru"` adauga o noua pereche. Stergi cu `del robot["activ"]`.',
            "Iterezi peste un dictionar in 3 moduri: `for cheie in robot:` (doar cheile), `for val in robot.values():` (doar valorile), `for cheie, val in robot.items():` (ambele, cel mai folositor).",
        ),
        "theory_takeaways": [
            "Un dictionar leaga CHEI de VALORI prin paranteze acolada `{ }`.",
            "Accesezi valoarea cu `dict[cheie]`, iar `dict.get(cheie, default)` evita erorile.",
            "`.items()` iti da perechi cheie-valoare — ideal pentru iteratie completa.",
        ],
        "warmup_prompt": "Daca ai descrie un robot prin 3 atribute, care ar fi acelea?",
        "discussion_prompts": [
            "Ce avantaj are un dictionar fata de o lista?",
            "Cand ai folosi `.get()` in loc de `dict[cheie]`?",
            "Ce s-ar intampla daca ai avea doua chei identice intr-un dictionar?",
        ],
        "story_anchor": "Nova construieste un registru cu statusul fiecarui robot din echipa — nume, baterie, misiune. Un dictionar este alegerea perfecta.",
        "home_extension": 'Scrie un dictionar cu 3 lucruri despre tine: `{"nume": ..., "varsta": ..., "hobby": ...}`.',
        "collaboration_mode": "pairs",
        "content_tracks": ["Teorie clara", "Mini-provocare de cod"],
        "fun_fact": "In Python 3.7+ dictionarele isi pastreaza ordinea de inserare — inainte de asta, ordinea era aleatoare!",
        "hero_theme": "sunrise-lab",
        "hero_emoji": "📖",
        "objectives": [
            _objective(
                "Sa creez un dictionar cu chei si valori.",
                "Concept",
                'Pot scrie `{"cheie": valoare, ...}` cu 3 perechi.',
            ),
            _objective(
                "Sa accesez, modific si adaug valori.",
                "Practica",
                "Pot citi cu `dict[cheie]` si adauga perechi noi.",
            ),
            _objective(
                "Sa iterez peste un dictionar.",
                "Reflectie",
                "Pot explica diferenta dintre `.keys()`, `.values()`, `.items()`.",
            ),
        ],
        "practice": _practice(
            "Potriveste fiecare operatie cu ce face pe un dictionar `robot`.",
            "Trage operatia spre descrierea ei.",
            "Excelent! Dictionarele nu mai au secrete pentru tine.",
            [
                ("access", 'robot["nume"]'),
                ("get", 'robot.get("culoare", "?")'),
                ("update", 'robot["baterie"] = 100'),
                ("delete", 'del robot["activ"]'),
                ("items", "for k, v in robot.items():"),
                ("add", 'robot["misiune"] = "Marte"'),
            ],
            [
                ("Citeste valoarea pentru cheia `nume`.", "access"),
                ("Citeste valoarea cu o valoare implicita daca cheia lipseste.", "get"),
                ("Actualizeaza valoarea unei chei existente.", "update"),
                ("Sterge complet o pereche din dictionar.", "delete"),
                ("Parcurge toate perechile (cheie, valoare).", "items"),
                ("Adauga o cheie noua cu valoarea ei.", "add"),
            ],
        ),
        "tests": [
            _test(
                "Cum accesezi valoarea cheii `nume` din dictionarul `robot`?",
                'robot["nume"]',
                [
                    "robot.nume",
                    "robot(nume)",
                    "robot->nume",
                ],
                "Se foloseste sintaxa `dict[cheie]` cu paranteze patrate — cheia este un string in ghilimele.",
                "Scrie in gand cum ai accesa cheia `baterie` din acelasi dictionar.",
                "Python foloseste paranteze patrate pentru orice acces prin cheie sau index, fie el dictionar sau lista.",
            ),
            _test(
                'Ce returneaza `robot.get("culoare", "necunoscut")` daca cheia `culoare` nu exista?',
                '"necunoscut"',
                [
                    "None",
                    "O eroare KeyError",
                    "Un dictionar gol",
                ],
                "`.get()` cu un al doilea argument returneaza acea valoare daca cheia nu exista — evita exceptia.",
                'Cand ai prefera `.get()` in loc de `robot["culoare"]`?',
                "Al doilea argument este valoarea implicita — o plasa de siguranta pentru chei opționale.",
            ),
            _test(
                "Care metoda iti da pereche (cheie, valoare) cand iterezi?",
                ".items()",
                [".keys()", ".values()", ".pairs()"],
                "`.keys()` da doar cheile, `.values()` doar valorile, iar `.items()` da perechi (cheie, valoare).",
                "Cand ai folosi `.values()` in loc de `.items()`?",
                "`for k, v in dict.items():` este cel mai folosit pattern cand ai nevoie de ambele.",
            ),
        ],
        "reflections": _default_reflections(
            "Code 7 · Dictionare — perechi cheie-valoare",
            "Ce informatii din viata ta s-ar modela bine cu un dictionar?",
        ),
    },
    {
        "slug": "nivel-4-clase-si-obiecte",
        "legacy_slugs": [],
        "title": "Nivel 4 · Clase si obiecte",
        "date": date(2025, 11, 26),
        "age_bracket": "14-16",
        "difficulty": "advanced",
        "duration_minutes": 40,
        "xp_reward": 75,
        "excerpt": "Construiesti propriile tale tipuri de date cu `class` — primul pas spre programare orientata pe obiecte.",
        "theory_intro": "O CLASA este un sablon, iar un OBIECT este o instanta creata dupa acel sablon. Invatam sa modelam concepte reale in cod: roboti, conturi, carti.",
        "content": _content(
            "Definesti o clasa cu `class`: `class Robot:`. In interior pui metode, iar `__init__(self, ...)` este constructorul — ruleaza la crearea fiecarui obiect si seteaza atributele initiale.",
            'Exemplu:\n\n```\nclass Robot:\n    def __init__(self, nume, baterie):\n        self.nume = nume\n        self.baterie = baterie\n\n    def salut(self):\n        return f"Salut, sunt {self.nume}!"\n```\n\n`self` se refera la obiectul curent — il folosesti ca sa accesezi atributele sale.',
            'Creezi un obiect apeland clasa ca pe o functie: `r = Robot("Nova", 80)`. Acum `r.nume` e `"Nova"` si `r.salut()` returneaza `"Salut, sunt Nova!"`.',
            'Avantajul: poti crea oricate obiecte din aceeasi clasa, fiecare cu propriile sale atribute. `r1 = Robot("Zipp", 50)`, `r2 = Robot("Nova", 90)` — doua obiecte independente, dar cu aceleasi metode.',
        ),
        "theory_takeaways": [
            "O `class` este un sablon pentru obiecte; fiecare obiect are propriile atribute.",
            "`__init__(self, ...)` ruleaza la creare si seteaza starea initiala.",
            "`self` se refera la obiectul curent — obligatoriu ca prim parametru in metode.",
        ],
        "warmup_prompt": "Ce concept din jocul tau preferat ar fi o clasa? (personaj, arma, inventar?)",
        "discussion_prompts": [
            "De ce este util sa grupezi date si functii intr-o clasa?",
            "Ce s-ar intampla daca ai uita `self` intr-o metoda?",
            "Cand preferi o clasa in loc de un dictionar?",
        ],
        "story_anchor": "Echipa Nova trebuie sa gestioneze o flota de roboti. In loc de zeci de dictionare, o singura clasa `Robot` modeleaza totul elegant.",
        "home_extension": "Creeaza pe hartie o clasa pentru ceva din viata ta: `Carte`, `JocVideo` sau `AnimalDeCasa` — cu 2 atribute si o metoda.",
        "collaboration_mode": "pairs",
        "content_tracks": ["Teorie clara", "Mini-proiect OOP"],
        "fun_fact": "Conceptul de clase vine din 1967 (limbajul Simula). Python este unul dintre putinele limbaje majore unde OOP este optional — nu obligatoriu.",
        "hero_theme": "sunrise-lab",
        "hero_emoji": "🏗️",
        "objectives": [
            _objective(
                "Sa definesc o clasa cu `__init__` si metode.",
                "Concept",
                "Pot scrie o clasa cu 2 atribute si 1 metoda.",
            ),
            _objective(
                "Sa creez obiecte si sa le accesez atributele.",
                "Practica",
                "Pot crea 2 obiecte si apela metodele lor.",
            ),
            _objective(
                "Sa inteleg rolul lui `self`.",
                "Reflectie",
                "Pot explica de ce `self` apare in toate metodele.",
            ),
        ],
        "practice": _practice(
            "Potriveste fiecare element al unei clase cu rolul lui.",
            "Trage conceptul spre explicatia potrivita.",
            "Excelent! Ai deschis usa catre OOP.",
            [
                ("class-kw", "class Robot:"),
                ("init", "__init__(self, nume)"),
                ("self", "self.nume = nume"),
                ("method", "def salut(self):"),
                ("instantiate", 'r = Robot("Nova")'),
                ("access", "r.nume"),
            ],
            [
                ("Declara inceputul unei clase noi.", "class-kw"),
                ("Constructor — ruleaza la crearea fiecarui obiect.", "init"),
                ("Salveaza un atribut pe obiectul curent.", "self"),
                ("Metoda — functie care apartine clasei.", "method"),
                ("Creeaza un obiect nou (instantiere).", "instantiate"),
                ("Citeste un atribut dintr-un obiect.", "access"),
            ],
        ),
        "tests": [
            _test(
                "Ce face metoda `__init__` intr-o clasa?",
                "Initializeaza atributele unui obiect nou",
                [
                    "Sterge obiectul",
                    "Ruleaza doar cand apelezi explicit `init()`",
                    "Este optionala si ignorata de Python",
                ],
                "`__init__` este constructorul — se apeleaza automat la crearea obiectului si primeste argumentele trecute la instantiere.",
                "Ce s-ar intampla daca ai uita `__init__`?",
                "Constructorul este locul unde setezi starea initiala a fiecarui obiect nou.",
            ),
            _test(
                "La ce foloseste `self` in metodele unei clase?",
                "Se refera la obiectul curent pe care a fost apelata metoda",
                [
                    "Este un nume special pentru clasa",
                    "Se refera la ultimul obiect creat",
                    "Nu face nimic, e doar o conventie",
                ],
                "`self` este obligatoriu ca prim parametru — Python il completeaza automat cu obiectul pe care apelezi metoda.",
                "Cum accesezi `nume` in metoda `salut` daca e setat in `__init__`?",
                "`self.atribut` este modul standard prin care metodele acceseaza datele obiectului.",
            ),
            _test(
                "Cum creezi un obiect din clasa `Robot`?",
                'r = Robot("Nova", 80)',
                [
                    'r = new Robot("Nova", 80)',
                    'r = Robot:create("Nova", 80)',
                    'r = init Robot("Nova", 80)',
                ],
                "In Python, instantiezi apeland clasa direct, ca pe o functie. Nu exista cuvantul `new`.",
                "Imagineaza-ti o clasa `Carte` — cum ai crea un obiect al ei?",
                "Python pastreaza sintaxa curata — argumentele sunt cele din `__init__` (fara `self`).",
            ),
        ],
        "reflections": _default_reflections(
            "Nivel 4 · Clase si obiecte",
            "Ce alta clasa ai vrea sa construiesti si ce metode ar avea?",
        ),
    },
]


def _sync_related_content(lesson, blueprint, models):
    LessonObjective = models["LessonObjective"]
    LessonPractice = models["LessonPractice"]
    LessonReflectionPrompt = models["LessonReflectionPrompt"]
    Test = models["Test"]

    LessonObjective.objects.filter(lesson=lesson).delete()
    LessonObjective.objects.bulk_create(
        [
            LessonObjective(
                lesson=lesson,
                description=item["description"],
                focus_area=item["focus_area"],
                success_criteria=item["success_criteria"],
                order=index,
            )
            for index, item in enumerate(blueprint["objectives"])
        ]
    )

    Test.objects.filter(lesson=lesson).delete()
    Test.objects.bulk_create(
        [
            Test(
                lesson=lesson,
                question=item["question"],
                correct_answer=item["correct_answer"],
                wrong_answers=item["wrong_answers"],
                theory_summary=item["theory_summary"],
                practice_prompt=item["practice_prompt"],
                explanation=item["explanation"],
                difficulty=blueprint["difficulty"],
                points=100,
                time_limit_seconds=75,
                bonus_time_threshold=25,
            )
            for item in blueprint["tests"]
        ]
    )

    LessonReflectionPrompt.objects.filter(lesson=lesson).delete()
    LessonReflectionPrompt.objects.bulk_create(
        [
            LessonReflectionPrompt(
                lesson=lesson,
                prompt=item["prompt"],
                format=item["format"],
                order=index,
                scale_labels=item.get("scale_labels", []),
            )
            for index, item in enumerate(blueprint["reflections"])
        ]
    )

    practice_payload = blueprint["practice"]
    practice, _ = LessonPractice.objects.get_or_create(lesson=lesson)
    practice.intro = practice_payload["intro"]
    practice.instructions = practice_payload["instructions"]
    practice.success_message = practice_payload["success_message"]
    practice.data = practice_payload["data"]
    practice.save()


def seed_python_extras(apps, schema_editor):
    Subject = apps.get_model("estudy", "Subject")
    Lesson = apps.get_model("estudy", "Lesson")
    LessonObjective = apps.get_model("estudy", "LessonObjective")
    LessonPractice = apps.get_model("estudy", "LessonPractice")
    LessonReflectionPrompt = apps.get_model("estudy", "LessonReflectionPrompt")
    Test = apps.get_model("estudy", "Test")

    models = {
        "LessonObjective": LessonObjective,
        "LessonPractice": LessonPractice,
        "LessonReflectionPrompt": LessonReflectionPrompt,
        "Test": Test,
    }

    # The existing Python curriculum lives under the "Coding Quest" subject
    # (curated in migration 0047). Append to it rather than splitting the curriculum.
    subject = Subject.objects.filter(name="Coding Quest").order_by("id").first()
    if subject is None:
        # Defensive fallback — shouldn't happen post-0047.
        subject = Subject.objects.create(
            name="Coding Quest",
            slug="coding-quest",
            description="Calea de Python pentru elevi, cu poveste si misiuni.",
        )

    for blueprint in LESSON_BLUEPRINTS:
        lesson = Lesson.objects.filter(slug=blueprint["slug"]).first()
        if lesson is None:
            lesson = Lesson(subject=subject)

        lesson.subject = subject
        lesson.slug = blueprint["slug"]
        lesson.title = blueprint["title"]
        lesson.excerpt = blueprint["excerpt"]
        lesson.content = blueprint["content"]
        lesson.date = blueprint["date"]
        lesson.duration_minutes = blueprint["duration_minutes"]
        lesson.difficulty = blueprint["difficulty"]
        lesson.lesson_type = "standard"
        lesson.age_bracket = blueprint["age_bracket"]
        lesson.theory_intro = blueprint["theory_intro"]
        lesson.theory_takeaways = blueprint["theory_takeaways"]
        lesson.warmup_prompt = blueprint["warmup_prompt"]
        lesson.discussion_prompts = blueprint["discussion_prompts"]
        lesson.story_anchor = blueprint["story_anchor"]
        lesson.home_extension = blueprint["home_extension"]
        lesson.collaboration_mode = blueprint["collaboration_mode"]
        lesson.content_tracks = blueprint["content_tracks"]
        lesson.xp_reward = blueprint["xp_reward"]
        lesson.fun_fact = blueprint["fun_fact"]
        lesson.hero_theme = blueprint["hero_theme"]
        lesson.hero_emoji = blueprint["hero_emoji"]
        lesson.featured = False
        lesson.save()

        _sync_related_content(lesson, blueprint, models)


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0057_seed_math_for_coders"),
    ]

    operations = [
        migrations.RunPython(seed_python_extras, migrations.RunPython.noop),
    ]
