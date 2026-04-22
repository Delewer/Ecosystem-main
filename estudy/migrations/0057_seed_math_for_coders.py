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
        "slug": "junior-math-coordonate-pe-harta",
        "legacy_slugs": [],
        "title": "Junior Math · Coordonate pe harta",
        "date": date(2026, 4, 24),
        "age_bracket": "8-10",
        "difficulty": "beginner",
        "duration_minutes": 25,
        "xp_reward": 45,
        "excerpt": "Inveti sa gasesti un loc pe o harta folosind numere: inainte si sus.",
        "theory_intro": "O harta cu patratele are doua directii: stanga-dreapta (X) si jos-sus (Y). Cu doua numere, poti arata exact unde este ceva.",
        "content": _content(
            "Imagineaza-ti o tabla de sah. Fiecare patrat are o adresa formata din doua numere: primul spune cat mergi la dreapta, al doilea cat mergi in sus.",
            "Scriem coordonatele in paranteze: `(3, 2)` inseamna 3 patrate la dreapta, 2 patrate in sus. Punctul `(0, 0)` este coltul de start — se numeste ORIGINE.",
            "In jocurile pe calculator, toate personajele au coordonate. Cand personajul se muta, coordonatele lui se schimba: (3, 2) → (4, 2) cand merge un pas la dreapta.",
        ),
        "theory_takeaways": [
            "Coordonatele sunt doua numere: `(X, Y)`.",
            "X inseamna stanga-dreapta; Y inseamna jos-sus.",
            "Punctul `(0, 0)` este ORIGINEA — locul de pornire.",
        ],
        "warmup_prompt": "Daca ai fi intr-un parc cu un prieten, cum i-ai explica unde sa te gaseasca?",
        "discussion_prompts": [
            "Unde ai mai vazut coordonate? (jocuri, harti, batalia navala)",
            "De ce avem nevoie de DOUA numere si nu unul singur?",
            "Ce s-ar intampla daca am uita care numar e X si care e Y?",
        ],
        "story_anchor": "Robo vrea sa ajunga la o comoara ascunsa pe harta spatiului. Tu ii dai coordonatele corecte.",
        "home_extension": "Deseneaza o harta a camerei tale cu patratele si noteaza coordonatele pentru pat, masa si usa.",
        "collaboration_mode": "pairs",
        "content_tracks": ["Poveste ghidata", "Provocare bonus"],
        "fun_fact": "Sistemul de coordonate a fost inventat de Rene Descartes in 1637, uitandu-se la o musca pe tavan!",
        "hero_theme": "sunrise-lab",
        "hero_emoji": "🗺️",
        "objectives": [
            _objective(
                "Sa inteleg ce inseamna X si Y pe o harta.",
                "Concept",
                "Pot arata unde merge X si unde merge Y.",
            ),
            _objective(
                "Sa gasesc un punct dat prin coordonate.",
                "Practica",
                "Pot localiza `(3, 2)` pe o harta cu patratele.",
            ),
            _objective(
                "Sa scriu coordonatele unui obiect.",
                "Reflectie",
                "Pot spune coordonatele unui obiect cand il vad pe harta.",
            ),
        ],
        "practice": _practice(
            "Robo are 4 comori pe harta. Potriveste fiecare comoara cu coordonatele ei.",
            "Trage coordonatele spre locul potrivit pe harta.",
            "Super! Robo a gasit toate comorile.",
            [
                ("coord-00", "(0, 0)"),
                ("coord-30", "(3, 0)"),
                ("coord-02", "(0, 2)"),
                ("coord-33", "(3, 3)"),
            ],
            [
                ("Origine — coltul de start.", "coord-00"),
                ("3 patrate la dreapta, pe linia de jos.", "coord-30"),
                ("Pe marginea din stanga, 2 patrate in sus.", "coord-02"),
                ("3 la dreapta si 3 in sus — coltul opus originii.", "coord-33"),
            ],
        ),
        "tests": [
            _test(
                "Ce inseamna primul numar din `(5, 2)`?",
                "5 patrate la dreapta",
                [
                    "5 patrate in sus",
                    "Numarul comorii",
                    "Marimea hartii",
                ],
                "In `(X, Y)`, primul numar este X (stanga-dreapta), al doilea este Y (jos-sus).",
                "Daca ai `(5, 2)`, unde esti pe harta?",
                "Mereu citim coordonatele in ordinea X, Y — ca sa nu ne incurcam.",
            ),
            _test(
                "Care sunt coordonatele originii?",
                "(0, 0)",
                ["(1, 1)", "(10, 10)", "(0, 1)"],
                "Originea este locul de start — 0 la dreapta si 0 in sus.",
                "De unde incepe harta ta preferata de joc?",
                "`(0, 0)` este punctul de referinta fata de care masuram toate celelalte pozitii.",
            ),
        ],
        "reflections": _default_reflections(
            "Junior Math · Coordonate pe harta",
            "Ce ai alege sa plasezi la `(0, 0)` in harta ta: casa, o comoara, sau alt lucru?",
        ),
    },
    {
        "slug": "math-1-modulo-resturi-magice",
        "legacy_slugs": [],
        "title": "Math · Modulo — resturi magice",
        "date": date(2026, 4, 25),
        "age_bracket": "11-13",
        "difficulty": "intermediate",
        "duration_minutes": 30,
        "xp_reward": 55,
        "excerpt": "Descoperi operatorul `%` si vezi cum ajuta la cicluri, par/impar si ceasuri.",
        "theory_intro": "Modulo (`%`) este impartirea cu REST. In loc de cat, iti da cat a ramas. E una dintre cele mai folosite operatii in programare.",
        "content": _content(
            "`17 % 5` inseamna: „imparte 17 la 5 si da-mi restul”. 17 ÷ 5 = 3 rest 2, deci `17 % 5 == 2`. Restul este mereu mai mic decat impartitorul.",
            "Folosirea 1: PAR sau IMPAR. `n % 2 == 0` inseamna par, altfel e impar. Practic pe orice numar: `4 % 2 == 0` (par), `7 % 2 == 1` (impar).",
            "Folosirea 2: CICLURI. Vrei sa colorezi liniile tabelului alternat? `linie % 2` da 0 sau 1 — perfect pentru a alterna intre doua stiluri. Sau vrei sa faci ceva la fiecare a 10-a iteratie? `i % 10 == 0`.",
            "Folosirea 3: CEASUL. Dupa 23:00 vine 00:00, nu 24:00. Asta e modulo 24: `(ora + 5) % 24` iti da ora reala daca adaugi 5 ore.",
        ),
        "theory_takeaways": [
            "`a % b` returneaza restul impartirii `a / b`.",
            "`n % 2` este 0 pentru numere pare, 1 pentru impare.",
            "`i % n` creeaza un ciclu de la 0 la `n - 1` — util pentru alternante si ceas.",
        ],
        "warmup_prompt": "Daca azi este marti si trec 10 zile, in ce zi esti? Cum ai calcula?",
        "discussion_prompts": [
            "De ce este modulo perfect pentru a stabili daca un numar este par?",
            "Unde ai folosi modulo intr-un joc — un efect repetitiv, un timer?",
            "Ce s-ar intampla daca am face `n % 1`? De ce?",
        ],
        "story_anchor": "Statia spatiala ruleaza o animatie cu 6 cadre. Programul tau trebuie sa revina la cadrul 0 dupa ultimul — modulo este solutia.",
        "home_extension": "Calculeaza in minte: `50 % 7`, `100 % 10`, `23 % 5`. Verifica cu un calculator.",
        "collaboration_mode": "pairs",
        "content_tracks": ["Teorie clara", "Provocare cu cicluri"],
        "fun_fact": "Modulo e folosit in criptografie si hashing — este piesa de baza a multor algoritmi de securitate moderni.",
        "hero_theme": "sunrise-lab",
        "hero_emoji": "🔢",
        "objectives": [
            _objective(
                "Sa inteleg ce returneaza `a % b`.",
                "Concept",
                "Pot calcula rezultatul pentru numere mici.",
            ),
            _objective(
                "Sa folosesc modulo pentru par/impar.",
                "Practica",
                "Pot scrie o conditie care detecteaza numere pare.",
            ),
            _objective(
                "Sa recunosc ciclurile create de modulo.",
                "Reflectie",
                "Pot explica cum `i % 7` creeaza un ciclu de 7 zile.",
            ),
        ],
        "practice": _practice(
            "Potriveste fiecare expresie modulo cu rezultatul ei.",
            "Trage expresia spre rezultatul corect.",
            "Perfect! Stapanesti restul impartirii.",
            [
                ("mod-10-3", "10 % 3"),
                ("mod-8-2", "8 % 2"),
                ("mod-7-2", "7 % 2"),
                ("mod-25-5", "25 % 5"),
                ("mod-23-24", "23 % 24"),
                ("mod-5-10", "5 % 10"),
            ],
            [
                ("Rezultat: 1 (10 = 3*3 + 1).", "mod-10-3"),
                ("Rezultat: 0 (8 e par, imparte fix la 2).", "mod-8-2"),
                ("Rezultat: 1 (7 e impar).", "mod-7-2"),
                ("Rezultat: 0 (25 imparte exact la 5).", "mod-25-5"),
                (
                    "Rezultat: 23 (restul e tot numarul, pentru ca 23 < 24).",
                    "mod-23-24",
                ),
                ("Rezultat: 5 (restul e tot numarul, pentru ca 5 < 10).", "mod-5-10"),
            ],
        ),
        "tests": [
            _test(
                "Cat face `14 % 5`?",
                "4",
                ["2", "3", "0"],
                "14 ÷ 5 = 2 rest 4, deci `14 % 5 == 4`.",
                "Imparte 14 la 5 pe hartie si noteaza restul.",
                "Modulo returneaza intotdeauna restul, indiferent cat de mare este catul.",
            ),
            _test(
                "Ce conditie detecteaza daca `n` este par?",
                "n % 2 == 0",
                [
                    "n % 2 == 1",
                    "n / 2 == 0",
                    "n == 2",
                ],
                "Numerele pare se impart exact la 2 — deci restul este 0.",
                "Gandeste-te la 4, 6, 8 — ce rest dau la impartirea cu 2?",
                "`n % 2` produce 0 pentru pare si 1 pentru impare — pattern-ul standard pentru verificare.",
            ),
            _test(
                "La ce foloseste `i % n` intr-un ciclu?",
                "Creeaza o secventa ciclica de la 0 la n-1",
                [
                    "Opreste ciclul dupa n pasi",
                    "Face ciclul sa mearga invers",
                    "Sareste pasii fara sens",
                ],
                "`i % n` face ca valoarea sa se reseteze la 0 cand ajunge la n, creand un ciclu previzibil.",
                "Imagineaza-ti un ceas care revine la 12 dupa 11 — cum ai scrie asta cu modulo?",
                "Este tehnica de baza pentru animatii, zile ale saptamanii, culori alternante si multe altele.",
            ),
        ],
        "reflections": _default_reflections(
            "Math · Modulo — resturi magice",
            "Unde intr-un joc sau aplicatie ai putea folosi modulo?",
        ),
    },
    {
        "slug": "math-2-logica-adevarat-fals",
        "legacy_slugs": [],
        "title": "Math · Logica: AND, OR, NOT",
        "date": date(2026, 4, 26),
        "age_bracket": "11-13",
        "difficulty": "intermediate",
        "duration_minutes": 30,
        "xp_reward": 55,
        "excerpt": "Combini conditii adevarate si false ca sa iei decizii inteligente in cod.",
        "theory_intro": "Logica booleana este limbajul deciziilor. Doar doua valori — TRUE si FALSE — combinate prin AND, OR si NOT, deschid toate conditiile din programare.",
        "content": _content(
            "O expresie booleana este o intrebare cu raspuns da sau nu: „`varsta >= 10`” este TRUE sau FALSE in functie de valoarea varstei. Programele iau decizii bazate pe astfel de expresii.",
            "`AND` (si) este TRUE doar cand AMBELE parti sunt TRUE. `are_cheie AND este_zi` — ai acces doar daca ai cheia SI e zi.",
            "`OR` (sau) este TRUE cand CEL PUTIN UNA dintre parti este TRUE. `are_cheie OR este_ziua_ta` — intri daca ai cheia SAU daca este ziua ta.",
            "`NOT` (negatie) inverseaza valoarea. `NOT plouat` este TRUE cand nu a plouat. Utila pentru a exprima opusul unei conditii.",
            "Tabelele de adevar sumarizeaza toate combinatiile: `TRUE AND TRUE = TRUE`, `TRUE AND FALSE = FALSE`, `FALSE OR TRUE = TRUE`, `NOT TRUE = FALSE` si asa mai departe.",
        ),
        "theory_takeaways": [
            "O expresie booleana are doar doua valori: TRUE sau FALSE.",
            "`AND` cere ambele parti TRUE; `OR` cere cel putin una TRUE.",
            "`NOT` inverseaza: TRUE devine FALSE si invers.",
        ],
        "warmup_prompt": "Cand spui „ies afara daca e soare si nu plouat”, cate conditii trebuie sa fie adevarate?",
        "discussion_prompts": [
            "Care e diferenta practica intre `AND` si `OR` cand stabilesti o regula?",
            "Cand ai folosi `NOT` in loc de a scrie o conditie opusa direct?",
            "Poti combina AND, OR si NOT intr-o singura expresie? Da un exemplu.",
        ],
        "story_anchor": "Robo pazeste usa de la bucataria statiei. Trebuie sa decida cine intra, pe baza unor reguli combinate.",
        "home_extension": "Scrie 3 reguli din viata ta folosind AND, OR si NOT — de exemplu: „pot juca jocuri daca am terminat tema SI nu e ora culcarii”.",
        "collaboration_mode": "pairs",
        "content_tracks": ["Teorie clara", "Provocare cu tabele de adevar"],
        "fun_fact": "Logica booleana a fost inventata de George Boole in 1847 si sta la baza tuturor circuitelor digitale moderne.",
        "hero_theme": "sunrise-lab",
        "hero_emoji": "🔀",
        "objectives": [
            _objective(
                "Sa inteleg valorile TRUE si FALSE.",
                "Concept",
                "Pot da exemple de expresii booleane din viata reala.",
            ),
            _objective(
                "Sa combin expresii cu AND, OR si NOT.",
                "Practica",
                "Pot calcula rezultatul pentru combinatii simple.",
            ),
            _objective(
                "Sa citesc un tabel de adevar.",
                "Reflectie",
                "Pot explica de ce `AND` e TRUE doar intr-un caz din patru.",
            ),
        ],
        "practice": _practice(
            "Potriveste fiecare expresie booleana cu rezultatul ei.",
            "Trage expresia spre rezultatul corect (TRUE sau FALSE).",
            "Excelent! Ai stapanit logica booleana.",
            [
                ("and-tt", "TRUE AND TRUE"),
                ("and-tf", "TRUE AND FALSE"),
                ("or-ff", "FALSE OR FALSE"),
                ("or-tf", "TRUE OR FALSE"),
                ("not-t", "NOT TRUE"),
                ("not-f", "NOT FALSE"),
            ],
            [
                ("Este TRUE (ambele parti TRUE).", "and-tt"),
                ("Este FALSE (o parte e FALSE, AND cere ambele).", "and-tf"),
                ("Este FALSE (niciuna nu e TRUE).", "or-ff"),
                ("Este TRUE (cel putin una e TRUE).", "or-tf"),
                ("Este FALSE (NOT inverseaza TRUE).", "not-t"),
                ("Este TRUE (NOT inverseaza FALSE).", "not-f"),
            ],
        ),
        "tests": [
            _test(
                "Care e rezultatul expresiei `TRUE AND FALSE`?",
                "FALSE",
                ["TRUE", "Uneori TRUE", "Depinde de ordine"],
                "`AND` cere AMBELE parti sa fie TRUE. Daca una e FALSE, rezultatul e FALSE.",
                "Gandeste-te: „am bilet SI am ora valida” — daca biletul e expirat, intri?",
                "`AND` e strict — toate conditiile trebuie sa fie adevarate simultan.",
            ),
            _test(
                "Cand este `A OR B` adevarat?",
                "Cand cel putin una dintre A sau B este TRUE",
                [
                    "Doar cand ambele sunt TRUE",
                    "Doar cand ambele sunt FALSE",
                    "Niciodata",
                ],
                "`OR` este TRUE in 3 cazuri din 4 — doar cand ambele sunt FALSE rezultatul e FALSE.",
                "„Merg la magazin daca am bani SAU iau card” — cand pot merge?",
                "`OR` e mai permisiv decat `AND` — o singura parte TRUE e suficienta.",
            ),
            _test(
                "Cat face `NOT (FALSE OR TRUE)`?",
                "FALSE",
                ["TRUE", "Eroare", "Depinde"],
                "Mai intai evaluezi parantezele: `FALSE OR TRUE = TRUE`. Apoi `NOT TRUE = FALSE`.",
                "Calculeaza mai intai paranteza, apoi aplica NOT.",
                "Ordinea conteaza: parantezele se evalueaza inaintea operatorilor din afara lor.",
            ),
        ],
        "reflections": _default_reflections(
            "Math · Logica: AND, OR, NOT",
            "Ce regula din viata ta ai scrie cu AND, OR sau NOT?",
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


def seed_math_for_coders(apps, schema_editor):
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

    # Backfill slug for "Bazele Web" (seeded in 0055 without explicit slug).
    web_basics = Subject.objects.filter(name="Bazele Web", slug="").first()
    if web_basics is not None:
        web_basics.slug = "bazele-web"
        web_basics.save(update_fields=["slug"])

    subject_name = "Matematica pentru coderi"
    subject_slug = "matematica-pentru-coderi"
    subject_description = "Matematica utila in cod: coordonate, modulo si logica booleana — pentru toate varstele."
    subject = Subject.objects.filter(name=subject_name).order_by("id").first()
    if subject is None:
        subject = Subject.objects.create(
            name=subject_name, slug=subject_slug, description=subject_description
        )
    else:
        if not subject.slug:
            subject.slug = subject_slug
        subject.description = subject_description
        subject.save(update_fields=["slug", "description"])

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
        ("estudy", "0056_seed_web_basics_extras"),
    ]

    operations = [
        migrations.RunPython(seed_math_for_coders, migrations.RunPython.noop),
    ]
