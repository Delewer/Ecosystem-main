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
        "slug": "junior-web-poze-si-linkuri",
        "legacy_slugs": [],
        "title": "Junior Web · Poze si linkuri",
        "date": date(2026, 4, 22),
        "age_bracket": "8-10",
        "difficulty": "beginner",
        "duration_minutes": 25,
        "xp_reward": 45,
        "excerpt": "Pui o poza pe pagina ta si adaugi un link prieten spre alt site.",
        "theory_intro": "O pagina prinde viata cand adaugi poze si linkuri. Pozele te ajuta sa arati, iar linkurile te duc in alte locuri.",
        "content": _content(
            "Ca sa pui o poza pe pagina, folosesti eticheta `<img>`. Ea are doua piese importante: `src` spune browserului unde e poza, iar `alt` spune ce se vede in poza — foarte util cand poza nu se incarca.",
            'Un link se face cu `<a href="adresa">text</a>`. Apeasa pe text si ajungi la adresa. Linkurile sunt de obicei subliniate ca sa le vezi usor.',
            "Poti chiar sa pui o poza intr-un link! Astfel, cand apesi pe poza, ea te duce in alta parte — ca un buton cu imagine.",
        ),
        "theory_takeaways": [
            '`<img src="..." alt="...">` pune o poza pe pagina.',
            "`alt` descrie poza cand ea nu se incarca.",
            '`<a href="...">` creeaza un link catre alta pagina.',
        ],
        "warmup_prompt": "Daca pagina ta ar avea o singura poza, ce ai pune in ea?",
        "discussion_prompts": [
            "Unde ai vazut linkuri intr-o pagina web?",
            "De ce crezi ca pozele au nevoie de o descriere (alt)?",
            "Ce s-ar intampla daca n-ar exista linkuri intre pagini?",
        ],
        "story_anchor": "Robo vrea sa puna poza robotului sau preferat si un link spre biblioteca de robotei.",
        "home_extension": "Deseneaza pe hartie cum ar arata o pagina cu o poza sus si un link dedesubt.",
        "collaboration_mode": "pairs",
        "content_tracks": ["Poveste ghidata", "Provocare bonus"],
        "fun_fact": "Prima poza de pe web a fost pusa in 1992 si arata o trupa de la CERN.",
        "hero_theme": "sunrise-lab",
        "hero_emoji": "🖼️",
        "objectives": [
            _objective(
                "Sa adaug o poza folosind eticheta `<img>`.",
                "Concept",
                "Stiu ca `src` este adresa pozei si `alt` este descrierea.",
            ),
            _objective(
                "Sa fac un link cu eticheta `<a>`.",
                "Practica",
                'Pot scrie `<a href="...">Apasa aici</a>`.',
            ),
            _objective(
                "Sa combin text, poza si link pe aceeasi pagina.",
                "Reflectie",
                "Pot spune ce face fiecare piesa.",
            ),
        ],
        "practice": _practice(
            "Robo amesteca piesele. Ajuta-l sa le puna la locul lor.",
            "Trage fiecare piesa spre descrierea ei.",
            "Bravo! Pagina lui Robo are acum poze si linkuri.",
            [
                ("img-src", 'src="robo.png"'),
                ("img-alt", 'alt="Robot vesel"'),
                ("a-href", 'href="biblioteca.html"'),
                ("a-text", "Apasa aici"),
            ],
            [
                ("Adresa pozei — spune unde e fisierul.", "img-src"),
                ("Descrierea pozei — pentru cand poza nu se incarca.", "img-alt"),
                ("Adresa linkului — spune unde te duce.", "a-href"),
                ("Textul vizibil al linkului — pe ce apesi.", "a-text"),
            ],
        ),
        "tests": [
            _test(
                "Care eticheta pune o poza pe pagina?",
                "<img>",
                ["<pic>", "<photo>", "<a>"],
                "Pozele se adauga cu `<img>`; `<a>` este pentru linkuri.",
                "Imagineaza-ti o pagina cu poza animalului tau preferat — ce eticheta folosesti?",
                "Browserul stie sa deseneze poze doar cand intalneste eticheta `<img>` cu un `src`.",
            ),
            _test(
                "Ce rol are atributul `alt` la o poza?",
                "Descrie poza cand nu se poate afisa",
                [
                    "Coloreaza poza in alb-negru",
                    "Face poza mai mare",
                    "Schimba pozitia pozei",
                ],
                "`alt` este o descriere scurta a pozei — se vede cand poza nu se incarca si ajuta cititoarele de ecran.",
                "Cum ai descrie in 3 cuvinte poza ta preferata?",
                "`alt` face pagina mai prietenoasa si accesibila pentru toata lumea.",
            ),
        ],
        "reflections": _default_reflections(
            "Junior Web · Poze si linkuri",
            "Ce poza si ce link ai pune primele pe pagina ta?",
        ),
    },
    {
        "slug": "web-3-flexbox-layout",
        "legacy_slugs": [],
        "title": "Web 3 · Layout cu Flexbox",
        "date": date(2026, 4, 23),
        "age_bracket": "11-13",
        "difficulty": "intermediate",
        "duration_minutes": 35,
        "xp_reward": 65,
        "excerpt": "Asezi cutii una langa alta, le centrezi si le distribui cu Flexbox — primul tau sistem de layout.",
        "theory_intro": "Flexbox este un sistem CSS care aranjeaza cutii intr-un rand sau o coloana. Cu cateva reguli pe parinte, copiii se aliniaza si se distribuie automat.",
        "content": _content(
            "Pentru a activa Flexbox, pui `display: flex;` pe elementul parinte. Imediat, toti copiii se aseaza pe un rand orizontal, unul langa altul.",
            "Doua proprietati fac magia: `justify-content` controleaza alinierea pe axa principala (orizontala by default) — valori utile: `flex-start`, `center`, `space-between`. `align-items` controleaza axa perpendiculara — `center` aliniaza vertical continutul.",
            "Cu `flex-direction: column` schimbi axa principala pe verticala. Asta transforma flexbox-ul dintr-un rand de cutii intr-o coloana — util pentru meniuri sau liste verticale.",
            "`gap` este cel mai curat mod de a adauga spatiu intre elemente — in loc sa pui `margin` pe fiecare copil, pui `gap: 16px` pe parinte si toti primesc spatiu egal.",
        ),
        "theory_takeaways": [
            "`display: flex` transforma elementul intr-un container flex.",
            "`justify-content` aliniaza pe axa principala; `align-items` pe cea perpendiculara.",
            "`flex-direction: column` schimba axa principala pe verticala.",
            "`gap` creeaza spatiu egal intre copii.",
        ],
        "warmup_prompt": "Cum ai aseza 3 carduri pe o pagina: pe rand, in coloana sau in grila?",
        "discussion_prompts": [
            "Cand folosesti `space-between` si cand `center`?",
            "Ce avantaje are `gap` fata de `margin` la fiecare copil?",
            "Cand ai schimba `flex-direction` pe `column` in loc de `row`?",
        ],
        "story_anchor": "Nova construieste un panou de control pentru statia spatiala — butoanele trebuie aliniate perfect pe rand si apoi in coloana pe mobil.",
        "home_extension": "Deseneaza pe hartie trei layout-uri: un rand de butoane, o coloana de carduri, un header cu logo stanga si meniu dreapta.",
        "collaboration_mode": "pairs",
        "content_tracks": ["Teorie clara", "Provocare de layout"],
        "fun_fact": "Flexbox a devenit standard CSS oficial in 2017, dupa aproape 10 ani de propuneri si rafinari.",
        "hero_theme": "sunrise-lab",
        "hero_emoji": "📐",
        "objectives": [
            _objective(
                "Sa inteleg ce face `display: flex`.",
                "Concept",
                "Pot explica ce se intampla cand pun `display: flex` pe un parinte.",
            ),
            _objective(
                "Sa aliniez elemente cu `justify-content` si `align-items`.",
                "Practica",
                "Pot centra trei cutii pe orizontala si pe verticala.",
            ),
            _objective(
                "Sa schimb axa cu `flex-direction`.",
                "Reflectie",
                "Pot transforma un rand intr-o coloana cu o singura linie.",
            ),
        ],
        "practice": _practice(
            "Potriveste fiecare proprietate Flexbox cu efectul ei.",
            "Trage proprietatea corecta spre descrierea potrivita.",
            "Excelent! Acum poti aranja orice pagina cu Flexbox.",
            [
                ("display-flex", "display: flex"),
                ("justify-content", "justify-content: center"),
                ("align-items", "align-items: center"),
                ("flex-direction", "flex-direction: column"),
                ("gap", "gap: 16px"),
                ("space-between", "justify-content: space-between"),
            ],
            [
                (
                    "Transforma elementul intr-un container flex — copiii se aseaza pe rand.",
                    "display-flex",
                ),
                (
                    "Centreaza copiii pe axa principala (orizontala by default).",
                    "justify-content",
                ),
                (
                    "Centreaza copiii pe axa perpendiculara (verticala by default).",
                    "align-items",
                ),
                (
                    "Schimba axa principala pe verticala — copiii se pun unul sub altul.",
                    "flex-direction",
                ),
                ("Adauga spatiu egal intre toti copiii.", "gap"),
                (
                    "Impinge primul copil la stanga si ultimul la dreapta, restul la mijloc.",
                    "space-between",
                ),
            ],
        ),
        "tests": [
            _test(
                "Ce face `display: flex` pus pe un element parinte?",
                "Aseaza copiii pe un rand, controlabil cu proprietati flex",
                [
                    "Face elementul invizibil",
                    "Centreaza automat pagina intreaga",
                    "Aplica un border in jurul elementului",
                ],
                "`display: flex` activeaza Flexbox pe container — copiii devin `flex items` si pot fi aliniati cu `justify-content` si `align-items`.",
                "Ce s-ar schimba daca ai pune `display: flex` pe un `<nav>` cu trei linkuri?",
                "Fara `display: flex`, copiii raman blocuri verticale standard; cu el, devin un rand controlabil.",
            ),
            _test(
                "Cum centrezi vertical un card intr-un container flex?",
                "`align-items: center`",
                [
                    "`justify-content: center`",
                    "`text-align: center`",
                    "`vertical-align: middle`",
                ],
                "`align-items` controleaza axa perpendiculara; cand `flex-direction` este `row` (default), ea este verticala.",
                "Cum centrezi atat pe orizontala cat si pe verticala?",
                "Pentru centrare completa: `justify-content: center` + `align-items: center`.",
            ),
            _test(
                "Ce valoare a `justify-content` pune logo la stanga si meniu la dreapta?",
                "space-between",
                [
                    "center",
                    "flex-start",
                    "stretch",
                ],
                "`space-between` distribuie copiii astfel incat primul este lipit de inceput, ultimul de sfarsit, iar spatiile raman egale intre ei.",
                "Gandeste-te la header-ul unui site — logo stanga, butoane dreapta. Ce proprietate folosesti?",
                "`space-between` e perfecta pentru bare de navigatie cu doua grupuri de elemente.",
            ),
        ],
        "reflections": _default_reflections(
            "Web 3 · Layout cu Flexbox",
            "Ce pagina ti-ar fi mai usor de facut acum, cu Flexbox, decat inainte?",
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


def seed_web_basics_extras(apps, schema_editor):
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

    subject = Subject.objects.filter(name="Bazele Web").order_by("id").first()
    if subject is None:
        subject = Subject.objects.create(
            name="Bazele Web",
            description="Construieste pagini web cu HTML si CSS — traseu vizual pentru 8-10 ani si cod real pentru 11+.",
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
        ("estudy", "0055_seed_web_basics_lessons"),
    ]

    operations = [
        migrations.RunPython(seed_web_basics_extras, migrations.RunPython.noop),
    ]
