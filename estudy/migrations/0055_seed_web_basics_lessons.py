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
        "slug": "junior-web-pagina-ta-colorata",
        "legacy_slugs": [],
        "title": "Junior Web · Pagina ta colorata",
        "date": date(2026, 4, 19),
        "age_bracket": "8-10",
        "difficulty": "beginner",
        "duration_minutes": 25,
        "xp_reward": 40,
        "excerpt": "Creezi prima ta pagina web cu un titlu mare, un mesaj si o culoare preferata.",
        "theory_intro": "O pagina web este ca un desen cu etichete. HTML pune piesele la locul lor, iar culorile le adaugam cu putina magie.",
        "content": _content(
            "O pagina web este facuta din piese mici numite etichete. Fiecare eticheta are un rol: una este pentru titluri, alta este pentru text, iar alta pune o imagine.",
            "Etichetele se scriu intre paranteze ascutite: `<h1>Salut!</h1>`. Ce este intre paranteza de deschidere si cea de inchidere apare pe pagina ta.",
            'Daca vrei sa colorezi un titlu, adaugi un mic stil: `<h1 style="color:purple">Salut!</h1>`. Acum titlul tau este violet, exact cum ti l-ai imaginat.',
        ),
        "theory_takeaways": [
            "Etichetele HTML spun pagina ce sa arate.",
            "Titlurile mari se scriu cu `<h1>`.",
            'Culorile se adauga cu `style="color:..."`.',
        ],
        "warmup_prompt": "Daca ai avea o pagina doar a ta, ce culoare ai alege pentru titlu?",
        "discussion_prompts": [
            "Unde ai vazut titluri mari si litere mici pe aceeasi pagina?",
            "De ce crezi ca etichetele au un inceput si un sfarsit?",
            "Ce ai schimba pe pagina preferata de tine daca ai putea?",
        ],
        "story_anchor": "Robo face prima lui pagina personala si are nevoie de tine sa-i alegi titlul si culoarea.",
        "home_extension": "Arata acasa ce ai vrea sa scrii pe prima ta pagina: un titlu, doua randuri despre tine si o culoare preferata.",
        "collaboration_mode": "pairs",
        "content_tracks": ["Poveste ghidata", "Provocare bonus"],
        "fun_fact": "Prima pagina web a fost creata in 1991 si avea doar text alb pe fond gri.",
        "hero_theme": "sunrise-lab",
        "hero_emoji": "🎨",
        "objectives": [
            _objective(
                "Sa recunosc etichete simple de HTML.",
                "Concept",
                "Pot arata eticheta unui titlu si eticheta unui paragraf.",
            ),
            _objective(
                "Sa pun un titlu si un mesaj pe pagina.",
                "Practica",
                "Pot scrie `<h1>` si `<p>` cu mesajele mele.",
            ),
            _objective(
                "Sa schimb culoarea textului cu un mic stil.",
                "Reflectie",
                "Pot spune ce culoare alegem si de ce.",
            ),
        ],
        "practice": _practice(
            "Robo are etichetele amestecate. Potriveste fiecare piesa cu rolul ei.",
            "Trage cartonasul spre explicatia potrivita ca sa completezi pagina lui Robo.",
            "Super! Pagina lui Robo arata grozav acum.",
            [
                ("tag-h1", "<h1>"),
                ("tag-p", "<p>"),
                ("tag-a", '<a href="...">'),
                ("style-color", 'style="color:red"'),
            ],
            [
                ("Eticheta pentru un titlu mare.", "tag-h1"),
                ("Eticheta pentru un paragraf de text.", "tag-p"),
                ("Eticheta pentru o legatura (link) spre alta pagina.", "tag-a"),
                ("Instructiunea care coloreaza textul in rosu.", "style-color"),
            ],
        ),
        "tests": [
            _test(
                "Care eticheta face un titlu mare pe pagina?",
                "<h1>",
                ["<p>", "<a>", "<div>"],
                "Titlurile mari se scriu cu eticheta `<h1>`; celelalte sunt pentru paragraf sau link.",
                "Imagineaza-ti un poster cu numele tau — ce eticheta ai folosi?",
                "Eticheta `<h1>` ii spune browserului ca textul este cel mai important titlu.",
            ),
            _test(
                "Cum schimbi culoarea textului dintr-un titlu?",
                'Adaugi `style="color:..."` la eticheta',
                [
                    "Schimbi numele etichetei in `<color>`",
                    "Scrii titlul cu litere mari",
                    "Pui un punct la sfarsitul titlului",
                ],
                "Stilurile mici se adauga direct in eticheta cu atributul `style`.",
                "Ce culoare ai folosi pentru un titlu vesel?",
                '`style="color:..."` spune browserului ce culoare sa desenze pentru textul din acea eticheta.',
            ),
        ],
        "reflections": _default_reflections(
            "Junior Web · Pagina ta colorata",
            "Ce titlu si ce culoare ai pune pe pagina ta daca o creezi acum?",
        ),
    },
    {
        "slug": "web-1-prima-pagina-html",
        "legacy_slugs": [],
        "title": "Web 1 · Prima pagina HTML",
        "date": date(2026, 4, 20),
        "age_bracket": "11-13",
        "difficulty": "beginner",
        "duration_minutes": 30,
        "xp_reward": 50,
        "excerpt": "Construiesti scheletul unei pagini web folosind etichete HTML clare si bine ordonate.",
        "theory_intro": "HTML este limbajul care structureaza o pagina. Browserul citeste etichetele si transforma codul tau intr-o pagina vizibila.",
        "content": _content(
            "Fiecare pagina HTML porneste de la un schelet: `<!DOCTYPE html>`, apoi `<html>`, cu `<head>` si `<body>` inauntru. Head-ul contine informatii despre pagina, iar body-ul contine ce vede utilizatorul.",
            'In body folosesti etichete ca `<h1>` pentru titlu, `<p>` pentru paragraf si `<a href="...">` pentru legaturi. Fiecare eticheta are o deschidere si o inchidere, iar continutul este cuprins intre ele.',
            "Structura curata conteaza: titluri ierarhizate (`<h1>` → `<h2>`), paragrafe scurte si linkuri clare fac pagina usor de citit atat pentru oameni, cat si pentru motoarele de cautare.",
        ),
        "theory_takeaways": [
            "O pagina HTML are mereu `<html>`, `<head>` si `<body>`.",
            "Titlurile merg de la `<h1>` (cel mai mare) la `<h6>`.",
            'Linkurile se fac cu `<a href="adresa">...</a>`.',
        ],
        "warmup_prompt": "Daca ar trebui sa descrii pagina ta preferata in 3 sectiuni, care ar fi ele?",
        "discussion_prompts": [
            "De ce crezi ca o pagina are nevoie de un `<head>` separat de `<body>`?",
            "Cand este util sa folosesti mai multe niveluri de titluri?",
            "Cum ajuta linkurile un utilizator sa navigheze?",
        ],
        "story_anchor": "Nova construieste site-ul echipei de roboti si are nevoie de o pagina de prezentare bine structurata.",
        "home_extension": "Schiteaza pe hartie planul unei pagini personale: titlu, doua paragrafe, un link si o imagine.",
        "collaboration_mode": "pairs",
        "content_tracks": ["Teorie clara", "Mini-provocare de constructie"],
        "fun_fact": "HTML inseamna HyperText Markup Language si a fost inventat de Tim Berners-Lee in 1991.",
        "hero_theme": "sunrise-lab",
        "hero_emoji": "🌐",
        "objectives": [
            _objective(
                "Sa cunosc scheletul unei pagini HTML.",
                "Concept",
                "Pot spune ce face `<head>` si ce face `<body>`.",
            ),
            _objective(
                "Sa folosesc etichete pentru titluri, paragrafe si linkuri.",
                "Practica",
                'Pot scrie corect `<h1>`, `<p>` si `<a href="...">`.',
            ),
            _objective(
                "Sa structurez ierarhic o pagina scurta.",
                "Reflectie",
                "Pot explica de ce un titlu principal este `<h1>` si nu `<h3>`.",
            ),
        ],
        "practice": _practice(
            "Potriveste fiecare eticheta HTML cu ce face pe pagina.",
            "Trage eticheta corecta spre explicatia ei.",
            "Excelent! Acum cunosti piesele scheletului unei pagini.",
            [
                ("doctype", "<!DOCTYPE html>"),
                ("html-root", "<html>...</html>"),
                ("head", "<head>"),
                ("body", "<body>"),
                ("h1", "<h1>"),
                ("link", '<a href="...">'),
            ],
            [
                (
                    "Linia care spune browserului ca e un document HTML modern.",
                    "doctype",
                ),
                ("Radacina intregii pagini.", "html-root"),
                ("Contine informatii despre pagina (titlu, meta, stiluri).", "head"),
                ("Contine tot ce vede utilizatorul.", "body"),
                ("Cel mai important titlu al paginii.", "h1"),
                ("Creeaza o legatura spre alta pagina.", "link"),
            ],
        ),
        "tests": [
            _test(
                "Care este eticheta corecta pentru un hyperlink?",
                "<a>",
                ["<link>", "<href>", "<nav>"],
                'Linkurile se fac cu `<a href="...">` — `<link>` este o eticheta din `<head>` pentru fisiere externe.',
                "Scrie in gand cum arata un link catre pagina de ajutor.",
                "Eticheta `<a>` (anchor) contine atributul `href` cu adresa destinatiei.",
            ),
            _test(
                "Ce rol are eticheta `<head>`?",
                "Contine metadate despre pagina, nu continutul vizibil",
                [
                    "Afiseaza antetul paginii in partea de sus",
                    "Contine toate paragrafele paginii",
                    "Este ignorata de browser",
                ],
                "`<head>` tine titlul paginii, iconita, stilurile si metainformatii — nu se afiseaza direct in pagina.",
                "Ce ai pune in `<head>` daca ai crea o pagina personala?",
                "Browserul citeste `<head>` pentru a sti cum sa afiseze pagina, dar afiseaza doar continutul din `<body>`.",
            ),
        ],
        "reflections": _default_reflections(
            "Web 1 · Prima pagina HTML",
            "Ce pagina ai construi tu mai intai: portofoliu, blog de joc sau retetar? De ce?",
        ),
    },
    {
        "slug": "web-2-stiluri-cu-css",
        "legacy_slugs": [],
        "title": "Web 2 · Stiluri cu CSS",
        "date": date(2026, 4, 21),
        "age_bracket": "11-13",
        "difficulty": "beginner",
        "duration_minutes": 30,
        "xp_reward": 55,
        "excerpt": "Inveti cum sa pictezi si sa aranjezi pagina folosind selectori si proprietati CSS.",
        "theory_intro": "CSS (Cascading Style Sheets) este haina paginii tale. Cu selectori tintesti elemente, iar cu proprietati le schimbi culoarea, marimea si spatiul.",
        "content": _content(
            "Un stil CSS are trei piese: un selector (ce tintesc), o proprietate (ce schimb) si o valoare (cum il schimb). Exemplu: `h1 { color: purple; }` schimba culoarea titlurilor in violet.",
            "Selectorii cei mai folositi sunt numele etichetei (`h1`), clasele (`.buton`) si identificatorii (`#hero`). Clasele sunt cele mai flexibile — le poti pune pe mai multe elemente.",
            "Spatiul se controleaza prin `margin` (in afara) si `padding` (in interior). Impreuna cu `border`, ele formeaza modelul de cutie — fiecare element este o cutie dreptunghiulara cu straturi.",
        ),
        "theory_takeaways": [
            "Un stil CSS tinteste elemente cu un selector.",
            "Clasele (`.nume`) sunt reutilizabile pe mai multe elemente.",
            "`margin` = spatiu afara, `padding` = spatiu inauntru.",
        ],
        "warmup_prompt": "Daca ai avea o singura proprietate CSS sa o folosesti peste tot, care ar fi si de ce?",
        "discussion_prompts": [
            "Cand alegi o clasa in loc de a scrie stilul pe fiecare element?",
            "Ce s-ar intampla daca toate titlurile ar fi la fel de mari?",
            "De ce crezi ca avem si `margin` si `padding`?",
        ],
        "story_anchor": "Echipa Nova vrea ca pagina de misiune sa arate modern — tu alegi culorile si spatiile.",
        "home_extension": "Descrie in cuvinte cum ai stiliza pagina ta: culoare de titlu, fundal, marime text.",
        "collaboration_mode": "pairs",
        "content_tracks": ["Teorie clara", "Experimenteaza cu selectori"],
        "fun_fact": "CSS a fost propus in 1994 de Hakon Wium Lie pentru ca paginile sa arate frumos si consistent.",
        "hero_theme": "sunrise-lab",
        "hero_emoji": "🎨",
        "objectives": [
            _objective(
                "Sa inteleg selectori de tag, clasa si ID.",
                "Concept",
                "Pot explica diferenta dintre `h1`, `.buton` si `#hero`.",
            ),
            _objective(
                "Sa folosesc proprietati de culoare si spatiu.",
                "Practica",
                "Pot scrie un stil cu `color`, `background` si `margin`.",
            ),
            _objective(
                "Sa vad pagina ca un set de cutii.",
                "Reflectie",
                "Pot arata unde este margin si unde este padding.",
            ),
        ],
        "practice": _practice(
            "Potriveste fiecare proprietate CSS cu efectul ei pe pagina.",
            "Trage proprietatea CSS spre explicatia potrivita.",
            "Bravo! Ai pictat pagina ca un profesionist.",
            [
                ("color", "color"),
                ("background", "background"),
                ("font-size", "font-size"),
                ("margin", "margin"),
                ("padding", "padding"),
                ("border", "border"),
            ],
            [
                ("Schimba culoarea textului.", "color"),
                ("Schimba culoarea fundalului unui element.", "background"),
                ("Schimba marimea literelor.", "font-size"),
                ("Adauga spatiu in afara elementului.", "margin"),
                ("Adauga spatiu intre continut si marginea elementului.", "padding"),
                ("Deseneaza o linie in jurul elementului.", "border"),
            ],
        ),
        "tests": [
            _test(
                "Ce proprietate schimba culoarea textului?",
                "color",
                ["background", "font-size", "align"],
                "`color` schimba culoarea textului; `background` schimba culoarea fundalului.",
                "Ce combinatie de culori ai folosi pentru un titlu care se citeste usor?",
                "Browserul foloseste `color` doar pentru text, iar `background` pentru fundal — sunt proprietati separate.",
            ),
            _test(
                "Ce controleaza `margin`?",
                "Spatiul din afara elementului",
                [
                    "Spatiul din interiorul elementului",
                    "Alinierea textului",
                    "Grosimea bordurii",
                ],
                "`margin` impinge elementele unul de altul; `padding` creeaza spatiu intre continut si marginea elementului.",
                "Gandeste-te la un buton cu spatiu frumos in jurul sau — ce proprietate folosesti?",
                "Modelul de cutie: continut → padding → border → margin. Margin e stratul cel mai exterior.",
            ),
            _test(
                "Care selector tinteste o clasa?",
                ".buton",
                ["#buton", "buton", "*buton"],
                "Clasele se scriu cu un punct inainte (`.`) si pot fi reutilizate pe mai multe elemente.",
                "Cand ai avea nevoie de aceeasi stilizare pe mai multe butoane?",
                '`.buton` tinteste orice element cu `class="buton"`; `#buton` ar fi un ID unic.',
            ),
        ],
        "reflections": _default_reflections(
            "Web 2 · Stiluri cu CSS",
            "Care proprietate CSS crezi ca o vei folosi cel mai des in paginile tale?",
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


def seed_web_basics_lessons(apps, schema_editor):
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
    subject.description = "Construieste pagini web cu HTML si CSS — traseu vizual pentru 8-10 ani si cod real pentru 11+."
    subject.save(update_fields=["description"])

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
        ("estudy", "0054_seed_robot_lab_skins"),
    ]

    operations = [
        migrations.RunPython(seed_web_basics_lessons, migrations.RunPython.noop),
    ]
