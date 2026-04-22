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


LESSON_BLUEPRINTS = []


LESSON_BLUEPRINTS.extend(
    [
        {
            "slug": "code-1-bun-venit-in-python",
            "legacy_slugs": ["1"],
            "title": "Code 1 · Bun venit in Python",
            "date": date(2025, 9, 24),
            "age_bracket": "11-13",
            "difficulty": "beginner",
            "duration_minutes": 30,
            "xp_reward": 45,
            "excerpt": "Faci cunostinta cu Python si inveti cum ruleaza un program, pas cu pas.",
            "theory_intro": "Python citeste instructiunile de sus in jos. Daca scrii clar, calculatorul executa exact pasii pe care ii ceri.",
            "content": _content(
                "Prima super-putere in Python este ordinea. Programul citeste fiecare linie pe rand, asa ca pasii trebuie asezati logic.",
                "Comanda `print()` afiseaza un mesaj pe ecran. Cu ea vezi rapid ce face programul tau si verifici daca ai scris bine ideea.",
                "In lectiile urmatoare vei adauga variabile, decizii si repetitii. Astazi important este sa intelegi ca un program este o lista clara de instructiuni.",
            ),
            "theory_takeaways": [
                "Python executa codul de sus in jos.",
                "`print()` afiseaza rezultatul pe ecran.",
                "Un program bun are pasi simpli si clari.",
            ],
            "warmup_prompt": "Ce mesaj ai afisa primul daca ai crea un robot care te saluta?",
            "discussion_prompts": [
                "Unde vezi in viata reala o lista de pasi care trebuie urmati in ordine?",
                "De ce este util sa vezi rezultatul imediat dupa ce rulezi codul?",
                "Cum ti-ai explica singur ce face `print()`?",
            ],
            "story_anchor": "Nova porneste consola robotului si iti cere primul mesaj de bun venit pentru echipa.",
            "home_extension": "Arata acasa doua exemple de mesaje pe care le-ai afisa cu `print()` intr-un joc sau intr-o aplicatie.",
            "collaboration_mode": "pairs",
            "content_tracks": ["Teorie clara", "Mica provocare de inceput"],
            "fun_fact": "Primele programe bune par simple tocmai pentru ca au pasi foarte clari.",
            "hero_theme": "sunrise-lab",
            "hero_emoji": "🤖",
            "objectives": [
                _objective(
                    "Sa intelegem cum ruleaza un program Python.",
                    "Concept",
                    "Pot spune cu propriile cuvinte ca programul se executa de sus in jos.",
                ),
                _objective(
                    "Sa folosim `print()` pentru a afisa un mesaj.",
                    "Practica",
                    "Pot recunoaste o linie care afiseaza text pe ecran.",
                ),
                _objective(
                    "Sa verificam daca ordinea pasilor este corecta.",
                    "Reflectie",
                    "Pot observa ce se schimba cand mut doua instructiuni.",
                ),
            ],
            "practice": _practice(
                "Robo vrea sa porneasca bine. Potriveste fiecare piesa cu rolul ei.",
                "Trage cartonasul corect spre explicatia potrivita.",
                "Perfect! Robo stie acum cum incepe un program.",
                [
                    ("print", "print('Salut!')"),
                    ("sir", "'Salut!'"),
                    ("ordine", "Pasul 1 -> Pasul 2"),
                    ("ruleaza", "Run"),
                ],
                [
                    ("Linia care afiseaza un mesaj pe ecran.", "print"),
                    ("Textul care va aparea in consola.", "sir"),
                    ("Ideea ca pasii se executa in ordinea scrisa.", "ordine"),
                    ("Butonul sau actiunea care porneste programul.", "ruleaza"),
                ],
            ),
            "tests": [
                _test(
                    "Ce face functia `print()`?",
                    "Afiseaza un mesaj sau o valoare pe ecran",
                    [
                        "Sterge codul care nu functioneaza",
                        "Repeta o instructiune de mai multe ori",
                        "Creeaza automat o variabila noua",
                    ],
                    "`print()` este cea mai simpla metoda de a vedea rezultatul programului tau.",
                    "Imagineaza-ti un mesaj de pornire pentru un joc si descrie-l in cuvinte.",
                    "Cand afisezi ceva pe ecran, poti verifica rapid daca programul face ce te astepti.",
                ),
                _test(
                    "De ce conteaza ordinea liniilor intr-un program?",
                    "Pentru ca Python executa instructiunile exact in ordinea in care apar",
                    [
                        "Pentru ca doar prima linie este citita",
                        "Pentru ca ordinea schimba culoarea editorului",
                        "Pentru ca liniile sunt alese la intamplare de calculator",
                    ],
                    "Calculatorul nu ghiceste intentia ta. El urmeaza pasii exact asa cum i-ai scris.",
                    "Da un exemplu de activitate de zi cu zi unde ordinea pasilor este importanta.",
                    "Daca ordinea este gresita, rezultatul se schimba sau programul nu mai are sens.",
                ),
            ],
            "reflections": _default_reflections(
                "Code 1 · Bun venit in Python",
                "Ce mesaj ai vrea sa afisezi primul intr-un program creat de tine?",
            ),
        },
        {
            "slug": "nivel-1-prieteni-cu-variabilele",
            "legacy_slugs": [],
            "title": "Junior 1 · Prieteni cu variabilele",
            "date": date(2025, 9, 25),
            "age_bracket": "8-10",
            "difficulty": "beginner",
            "duration_minutes": 25,
            "xp_reward": 40,
            "excerpt": "Inveti cum o cutie cu nume poate pastra un scor, un nume sau un mesaj.",
            "theory_intro": "O variabila este o cutie cu eticheta. Pui in ea o valoare si o poti folosi mai tarziu in jocul tau.",
            "content": _content(
                "Imagineaza-ti ca Robo strange stele intr-un joc. Daca vrei sa tii minte cate stele are, creezi o cutie numita `stele`.",
                "Scrii `stele = 3`, iar programul pastreaza numarul. Cand Robo mai gaseste o stea, schimbi valoarea din cutie.",
                "Variabilele sunt folositoare pentru nume, vieti, scoruri si mesaje personalizate. Alege mereu nume clare, ca sa intelegi usor codul.",
            ),
            "theory_takeaways": [
                "O variabila are un nume si o valoare.",
                "Valoarea din cutie se poate schimba.",
                "Numele clar te ajuta sa intelegi programul.",
            ],
            "warmup_prompt": "Ce ai vrea sa tina minte Robo: numele jucatorului, scorul sau culoarea preferata?",
            "discussion_prompts": [
                "Unde ai folosi o cutie cu nume intr-un joc?",
                "De ce crezi ca este bine sa alegem nume clare pentru variabile?",
                "Ce se poate intampla cand o variabila isi schimba valoarea?",
            ],
            "story_anchor": "Robo pregateste consola de joc si are nevoie de cutii etichetate pentru scor, nume si energie.",
            "home_extension": "Inventeaza acasa trei variabile pentru un joc simplu: una pentru nume, una pentru scor si una pentru vieti.",
            "collaboration_mode": "pairs",
            "content_tracks": ["Poveste ghidata", "Provocare bonus"],
            "fun_fact": "Multe jocuri tin minte scorul exact cu ajutorul variabilelor.",
            "hero_theme": "sunrise-lab",
            "hero_emoji": "⭐",
            "objectives": [
                _objective(
                    "Sa intelegem ce este o variabila.",
                    "Concept",
                    "Pot explica variabila ca pe o cutie cu eticheta.",
                ),
                _objective(
                    "Sa potrivim numele, valoarea si afisarea unei variabile.",
                    "Practica",
                    "Pot recunoaste un exemplu simplu de variabila.",
                ),
                _objective(
                    "Sa folosim ideea intr-un joc imaginar.",
                    "Reflectie",
                    "Pot spune ce as salva intr-o variabila din jocul meu.",
                ),
            ],
            "practice": _practice(
                "Robo are nevoie sa recapitulam ce inseamna fiecare piesa a unei variabile.",
                "Trage piesele corecte spre explicatia potrivita pentru a-l ajuta pe Robo sa repare consola.",
                "Excelent! Robo si-a reamintit totul despre variabile.",
                [
                    ("naming", "nume_jucator"),
                    ("value", "'Mara'"),
                    ("update", "scor = scor + bonus"),
                    ("display", "print(mesaj)"),
                ],
                [
                    ("Numele variabilei care pastreaza un text.", "naming"),
                    ("Exemplu de valoare pentru o variabila de tip text.", "value"),
                    ("Instructiune ce mareste valoarea existenta.", "update"),
                    ("Comanda care afiseaza continutul cutiei.", "display"),
                ],
            ),
            "tests": [
                _test(
                    "Care este rolul unei variabile intr-un program?",
                    "Pastreaza o informatie pe care o folosim mai tarziu",
                    [
                        "Deseneaza automat un personaj pe ecran",
                        "Opreste programul cand apare o eroare",
                        "Sterge toate valorile din memorie",
                    ],
                    "O variabila este o cutie cu nume care pastreaza o informatie utila.",
                    "Gandeste-te la o variabila pentru scor si spune ce valoare ar putea avea.",
                    "Fara variabile, ar trebui sa rescrii mereu aceeasi informatie in mai multe locuri.",
                ),
                _test(
                    "Ce inseamna `scor = scor + 1`?",
                    "Scorul creste cu 1 fata de valoarea pe care o avea deja",
                    [
                        "Scorul devine mereu 1",
                        "Variabila `scor` dispare",
                        "Comparam doua scoruri diferite",
                    ],
                    "O variabila poate fi actualizata folosind chiar valoarea ei curenta.",
                    "Imagineaza-ti ca Robo gaseste o stea. Ce s-ar intampla cu variabila `stele`?",
                    "Programul ia valoarea veche, adauga 1 si scrie noul rezultat inapoi in variabila.",
                ),
            ],
            "reflections": _default_reflections(
                "Junior 1 · Prieteni cu variabilele",
                "Unde ai folosi o variabila intr-un joc creat de tine?",
            ),
        },
        {
            "slug": "code-2-variabile-si-date",
            "legacy_slugs": ["tmp-python-entry"],
            "title": "Code 2 · Variabile si date",
            "date": date(2025, 10, 1),
            "age_bracket": "11-13",
            "difficulty": "beginner",
            "duration_minutes": 30,
            "xp_reward": 50,
            "excerpt": "Inveti sa stochezi texte, numere si valori simple in variabile bine numite.",
            "theory_intro": "Variabilele sunt memoria programului tau. In ele poti pastra texte, numere sau stari pe care le vei folosi mai tarziu.",
            "content": _content(
                "Cand construiesti un joc, ai nevoie de locuri unde sa pastrezi informatii: numele jucatorului, scorul, nivelul sau energia.",
                "Python iti permite sa creezi rapid o variabila: `nume = 'Ana'` sau `scor = 10`. Tipul valorii iti spune ce poti face mai departe cu ea.",
                "Cele mai bune variabile au nume clare. Daca alegi nume precum `energie_robot` sau `mesaj_final`, citesti codul mult mai usor si gasesti mai repede greselile.",
            ),
            "theory_takeaways": [
                "O variabila poate pastra text, numar sau o stare simpla.",
                "Tipul valorii influenteaza operatiile pe care le poti face.",
                "Numele clar face codul mai usor de citit.",
            ],
            "warmup_prompt": "Ce trei informatii ar trebui sa retina un robot de joc la inceputul unei misiuni?",
            "discussion_prompts": [
                "Cum alegi un nume bun pentru o variabila?",
                "Cand ai folosi text si cand ai folosi numere intr-un program?",
                "De ce este util sa actualizezi o variabila in loc sa creezi alta noua?",
            ],
            "story_anchor": "Byte construieste un panou de control si are nevoie de date corecte despre robot si despre jucator.",
            "home_extension": "Scrie acasa o lista cu cinci variabile pe care le-ai folosi intr-un quiz, intr-un joc sau intr-o aplicatie de teme.",
            "collaboration_mode": "solo",
            "content_tracks": ["Teorie + exemplu", "Provocare de cod"],
            "fun_fact": "Multe bug-uri simple apar din cauza unor nume de variabile neclare sau prea asemanatoare.",
            "hero_theme": "sky-fizz",
            "hero_emoji": "🧠",
            "objectives": [
                _objective(
                    "Sa recunoastem principalele tipuri de valori simple din Python.",
                    "Concept",
                    "Pot distinge intre text, numar si stare simpla.",
                ),
                _objective(
                    "Sa potrivim corect variabile si exemple reale de folosire.",
                    "Practica",
                    "Pot alege o variabila potrivita pentru un scenariu dat.",
                ),
                _objective(
                    "Sa descriem de ce numele clare conteaza.",
                    "Reflectie",
                    "Pot rescrie un nume vag intr-unul mai bun.",
                ),
            ],
            "practice": _practice(
                "Consola lui Byte afiseaza date amestecate. Pune fiecare piesa la locul ei.",
                "Potriveste cartonasul cu explicatia corecta.",
                "Datele sunt acum organizate perfect.",
                [
                    ("text", "'Misiune pornita'"),
                    ("number", "45"),
                    ("state", "robot_activ = True"),
                    ("name", "energie_robot"),
                ],
                [
                    ("Exemplu de valoare de tip text.", "text"),
                    ("Exemplu de valoare numerica.", "number"),
                    ("Exemplu de variabila care pastreaza o stare.", "state"),
                    ("Nume clar pentru o variabila dintr-un joc.", "name"),
                ],
            ),
            "tests": [
                _test(
                    "Care variabila are cel mai clar nume pentru energia robotului?",
                    "energie_robot",
                    ["x", "abc", "data1"],
                    "Un nume bun trebuie sa spuna ce informatie pastreaza.",
                    "Rescrie pe hartie doua nume vagi si doua nume clare pentru acelasi tip de informatie.",
                    "Cand numele este clar, citesti si repari codul mult mai usor.",
                ),
                _test(
                    "Ce valoare ai alege pentru un scor?",
                    "Un numar, de exemplu 120",
                    [
                        "Un text precum 'rapid'",
                        "O comanda `print()`",
                        "O bucla `for`",
                    ],
                    "Scorul se modifica prin calcule, deci este de obicei un numar.",
                    "Imagineaza-ti un joc cu puncte. Noteaza un numar de inceput pentru variabila `scor`.",
                    "Numerele pot fi adunate, scazute si comparate, de aceea sunt potrivite pentru scor.",
                ),
            ],
            "reflections": _default_reflections(
                "Code 2 · Variabile si date",
                "Ce variabile ai alege pentru un mic joc creat de tine?",
            ),
        },
        {
            "slug": "junior-2-comenzi-pentru-robo",
            "legacy_slugs": ["junior-entry-debug"],
            "title": "Junior 2 · Comenzi pentru Robo",
            "date": date(2025, 10, 2),
            "age_bracket": "8-10",
            "difficulty": "beginner",
            "duration_minutes": 25,
            "xp_reward": 40,
            "excerpt": "Descoperi ca un algoritm este o lista clara de pasi asezati in ordinea potrivita.",
            "theory_intro": "Un algoritm este un plan cu pasi clari. Daca ordinea este buna, Robo ajunge unde trebuie.",
            "content": _content(
                "Cand Robo merge prin laborator, nu ghiceste drumul. El urmeaza pasii exact in ordinea in care ii primeste.",
                "Daca schimbi doi pasi intre ei, robotul poate rata usa sau se poate lovi de un obstacol. De aceea ordinea este foarte importanta.",
                "Programarea incepe cu planuri simple: mergi, opreste-te, intoarce-te, verifica. Un algoritm bun spune clar ce urmeaza.",
            ),
            "theory_takeaways": [
                "Un algoritm este o lista de pasi.",
                "Ordinea pasilor schimba rezultatul.",
                "Pasi mici si clari inseamna mai putine greseli.",
            ],
            "warmup_prompt": "Cum i-ai explica lui Robo drumul de la usa pana la banca ta?",
            "discussion_prompts": [
                "Ce s-ar intampla daca ai pune pasii in alta ordine?",
                "Unde folosesti si tu algoritmi in viata de zi cu zi?",
                "Ce fel de pasi trebuie sa fie usor de urmat de catre un robot?",
            ],
            "story_anchor": "Pixel ii pregateste lui Robo un traseu prin laborator si are nevoie de instructiuni foarte clare.",
            "home_extension": "Fa acasa un algoritm in trei sau patru pasi pentru a pregati ghiozdanul sau pentru a uda o planta.",
            "collaboration_mode": "small_group",
            "content_tracks": ["Pasi ghidati", "Provocare bonus"],
            "fun_fact": "Chiar si o reteta de sandvis poate fi vazuta ca un algoritm.",
            "hero_theme": "mint-track",
            "hero_emoji": "🗺️",
            "objectives": [
                _objective(
                    "Sa intelegem ce este un algoritm.",
                    "Concept",
                    "Pot descrie un algoritm ca pe o lista de pasi.",
                ),
                _objective(
                    "Sa alegem ordinea corecta pentru un traseu simplu.",
                    "Practica",
                    "Pot identifica pasul care trebuie pus primul.",
                ),
                _objective(
                    "Sa legam ideea de o activitate de zi cu zi.",
                    "Reflectie",
                    "Pot inventa un algoritm simplu pentru acasa.",
                ),
            ],
            "practice": _practice(
                "Robo a primit comenzile amestecate. Ajuta-l sa le inteleaga.",
                "Trage fiecare cartonas la rolul potrivit.",
                "Super! Traseul lui Robo este acum clar.",
                [
                    ("start", "Porneste"),
                    ("move", "Mergi inainte"),
                    ("turn", "Intoarce la dreapta"),
                    ("stop", "Opreste-te"),
                ],
                [
                    ("Primul pas prin care incepe algoritmul.", "start"),
                    ("Comanda folosita pentru a avansa.", "move"),
                    ("Comanda folosita pentru a schimba directia.", "turn"),
                    ("Ultimul pas care incheie traseul.", "stop"),
                ],
            ),
            "tests": [
                _test(
                    "Ce este un algoritm?",
                    "O lista clara de pasi pentru a rezolva o sarcina",
                    [
                        "Un desen pe tabla",
                        "Un tip special de baterie",
                        "Un joc in care nu exista reguli",
                    ],
                    "Algoritmul spune exact ce trebuie facut si in ce ordine.",
                    "Descrie pe scurt pasii pentru a deschide un penar.",
                    "Cand pasii sunt clari, altcineva ii poate urma fara sa ghiceasca.",
                ),
                _test(
                    "De ce conteaza ordinea pasilor?",
                    "Pentru ca rezultatul se schimba daca muti pasii intre ei",
                    [
                        "Pentru ca robotii tin minte doar primul pas",
                        "Pentru ca ultimul pas este mereu optional",
                        "Pentru ca ordinea nu are nicio importanta",
                    ],
                    "Ordinea este partea care leaga pasii intr-un plan corect.",
                    "Imagineaza-ti doi pasi inversati intr-o reteta. Ce problema apare?",
                    "Un pas bun la momentul gresit poate produce un rezultat gresit.",
                ),
            ],
            "reflections": _default_reflections(
                "Junior 2 · Comenzi pentru Robo",
                "Ce algoritm simplu ai vrea sa-i dai lui Robo pentru maine?",
            ),
        },
    ]
)


LESSON_BLUEPRINTS.extend(
    [
        {
            "slug": "nivel-3-super-puteri-cu-functii",
            "legacy_slugs": [],
            "title": "Code 7 · Super-puteri cu functii",
            "date": date(2025, 11, 5),
            "age_bracket": "14-16",
            "difficulty": "intermediate",
            "duration_minutes": 40,
            "xp_reward": 65,
            "excerpt": "Impachetezi logica in functii reutilizabile si inveti sa trimiti si sa primesti valori.",
            "theory_intro": "Functiile sunt super-puteri pe care le chemi cand ai nevoie. Ele grupeaza pasi utili sub un nume clar.",
            "content": _content(
                "Daca ai un calcul pe care il folosesti de multe ori, nu vrei sa copiezi acelasi cod in mai multe locuri. O functie iti permite sa scrii logica o singura data.",
                "Parametrii trimit functiei datele de care are nevoie. Cu `return`, functia iti da inapoi rezultatul ca sa-l poti folosi in alte parti ale programului.",
                "Functiile fac proiectele mai ordonate. Cand numele este bun si pasii din interior au sens, codul devine mai usor de citit, testat si reparat.",
            ),
            "theory_takeaways": [
                "Functiile grupeaza pasi reutilizabili.",
                "Parametrii duc datele spre functie.",
                "`return` aduce rezultatul inapoi.",
            ],
            "warmup_prompt": "Ce super-putere repetitiva ai transforma intr-o functie intr-un joc sau intr-o aplicatie?",
            "discussion_prompts": [
                "Ce fel de sarcini merita puse intr-o functie?",
                "Cum alegi un nume bun pentru o functie?",
                "Cand iti este util `return`?",
            ],
            "story_anchor": "Byte construieste o biblioteca de miscari si calcule pentru tot laboratorul robotilor.",
            "home_extension": "Descrie acasa o functie imaginara pentru un joc: ce parametri primeste si ce rezultat intoarce.",
            "collaboration_mode": "pairs",
            "content_tracks": ["Teorie + exemplu", "Misiune de structurare"],
            "fun_fact": "Functiile bine numite fac proiectele mari mult mai usor de inteles in echipa.",
            "hero_theme": "cosmos-grid",
            "hero_emoji": "✨",
            "objectives": [
                _objective(
                    "Sa intelegem de ce folosim functii.",
                    "Concept",
                    "Pot spune ce problema rezolva o functie intr-un proiect mai mare.",
                ),
                _objective(
                    "Sa potrivim definitia, parametrii si rezultatul unei functii.",
                    "Practica",
                    "Pot recunoaste rolul fiecarui element dintr-o functie simpla.",
                ),
                _objective(
                    "Sa gandim o functie utila pentru un joc sau pentru un robot.",
                    "Reflectie",
                    "Pot descrie pe scurt o functie proprie.",
                ),
            ],
            "practice": _practice(
                "Echipa ta are nevoie de o biblioteca de super-puteri. Sorteaza fiecare piesa la locul ei.",
                "Trage elementele spre definitia corecta pentru a finaliza laboratorul functiilor.",
                "Fantastic! Biblioteca de functii este gata de lansare.",
                [
                    ("define", "def calculeaza_bonus(...):"),
                    ("param", "multiplu"),
                    ("return", "return rezultat"),
                    ("call", "print(calculeaza_bonus(50, 2))"),
                ],
                [
                    ("Linia unde definim functia.", "define"),
                    ("Variabila locala care primeste valoarea trimisa.", "param"),
                    ("Instructiunea care trimite rezultatul inapoi.", "return"),
                    ("Exemplu de apel cu afisarea rezultatului.", "call"),
                ],
            ),
            "tests": [
                _test(
                    "Ce face `return` intr-o functie?",
                    "Trimite rezultatul functiei inapoi la locul de apel",
                    [
                        "Porneste functia din nou",
                        "Sterge parametrii functiei",
                        "Afiseaza automat un meniu",
                    ],
                    "`return` este modul prin care functia ofera un rezultat restului programului.",
                    "Descrie pe scurt o functie care calculeaza punctajul final al unui jucator.",
                    "Fara `return`, functia poate rula, dar programul nu primeste inapoi valoarea de care are nevoie.",
                ),
                _test(
                    "De ce folosim parametri?",
                    "Pentru a trimite functiei date diferite la fiecare apel",
                    [
                        "Pentru a opri functia sa ruleze",
                        "Pentru a transforma functia intr-o bucla",
                        "Pentru a ascunde numele functiei",
                    ],
                    "Parametrii fac functiile flexibile si reutilizabile.",
                    "Imagineaza-ti o functie `saluta(nume)`. Ce valori ai putea trimite?",
                    "Cu parametri, aceeasi functie poate rezolva multe situatii asemanatoare.",
                ),
            ],
            "reflections": _default_reflections(
                "Code 7 · Super-puteri cu functii",
                "Ce functie utila ai vrea sa creezi pentru propriul tau proiect?",
            ),
        },
        {
            "slug": "code-8-functii-pentru-jocuri",
            "legacy_slugs": ["code-entry-client2"],
            "title": "Code 8 · Functii pentru jocuri",
            "date": date(2025, 11, 12),
            "age_bracket": "11-13",
            "difficulty": "intermediate",
            "duration_minutes": 35,
            "xp_reward": 65,
            "excerpt": "Folosesti functii ca sa separi meniul, scorul si regulile unui joc mic.",
            "theory_intro": "Cand proiectul tau creste, functiile te ajuta sa imparti programul in bucati mici si usor de refolosit.",
            "content": _content(
                "Intr-un joc ai parti diferite: afisarea meniului, calculul scorului, verificarea victoriei sau raspunsul la o alegere a jucatorului.",
                "Daca fiecare parte devine o functie, intelegi mai usor unde se intampla fiecare lucru. Poti testa separat o singura piesa fara sa rulezi tot proiectul.",
                "Acesta este pasul care transforma un cod mic si dezordonat intr-un proiect pe care il poti imbunatati fara teama.",
            ),
            "theory_takeaways": [
                "Functiile impart proiectul in bucati mici.",
                "Fiecare functie ar trebui sa aiba un scop clar.",
                "Un proiect organizat este mai usor de testat si extins.",
            ],
            "warmup_prompt": "Daca ai crea un quiz, ce parte ai pune prima intr-o functie: mesajul de start, scorul sau verificarea raspunsului?",
            "discussion_prompts": [
                "Ce functie ai crea pentru a afisa regulile unui joc?",
                "Cum te ajuta separarea pe functii cand apar bug-uri?",
                "De ce este bine ca fiecare functie sa faca un lucru clar?",
            ],
            "story_anchor": "Nova vrea sa transforme ideile voastre intr-un joc ordonat, usor de testat si de prezentat.",
            "home_extension": "Deseneaza acasa schema unui mini joc cu trei functii: start, calculeaza_scor si afiseaza_rezultat.",
            "collaboration_mode": "pairs",
            "content_tracks": ["Planul jocului", "Provocare de structurare"],
            "fun_fact": "Multe proiecte bune par mai usoare doar pentru ca au fost impartite in functii mici si clare.",
            "hero_theme": "aurora-grid",
            "hero_emoji": "🎮",
            "objectives": [
                _objective(
                    "Sa vedem cum functiile organizeaza un proiect.",
                    "Concept",
                    "Pot spune ce parti ale unui joc pot deveni functii.",
                ),
                _objective(
                    "Sa potrivim functii cu rolul lor intr-un joc mic.",
                    "Practica",
                    "Pot asocia o functie cu responsabilitatea potrivita.",
                ),
                _objective(
                    "Sa schitam un mini proiect bine impartit.",
                    "Reflectie",
                    "Pot propune trei functii utile pentru un joc propriu.",
                ),
            ],
            "practice": _practice(
                "Quizul robotului are functiile amestecate. Pune fiecare piesa unde trebuie.",
                "Potriveste functia cu rolul ei in joc.",
                "Excelent! Jocul este acum mult mai bine organizat.",
                [
                    ("start", "afiseaza_bun_venit()"),
                    ("score", "calculeaza_scor(raspunsuri)"),
                    ("check", "verifica_raspuns(corect, primit)"),
                    ("end", "afiseaza_rezultat(final)"),
                ],
                [
                    (
                        "Functia care porneste jocul si afiseaza mesajul initial.",
                        "start",
                    ),
                    ("Functia care aduna punctele jucatorului.", "score"),
                    (
                        "Functia care compara raspunsul jucatorului cu cel corect.",
                        "check",
                    ),
                    ("Functia care afiseaza finalul jocului.", "end"),
                ],
            ),
            "tests": [
                _test(
                    "De ce este util sa imparti un joc in functii?",
                    "Pentru ca il intelegi, testezi si extinzi mai usor",
                    [
                        "Pentru ca dispar toate bug-urile automat",
                        "Pentru ca jocul ruleaza doar daca are exact trei functii",
                        "Pentru ca nu mai ai nevoie de variabile",
                    ],
                    "Functiile reduc haosul si separa responsabilitatile.",
                    "Descrie doua functii pe care le-ai folosi intr-un joc de intrebari.",
                    "Cand fiecare functie are un scop clar, stii imediat unde sa cauti o problema sau unde sa adaugi o idee noua.",
                ),
                _test(
                    "Ce functie se ocupa cel mai bine de compararea unui raspuns?",
                    "`verifica_raspuns(corect, primit)`",
                    [
                        "`afiseaza_bun_venit()`",
                        "`porneste_muzica()`",
                        "`deseneaza_fundal()`",
                    ],
                    "Numele functiei trebuie sa spuna clar responsabilitatea ei.",
                    "Gandeste-te la un nume bun pentru o functie care arata scorul curent.",
                    "Cea mai buna functie pentru comparare este cea care spune exact ca verifica raspunsuri.",
                ),
            ],
            "reflections": _default_reflections(
                "Code 8 · Functii pentru jocuri",
                "Ce trei functii ai pune intr-un quiz facut de tine?",
            ),
        },
        {
            "slug": "junior-6-poveste-interactiva",
            "legacy_slugs": ["junior-entry-client3"],
            "title": "Junior 6 · Poveste interactiva",
            "date": date(2025, 10, 30),
            "age_bracket": "8-10",
            "difficulty": "intermediate",
            "duration_minutes": 30,
            "xp_reward": 50,
            "excerpt": "Folosesti ideile invatate ca sa planifici o mica poveste cu alegeri, scor si personaje.",
            "theory_intro": "Acum combini mai multe idei: un personaj, o alegere, un scor si cativa pasi repetati. Asa incepe un proiect adevarat.",
            "content": _content(
                "O poveste interactiva are nevoie de personaje, reguli si mici surprize. Poti pastra numele eroului intr-o variabila, poti folosi o regula daca si poti repeta o actiune importanta.",
                "Nu trebuie sa fie un proiect mare. Important este sa stii ce parte face fiecare idee si sa le asezi intr-o ordine usor de urmarit.",
                "Cand iti planifici povestea in pasi mici, proiectul devine clar, distractiv si usor de explicat altcuiva.",
            ),
            "theory_takeaways": [
                "Un proiect mic combina idei simple invatate deja.",
                "Variabilele, regulile si repetitiile pot lucra impreuna.",
                "Planul clar este primul pas spre un proiect reusit.",
            ],
            "warmup_prompt": "Cum s-ar numi eroul din povestea ta interactiva si ce alegere importanta ar avea de facut?",
            "discussion_prompts": [
                "Ce informatie ai pastra intr-o variabila in povestea ta?",
                "Unde ai folosi o regula de tip daca?",
                "Ce pas sau ce actiune s-ar repeta in proiectul tau?",
            ],
            "story_anchor": "Nova te invita sa construiesti o mica aventura pentru Robo, cu alegeri si finaluri diferite.",
            "home_extension": "Povesteste acasa ideea proiectului tau si deseneaza trei cadre: inceput, alegere si final.",
            "collaboration_mode": "pairs",
            "content_tracks": ["Planul povestii", "Bonus creativ"],
            "fun_fact": "Multe jocuri mari au pornit de la un plan simplu pe hartie, cu cateva reguli clare.",
            "hero_theme": "story-spark",
            "hero_emoji": "📖",
            "objectives": [
                _objective(
                    "Sa legam intre ele ideile invatate pana acum.",
                    "Concept",
                    "Pot spune ce rol are fiecare piesa intr-un proiect mic.",
                ),
                _objective(
                    "Sa potrivim elementele unei povesti interactive.",
                    "Practica",
                    "Pot alege ce parte tine de personaj, regula sau scor.",
                ),
                _objective(
                    "Sa schitam un proiect propriu usor de prezentat.",
                    "Reflectie",
                    "Pot descrie pe scurt ideea unei povesti interactive create de mine.",
                ),
            ],
            "practice": _practice(
                "Planul povestii lui Robo este amestecat. Potriveste fiecare piesa cu locul ei.",
                "Trage fiecare cartonas spre explicatia corecta.",
                "Minunat! Povestea interactiva are acum un plan clar.",
                [
                    ("hero", "nume_erou"),
                    ("choice", "Daca alegi usa rosie..."),
                    ("score", "stele = stele + 1"),
                    ("repeat", "Repeta cautarea de 3 ori"),
                ],
                [
                    ("Variabila care tine minte numele personajului.", "hero"),
                    ("Regula care schimba povestea dupa alegere.", "choice"),
                    ("Partea care modifica punctajul.", "score"),
                    ("Partea care repeta o actiune in proiect.", "repeat"),
                ],
            ),
            "tests": [
                _test(
                    "Ce face un proiect interactiv mai usor de inteles?",
                    "Un plan clar, cu pasi mici si roluri bine impartite",
                    [
                        "Sa fie cat mai lung de la inceput",
                        "Sa schimbi toate ideile in acelasi timp",
                        "Sa nu folosesti reguli deloc",
                    ],
                    "Un proiect bun incepe cu un plan simplu si usor de urmarit.",
                    "Descrie inceputul, alegerea si finalul unei mini povesti pentru Robo.",
                    "Cand fiecare parte are un rol clar, proiectul este mai usor de construit si de explicat.",
                ),
                _test(
                    "Unde ai putea folosi o variabila intr-o poveste interactiva?",
                    "Pentru numele eroului, scor sau numarul de stele",
                    [
                        "Doar pentru a schimba fundalul",
                        "Doar la final, fara alt rol",
                        "Nu ai nevoie de variabile intr-o poveste",
                    ],
                    "Variabilele pastreaza datele care se pot schimba pe parcursul povestii.",
                    "Spune ce variabila ai crea prima in povestea ta.",
                    "Fara variabile ar fi greu sa tii minte numele, scorul sau progresul jucatorului.",
                ),
            ],
            "reflections": _default_reflections(
                "Junior 6 · Poveste interactiva",
                "Ce aventura ai vrea sa construiesti pentru Robo ca proiect final?",
            ),
        },
        {
            "slug": "code-9-mini-proiect-quiz-robot",
            "legacy_slugs": ["code-entry-client3"],
            "title": "Code 9 · Mini proiect: Quiz Robot",
            "date": date(2025, 11, 19),
            "age_bracket": "11-13",
            "difficulty": "advanced",
            "duration_minutes": 40,
            "xp_reward": 70,
            "excerpt": "Combini variabile, conditii, liste si functii intr-un mini proiect coerent si usor de prezentat.",
            "theory_intro": "Un mini proiect bun nu inseamna mult cod, ci cod clar. Acum aduci la un loc ideile invatate ca sa construiesti un quiz mic pentru Robo.",
            "content": _content(
                "Quizul are nevoie de cateva piese simple: intrebari, raspunsuri, o metoda de verificare, un scor si un final clar pentru jucator.",
                "Variabilele tin minte starea curenta, listele grupeaza intrebarile, conditiile verifica raspunsul, iar functiile impart proiectul in bucati usor de citit.",
                "Cand gandesti proiectul pe componente, devine mai usor sa-l explici, sa-l testezi si sa-l imbunatatesti dupa feedback.",
            ),
            "theory_takeaways": [
                "Un mini proiect bun combina idei simple intr-un plan clar.",
                "Fiecare componenta trebuie sa aiba un rol usor de explicat.",
                "Testarea si feedbackul te ajuta sa imbunatatesti proiectul.",
            ],
            "warmup_prompt": "Ce intrebare ai pune prima intr-un quiz facut pentru Robo si prietenii lui?",
            "discussion_prompts": [
                "Ce parti ai separa in functii intr-un quiz?",
                "Ce date ai pune intr-o lista?",
                "Cum ai verifica daca proiectul tau este usor de folosit?",
            ],
            "story_anchor": "Echipa UNITEX pregateste un concurs pentru Robo, iar tu construiesti quizul care il va ghida din intrebare in intrebare.",
            "home_extension": "Arata acasa schita proiectului tau: lista de intrebari, scor, regula de verificare si mesajul final.",
            "collaboration_mode": "solo",
            "content_tracks": ["Structura proiectului", "Verificare si feedback"],
            "fun_fact": "Proiectele mici bine organizate sunt adesea mai impresionante decat proiectele mari si confuze.",
            "hero_theme": "midnight-arcade",
            "hero_emoji": "🏁",
            "objectives": [
                _objective(
                    "Sa intelegem arhitectura simpla a unui mini proiect.",
                    "Concept",
                    "Pot spune ce componente are quizul meu si de ce.",
                ),
                _objective(
                    "Sa potrivim idei invatate anterior cu rolul lor in proiect.",
                    "Practica",
                    "Pot spune unde folosesc variabile, liste, conditii si functii.",
                ),
                _objective(
                    "Sa pregatim proiectul pentru testare si prezentare.",
                    "Reflectie",
                    "Pot descrie ce as verifica inainte de a arata proiectul altora.",
                ),
            ],
            "practice": _practice(
                "Schema quizului este amestecata. Pune fiecare componenta la rolul potrivit.",
                "Potriveste fiecare piesa a proiectului cu descrierea ei.",
                "Excelent! Quizul robotului are o structura clara.",
                [
                    ("questions", "intrebari = ['Q1', 'Q2']"),
                    ("score", "scor = 0"),
                    ("check", "verifica_raspuns(...)"),
                    ("result", "afiseaza_rezultat(scor)"),
                ],
                [
                    ("Lista care tine toate intrebarile quizului.", "questions"),
                    ("Variabila care memoreaza punctajul.", "score"),
                    ("Functia care spune daca raspunsul este corect.", "check"),
                    ("Functia care afiseaza rezultatul final.", "result"),
                ],
            ),
            "tests": [
                _test(
                    "Ce combinatie descrie cel mai bine un mini proiect clar?",
                    "Componente simple, fiecare cu un rol clar",
                    [
                        "Cat mai multe idei puse fara plan",
                        "O singura functie foarte mare pentru tot",
                        "Fara testare si fara verificari",
                    ],
                    "Claritatea proiectului vine din impartirea responsabilitatilor si din ordinea buna a pasilor.",
                    "Descrie pe scurt cele mai importante doua componente ale quizului tau.",
                    "Cand fiecare parte face un lucru clar, proiectul este mai usor de inteles si de reparat.",
                ),
                _test(
                    "Unde ai folosi lista intr-un quiz?",
                    "Pentru a grupa intrebarile sau raspunsurile",
                    [
                        "Pentru a inlocui complet scorul",
                        "Pentru a desena fundalul",
                        "Doar pentru a inchide programul",
                    ],
                    "Listele sunt utile atunci cand ai mai multe elemente de acelasi tip, precum intrebari, raspunsuri sau categorii.",
                    "Gandeste-te la doua intrebari pentru quizul tau si noteaza-le ca elemente intr-o lista.",
                    "Folosirea listelor face quizul mai usor de extins cu intrebari noi.",
                ),
            ],
            "reflections": _default_reflections(
                "Code 9 · Mini proiect: Quiz Robot",
                "Ce ai imbunatati prima data dupa ce ai testa mini proiectul tau?",
            ),
        },
    ]
)


LESSON_BLUEPRINTS.extend(
    [
        {
            "slug": "junior-4-repetitii-care-ajuta",
            "legacy_slugs": ["junior-rf"],
            "title": "Junior 4 · Repetitii care ajuta",
            "date": date(2025, 10, 16),
            "age_bracket": "8-10",
            "difficulty": "beginner",
            "duration_minutes": 25,
            "xp_reward": 45,
            "excerpt": "Descoperi cum economisim timp atunci cand repetam acelasi pas de mai multe ori.",
            "theory_intro": "Uneori Robo face acelasi lucru de mai multe ori. In loc sa ii spui mereu acelasi pas, il inveti sa repete.",
            "content": _content(
                "Daca Robo trebuie sa faca trei salturi, nu are nevoie de trei planuri diferite. Poate repeta acelasi pas de trei ori.",
                "Repetitia este utila cand miscarea sau actiunea se repeta la fel. Asa economisim timp si evitam sa scriem sau sa spunem acelasi lucru de prea multe ori.",
                "Conteaza sa stii si cand se opreste repetitia. Un robot bun nu repeta la nesfarsit daca misiunea s-a terminat deja.",
            ),
            "theory_takeaways": [
                "Repetitia economiseste timp.",
                "O folosim cand acelasi pas se repeta.",
                "Trebuie sa stim si cand se termina.",
            ],
            "warmup_prompt": "Ce miscare i-ai cere lui Robo sa repete de trei ori intr-un joc?",
            "discussion_prompts": [
                "Unde vezi repetitii in dans, sport sau jocuri?",
                "Ce problema apare daca nu spui cand se opreste repetitia?",
                "Ce pas ai repeta tu intr-un labirint simplu?",
            ],
            "story_anchor": "Robo exerseaza aceeasi miscare pentru un spectacol si vrea sa nu se incurce la numaratoare.",
            "home_extension": "Inventeaza acasa o activitate cu trei repetitii: trei sarituri, trei batai din palme sau trei pasi inainte.",
            "collaboration_mode": "small_group",
            "content_tracks": ["Joc vizual", "Provocare bonus"],
            "fun_fact": "Multe dansuri si animatii se bazeaza pe miscari repetate.",
            "hero_theme": "play-loop",
            "hero_emoji": "🔄",
            "objectives": [
                _objective(
                    "Sa intelegem ideea de repetitie.",
                    "Concept",
                    "Pot recunoaste o situatie in care folosim acelasi pas de mai multe ori.",
                ),
                _objective(
                    "Sa alegem ce comanda se repeta.",
                    "Practica",
                    "Pot identifica pasul care trebuie repetat.",
                ),
                _objective(
                    "Sa observam si momentul de oprire.",
                    "Reflectie",
                    "Pot spune cand ar trebui sa se termine repetitia.",
                ),
            ],
            "practice": _practice(
                "Robo are miscari de repetat pentru spectacol. Potriveste piesele corecte.",
                "Asaza fiecare cartonas la explicatia potrivita.",
                "Super! Spectacolul lui Robo este pregatit.",
                [
                    ("repeat", "Repeta de 3 ori"),
                    ("jump", "Sari"),
                    ("stop", "Stop"),
                    ("count", "1, 2, 3"),
                ],
                [
                    ("Ideea ca aceeasi actiune se face de mai multe ori.", "repeat"),
                    ("Actiunea care se repeta in exemplu.", "jump"),
                    ("Semnalul care opreste repetitia.", "stop"),
                    (
                        "Numaratoarea care te ajuta sa verifici cate repetitii au fost.",
                        "count",
                    ),
                ],
            ),
            "tests": [
                _test(
                    "De ce este buna repetitia?",
                    "Pentru ca nu mai spui sau scrii de multe ori acelasi pas",
                    [
                        "Pentru ca schimba culoarea robotului",
                        "Pentru ca sterge tot ce ai facut inainte",
                        "Pentru ca functioneaza doar in jocuri",
                    ],
                    "Repetitia ne ajuta sa economisim timp si sa lucram mai ordonat.",
                    "Da un exemplu de actiune pe care ai repeta-o intr-un joc cu Robo.",
                    "Cand aceeasi actiune apare de multe ori, repetitia este o alegere buna.",
                ),
                _test(
                    "Ce mai trebuie sa stim pe langa pasul repetat?",
                    "Cand se opreste repetitia",
                    [
                        "Ce culoare are fundalul",
                        "Cum se numeste profesorul",
                        "Cate litere are cuvantul robot",
                    ],
                    "O repetitie buna are un inceput clar si un final clar.",
                    "Imagineaza-ti ca Robo face pasi pana la usa. Cand ar trebui sa se opreasca?",
                    "Fara o oprire, robotul ar continua sa repete si dupa ce misiunea s-a terminat.",
                ),
            ],
            "reflections": _default_reflections(
                "Junior 4 · Repetitii care ajuta",
                "Ce actiune ai pune pe repetitie intr-un joc facut de tine?",
            ),
        },
        {
            "slug": "code-6-repara-codul",
            "legacy_slugs": ["code-rf"],
            "title": "Code 6 · Repara codul",
            "date": date(2025, 10, 29),
            "age_bracket": "11-13",
            "difficulty": "intermediate",
            "duration_minutes": 35,
            "xp_reward": 60,
            "excerpt": "Inveti sa gasesti erorile pas cu pas, fara graba si fara sa schimbi totul dintr-o data.",
            "theory_intro": "Debugging inseamna sa gasesti si sa repari o greseala. Programatorii buni nu ghicesc la intamplare, ci verifica pas cu pas.",
            "content": _content(
                "Cand codul nu merge, primul lucru util este sa observi ce trebuia sa se intample si ce s-a intamplat de fapt.",
                "Apoi verifici pe rand: ai scris bine numele variabilelor, ai folosit corect parantezele, ai pus semnele potrivite, ai ales ordinea corecta?",
                "Repara o singura problema o data si testeaza din nou. Asa intelegi exact ce a fost gresit si nu creezi alte erori noi din graba.",
            ),
            "theory_takeaways": [
                "Compara rezultatul asteptat cu rezultatul obtinut.",
                "Verifica o singura problema pe rand.",
                "Testeaza dupa fiecare schimbare mica.",
            ],
            "warmup_prompt": "Ce faci mai intai cand robotul nu mai raspunde cum te astepti?",
            "discussion_prompts": [
                "De ce nu este bine sa schimbi tot codul deodata?",
                "Ce greseli simple apar des la inceput?",
                "Cum te ajuta mesajele afisate cu `print()` in debugging?",
            ],
            "story_anchor": "Byte a gasit un bug in consola robotului si vrea sa-l repare metodic, fara panica.",
            "home_extension": "Alege acasa un puzzle sau o problema simpla si incearca sa gasesti greseala pas cu pas, explicand fiecare verificare.",
            "collaboration_mode": "pairs",
            "content_tracks": ["Observa problema", "Repara pas cu pas"],
            "fun_fact": "Uneori cea mai mica greseala este doar o litera scrisa diferit intr-un nume de variabila.",
            "hero_theme": "amber-grid",
            "hero_emoji": "🛠️",
            "objectives": [
                _objective(
                    "Sa intelegem ce inseamna debugging.",
                    "Concept",
                    "Pot descrie debuggingul ca pe o cautare ordonata a unei greseli.",
                ),
                _objective(
                    "Sa potrivim tipuri de greseli cu explicatia lor.",
                    "Practica",
                    "Pot recunoaste o eroare simpla de scriere sau de logica.",
                ),
                _objective(
                    "Sa alegem o strategie calma de reparare.",
                    "Reflectie",
                    "Pot spune ce verific mai intai cand ceva nu merge.",
                ),
            ],
            "practice": _practice(
                "Consola robotului arata patru probleme. Potriveste fiecare indiciu cu tipul de eroare.",
                "Trage cartonasul la explicatia potrivita.",
                "Foarte bine! Bug-urile sunt acum sub control.",
                [
                    ("typo", "energii_robot"),
                    ("paren", "print('Start'"),
                    ("logic", "scor = scor - 1"),
                    ("order", "afisare inainte de calcul"),
                ],
                [
                    ("Exemplu de nume scris gresit.", "typo"),
                    ("Exemplu de paranteza lipsa.", "paren"),
                    ("Exemplu de regula care face altceva decat astepti.", "logic"),
                    ("Exemplu de pasi pusi in ordinea nepotrivita.", "order"),
                ],
            ),
            "tests": [
                _test(
                    "Care este un pas bun in debugging?",
                    "Schimbi o singura parte si testezi din nou",
                    [
                        "Stergi programul si il rescrii imediat din memorie",
                        "Schimbi tot codul in acelasi timp",
                        "Ignori rezultatul si continui",
                    ],
                    "Modificarile mici te ajuta sa vezi exact ce a reparat problema.",
                    "Descrie o situatie in care ai testa iar programul dupa o singura schimbare mica.",
                    "Daca modifici totul deodata, nu mai stii ce a rezolvat eroarea si ce a stricat altceva.",
                ),
                _test(
                    "Ce compari mai intai cand ceva nu merge?",
                    "Rezultatul asteptat cu rezultatul obtinut",
                    [
                        "Culoarea editorului cu tema desktopului",
                        "Numarul de litere din titlu cu numarul de linii",
                        "Data curenta cu data ultimei teme",
                    ],
                    "Debuggingul incepe cu observatia corecta: ce voiai sa se intample si ce vezi in realitate.",
                    "Imagineaza-ti ca robotul trebuia sa mearga inainte, dar s-a oprit. Ce ai nota mai intai?",
                    "Fara aceasta comparatie nu stii exact ce tip de problema cauti.",
                ),
            ],
            "reflections": _default_reflections(
                "Code 6 · Repara codul",
                "Ce tip de greseala ti se pare cel mai usor de gasit si de ce?",
            ),
        },
        {
            "slug": "junior-5-detectivii-de-buguri",
            "legacy_slugs": ["junior-entry-client2"],
            "title": "Junior 5 · Detectivii de bug-uri",
            "date": date(2025, 10, 23),
            "age_bracket": "8-10",
            "difficulty": "beginner",
            "duration_minutes": 25,
            "xp_reward": 45,
            "excerpt": "Inveti ca greselile nu sunt sperietoare: le observam, le cautam si le reparam pas cu pas.",
            "theory_intro": "Un bug este o mica greseala care incurca planul. Detectivii de bug-uri se uita atent si repara cate o problema o data.",
            "content": _content(
                "Daca Robo spune alt mesaj decat trebuia sau merge in directia gresita, nu inseamna ca tot programul este rau. Inseamna doar ca exista o mica greseala de gasit.",
                "Mai intai observam problema: ce asteptam sa faca si ce a facut de fapt. Apoi cautam calm unde s-a schimbat planul.",
                "Cand repari un singur lucru o data, vezi imediat daca ai gasit bug-ul. Asa prinzi incredere si inveti mai repede.",
            ),
            "theory_takeaways": [
                "Bug-ul este o greseala mica in program.",
                "Ne uitam mai intai la ce a mers diferit.",
                "Reparam cate o problema o data.",
            ],
            "warmup_prompt": "Cum ti-ai da seama ca Robo a facut altceva decat ce ii cerusei?",
            "discussion_prompts": [
                "De ce nu trebuie sa ne suparam cand apare un bug?",
                "Ce observi mai intai cand ceva nu merge bine?",
                "Cum te ajuta rabdarea atunci cand repari o greseala?",
            ],
            "story_anchor": "Pixel a pus lupa de detectiv pe consola lui Robo si cauta prima greseala mica.",
            "home_extension": "Ia acasa un joc de puzzle sau un desen cu diferente si povesteste ce ai observat pas cu pas pana ai gasit problema.",
            "collaboration_mode": "pairs",
            "content_tracks": ["Observa", "Repara"],
            "fun_fact": "Chiar si programatorii mari gasesc zilnic bug-uri si le rezolva pe rand.",
            "hero_theme": "gold-lab",
            "hero_emoji": "🔍",
            "objectives": [
                _objective(
                    "Sa intelegem ce este un bug.",
                    "Concept",
                    "Pot explica bug-ul ca pe o mica greseala in plan.",
                ),
                _objective(
                    "Sa observam diferenta dintre ce voiam si ce s-a intamplat.",
                    "Practica",
                    "Pot spune ce a mers altfel decat ma asteptam.",
                ),
                _objective(
                    "Sa repar ceva simplu cu calm.",
                    "Reflectie",
                    "Pot alege un singur lucru de verificat mai intai.",
                ),
            ],
            "practice": _practice(
                "Avem patru semne ca ceva nu merge bine. Potriveste fiecare indiciu cu problema lui.",
                "Trage cartonasul la explicatia corecta.",
                "Bravo! Ai rezolvat cazul detectivilor de bug-uri.",
                [
                    ("wrong", "Mesaj gresit"),
                    ("missing", "Pas lipsa"),
                    ("order", "Ordine gresita"),
                    ("value", "Scor gresit"),
                ],
                [
                    ("Problema in care apare alt text decat te asteptai.", "wrong"),
                    ("Problema in care lipseste un pas important.", "missing"),
                    ("Problema in care pasii buni sunt asezati prost.", "order"),
                    ("Problema in care numarul afisat nu este cel bun.", "value"),
                ],
            ),
            "tests": [
                _test(
                    "Ce este un bug?",
                    "O greseala mica intr-un program",
                    [
                        "Un tip de baterie pentru robot",
                        "Un premiu pentru cel mai bun cod",
                        "Un nume nou pentru calculator",
                    ],
                    "Bug-ul este diferenta dintre planul tau si ce face cu adevarat programul.",
                    "Spune un exemplu de bug pe care l-ar putea face Robo intr-un joc.",
                    "Cand observi problema clar, esti deja mai aproape de reparatie.",
                ),
                _test(
                    "Ce faci bine atunci cand vrei sa repari o greseala?",
                    "Verifici pe rand cate un lucru",
                    [
                        "Schimbi totul deodata",
                        "Ignori problema si continui",
                        "Stergi numele tuturor variabilelor",
                    ],
                    "Pasi mici si atenti inseamna reparatii mai bune.",
                    "Ce ai verifica mai intai daca scorul afisat nu este bun?",
                    "Cand repari cate o problema o data, intelegi ce s-a schimbat.",
                ),
            ],
            "reflections": _default_reflections(
                "Junior 5 · Detectivii de bug-uri",
                "Cum te-ai simtit cand ai gasit o greseala si ai reparat-o?",
            ),
        },
    ]
)


LESSON_BLUEPRINTS.extend(
    [
        {
            "slug": "code-3-decizii-cu-if-si-else",
            "legacy_slugs": ["code-entry-debug"],
            "title": "Code 3 · Decizii cu if si else",
            "date": date(2025, 10, 8),
            "age_bracket": "11-13",
            "difficulty": "beginner",
            "duration_minutes": 35,
            "xp_reward": 55,
            "excerpt": "Inveti cum ia un program decizii folosind conditii simple si ramuri clare.",
            "theory_intro": "Un program nu alege la intamplare. Cu `if` si `else`, el verifica o conditie si merge pe drumul potrivit.",
            "content": _content(
                "In viata reala faci des alegeri: daca afara ploua, iei umbrela; altfel pleci direct. Programarea foloseste aceeasi logica.",
                "In Python, `if` verifica o conditie. Daca ea este adevarata, se executa un set de pasi. Cu `else`, pregatesti ce se intampla in celalalt caz.",
                "Conditiile bune sunt simple si usor de citit. Cand folosesti variabile cu nume clare, intelegi repede si de ce a ales programul o anumita ramura.",
            ),
            "theory_takeaways": [
                "`if` verifica o conditie.",
                "`else` defineste alternativa.",
                "Conditiile clare fac programul mai usor de explicat.",
            ],
            "warmup_prompt": "Daca robotul are baterie mica, ce ar trebui sa faca inainte sa plece din baza?",
            "discussion_prompts": [
                "Ce conditii folosesti si tu in viata de zi cu zi fara sa te gandesti?",
                "Cum ai denumi o variabila care spune daca usa este deschisa?",
                "Cand este util sa ai si ramura `else`, nu doar `if`?",
            ],
            "story_anchor": "Byte programeaza poarta laboratorului: daca accesul este permis, usa se deschide; altfel ramane blocata.",
            "home_extension": "Inventeaza acasa trei reguli de tip daca/altfel pentru un joc de masa sau pentru o rutina zilnica.",
            "collaboration_mode": "pairs",
            "content_tracks": ["Teorie + exemplu", "Provocare de logica"],
            "fun_fact": "Multe jocuri decid cu `if` daca ai castigat, ai pierdut sau treci la nivelul urmator.",
            "hero_theme": "ember-grid",
            "hero_emoji": "🚦",
            "objectives": [
                _objective(
                    "Sa intelegem logica unei conditii.",
                    "Concept",
                    "Pot spune ce se intampla cand o conditie este adevarata sau falsa.",
                ),
                _objective(
                    "Sa potrivim exemple de conditii cu rezultatul lor.",
                    "Practica",
                    "Pot alege ramura corecta intr-un scenariu simplu.",
                ),
                _objective(
                    "Sa formulam o regula de tip `if/else` cu cuvintele noastre.",
                    "Reflectie",
                    "Pot inventa o conditie pentru un robot sau pentru un joc.",
                ),
            ],
            "practice": _practice(
                "Sistemul de acces al laboratorului are regulile amestecate. Pune fiecare piesa la locul ei.",
                "Potriveste codul cu descrierea corecta.",
                "Poarta robotului functioneaza acum perfect.",
                [
                    ("if", "if energie > 20:"),
                    ("else", "else:"),
                    ("true", "porneste_misiunea()"),
                    ("false", "mergi_la_incarcare()"),
                ],
                [
                    ("Linia care verifica regula.", "if"),
                    ("Linia care pregateste alternativa.", "else"),
                    ("Actiunea care se executa daca regula este adevarata.", "true"),
                    ("Actiunea care se executa daca regula este falsa.", "false"),
                ],
            ),
            "tests": [
                _test(
                    "Cand se executa ramura de sub `else`?",
                    "Cand conditia din `if` nu este adevarata",
                    [
                        "La fiecare rulare, indiferent de conditie",
                        "Doar cand exista doua variabile",
                        "Numai dupa o bucla `for`",
                    ],
                    "`else` este planul de rezerva al programului.",
                    "Descrie o situatie in care robotul ar merge la incarcare in loc sa porneasca misiunea.",
                    "Programul are nevoie de un raspuns si pentru cazul in care regula nu se indeplineste.",
                ),
                _test(
                    "Ce expresie este o conditie buna pentru nivelul bateriei?",
                    "`energie > 20`",
                    ["`print('20')`", "`energie = 20`", "`for energie in range(20)`"],
                    "O conditie compara sau verifica o stare, nu afiseaza si nu repeta singura ceva.",
                    "Gandeste-te la o regula simpla pentru a deschide o usa automata.",
                    "Conditiile trebuie sa poata fi evaluate ca adevarate sau false.",
                ),
            ],
            "reflections": _default_reflections(
                "Code 3 · Decizii cu if si else",
                "Ce conditie ai adauga intr-un joc creat de tine?",
            ),
        },
        {
            "slug": "junior-3-alegeri-cu-daca",
            "legacy_slugs": ["junior-entry-client"],
            "title": "Junior 3 · Alegeri cu daca",
            "date": date(2025, 10, 9),
            "age_bracket": "8-10",
            "difficulty": "beginner",
            "duration_minutes": 25,
            "xp_reward": 45,
            "excerpt": "Inveti ca un robot poate alege intre doua drumuri atunci cand verifica o regula simpla.",
            "theory_intro": "Uneori Robo trebuie sa aleaga. Daca drumul este liber, merge inainte. Daca nu, cauta alta solutie.",
            "content": _content(
                "Alegerile apar peste tot: daca ploua, iei pelerina; daca nu ploua, iei sapca. Si robotii gandesc la fel.",
                "O conditie este o intrebare scurta care are doua raspunsuri posibile: da sau nu. Dupa raspuns, alegem pasul potrivit.",
                "Cand explici clar regula, robotul nu se incurca. El stie ce sa faca in fiecare situatie.",
            ),
            "theory_takeaways": [
                "O conditie este o intrebare cu raspuns da sau nu.",
                "Raspunsul decide urmatorul pas.",
                "Regulile simple sunt usor de urmat.",
            ],
            "warmup_prompt": "Daca vezi un obstacol pe drum, ce ar trebui sa faca Robo?",
            "discussion_prompts": [
                "Ce reguli de tip daca folosesti la scoala sau acasa?",
                "Cum arata un exemplu de alegere buna pentru un robot?",
                "De ce este util sa pregatesti si varianta de rezerva?",
            ],
            "story_anchor": "Robo patruleaza prin laborator si trebuie sa aleaga repede drumul corect.",
            "home_extension": "Inventeaza acasa doua reguli de tip daca pentru un robot care strange jucarii sau uda flori.",
            "collaboration_mode": "pairs",
            "content_tracks": ["Exemplu vizual", "Provocare bonus"],
            "fun_fact": "Semaforul este un bun exemplu de sistem care ia decizii pe baza unor reguli.",
            "hero_theme": "sunset-circuit",
            "hero_emoji": "🚥",
            "objectives": [
                _objective(
                    "Sa intelegem ideea de alegere dupa o regula.",
                    "Concept",
                    "Pot spune ce inseamna o intrebare cu raspuns da sau nu.",
                ),
                _objective(
                    "Sa potrivim reguli simple cu actiuni potrivite.",
                    "Practica",
                    "Pot alege ce face Robo dupa regula data.",
                ),
                _objective(
                    "Sa inventam o regula noua pentru un joc sau un robot.",
                    "Reflectie",
                    "Pot formula o regula scurta de tip daca.",
                ),
            ],
            "practice": _practice(
                "Robo are nevoie de reguli clare. Ajuta-l sa le puna in ordine.",
                "Potriveste fiecare regula cu actiunea corecta.",
                "Minunat! Robo ia acum deciziile potrivite.",
                [
                    ("green", "Daca semaforul este verde"),
                    ("wall", "Daca apare un perete"),
                    ("go", "Mergi inainte"),
                    ("turn", "Intoarce-te"),
                ],
                [
                    ("Regula care spune ca drumul este liber.", "green"),
                    ("Regula care anunta un obstacol.", "wall"),
                    ("Actiunea pentru drumul liber.", "go"),
                    ("Actiunea pentru obstacol.", "turn"),
                ],
            ),
            "tests": [
                _test(
                    "Ce este o conditie?",
                    "O regula care poate avea raspuns da sau nu",
                    [
                        "Un nume pentru un robot",
                        "O lista lunga de obiecte",
                        "Un buton care porneste calculatorul",
                    ],
                    "Conditiile ne ajuta sa alegem intre doua variante simple.",
                    "Da un exemplu de intrebare cu raspuns da sau nu pentru Robo.",
                    "Cand avem o regula clara, putem decide repede ce urmeaza.",
                ),
                _test(
                    "Ce face Robo daca apare un obstacol si regula spune sa ocoleasca?",
                    "Alege drumul de rezerva",
                    [
                        "Se opreste pentru totdeauna",
                        "Merge mai repede inainte",
                        "Uita complet de regula",
                    ],
                    "Alegerea corecta depinde de raspunsul la conditie.",
                    "Imagineaza-ti un drum blocat. Ce alta actiune ai pregati pentru Robo?",
                    "Scopul unei reguli este sa-i spuna robotului ce face in fiecare situatie.",
                ),
            ],
            "reflections": _default_reflections(
                "Junior 3 · Alegeri cu daca",
                "Ce regula noua ai crea pentru Robo daca ar avea grija de animale robotice?",
            ),
        },
        {
            "slug": "nivel-2-aventuri-cu-buclele",
            "legacy_slugs": [],
            "title": "Code 4 · Aventuri cu buclele",
            "date": date(2025, 10, 15),
            "age_bracket": "11-13",
            "difficulty": "intermediate",
            "duration_minutes": 35,
            "xp_reward": 55,
            "excerpt": "Antrenezi un robot dansator sa repete miscari corecte folosind bucle `for` si `while`.",
            "theory_intro": "Buclele sunt ritmul programarii. Ele repeta pasii de cate ori este nevoie fara sa rescrii totul.",
            "content": _content(
                "Daca un robot trebuie sa faca aceeasi miscare de cinci ori, nu are sens sa scrii de cinci ori aceeasi instructiune. O bucla rezolva exact aceasta problema.",
                "Cu `for`, repeti un numar fix de pasi sau parcurgi o colectie. Cu `while`, continui cat timp o conditie ramane adevarata.",
                "Cele mai bune bucle au o conditie clara de oprire. Altfel, robotul poate ramane blocat intr-o repetitie fara sfarsit.",
            ),
            "theory_takeaways": [
                "`for` este buna pentru un numar fix de repetitii.",
                "`while` continua cat timp regula ramane adevarata.",
                "Orice bucla trebuie sa aiba o iesire clara.",
            ],
            "warmup_prompt": "Ce activitate ai repeta automat daca ai avea un robot ajutor?",
            "discussion_prompts": [
                "Cand ai prefera `for` in loc de `while`?",
                "Ce semn iti arata ca o bucla se poate opri?",
                "Unde vezi repetitii utile in jocuri sau aplicatii?",
            ],
            "story_anchor": "Loopster, robotul dansator, isi repeta coregrafia doar daca primeste reguli bune.",
            "home_extension": "Inventeaza acasa un exemplu de bucla pentru o rutina simpla: spalat pe dinti, numarat pasi sau antrenament sportiv.",
            "collaboration_mode": "pairs",
            "content_tracks": ["Teorie + exemplu", "Misiune de repetitie"],
            "fun_fact": "Animatiile din jocuri folosesc des bucle pentru a repeta miscari pana cand se schimba starea personajului.",
            "hero_theme": "pulse-grid",
            "hero_emoji": "🔁",
            "objectives": [
                _objective(
                    "Sa deosebim `for` de `while`.",
                    "Concept",
                    "Pot spune cand folosesc fiecare tip de bucla.",
                ),
                _objective(
                    "Sa potrivim exemple de bucle cu scenariul potrivit.",
                    "Practica",
                    "Pot alege bucla potrivita pentru o repetitie simpla.",
                ),
                _objective(
                    "Sa observam cum se opreste o bucla.",
                    "Reflectie",
                    "Pot explica de ce o bucla infinita este o problema.",
                ),
            ],
            "practice": _practice(
                "Loopster, robotul dansator, are nevoie de coregrafia corecta pentru fiecare tip de bucla.",
                "Potriveste fiecare cartonas cu descrierea potrivita.",
                "Perfect! Loopster danseaza impecabil datorita tie.",
                [
                    ("forloop", "for pas in range(4)"),
                    ("whileloop", "while energie > 0"),
                    ("break", "break"),
                    ("continue", "continue"),
                ],
                [
                    ("Repeta un numar fix de miscari.", "forloop"),
                    ("Continua cat timp robotul mai are energie.", "whileloop"),
                    ("Opreste bucla imediat.", "break"),
                    ("Sari peste pasul curent si mergi la urmatorul.", "continue"),
                ],
            ),
            "tests": [
                _test(
                    "Ce face `for i in range(5):`?",
                    "Ruleaza instructiunile din interior de cinci ori",
                    [
                        "Ruleaza doar prima instructiune",
                        "Porneste un cronometru de cinci secunde",
                        "Creeaza cinci variabile noi",
                    ],
                    "`range(5)` ofera cinci pasi numerotati de la 0 la 4.",
                    "Noteaza un exemplu real unde ai repeta un pas de cinci ori.",
                    "Buclele `for` sunt utile cand stii dinainte de cate ori vrei sa repeti ceva.",
                ),
                _test(
                    "Cum se poate opri o bucla `while`?",
                    "Cand conditia devine falsa sau folosim `break`",
                    [
                        "Se opreste singura dupa prima rulare",
                        "Se opreste doar daca stergi cuvantul `while`",
                        "Nu se poate opri niciodata",
                    ],
                    "Conditia trebuie sa se schimbe in timp ca bucla sa poata iesi.",
                    "Descrie o situatie in care ai folosi `break` intr-un joc simplu.",
                    "Daca starea nu se actualizeaza, bucla poate continua la nesfarsit.",
                ),
            ],
            "reflections": _default_reflections(
                "Code 4 · Aventuri cu buclele",
                "Unde ai folosi o repetitie intr-un proiect de joc sau de robot?",
            ),
        },
        {
            "slug": "code-5-liste-care-organizeaza",
            "legacy_slugs": ["code-entry-client"],
            "title": "Code 5 · Liste care organizeaza",
            "date": date(2025, 10, 22),
            "age_bracket": "11-13",
            "difficulty": "intermediate",
            "duration_minutes": 35,
            "xp_reward": 60,
            "excerpt": "Inveti sa grupezi obiecte intr-o lista si sa parcurgi colectiile mai usor.",
            "theory_intro": "Cand ai mai multe valori de acelasi fel, o lista le tine impreuna si iti permite sa le folosesti ordonat.",
            "content": _content(
                "Daca un joc are mai multi jucatori, mai multe punctaje sau mai multe obiecte, ar fi greu sa creezi cate o variabila separata pentru fiecare.",
                "O lista pastreaza valorile la un loc: `culori = ['rosu', 'verde', 'albastru']`. Apoi poti lua elemente din lista sau poti parcurge toate valorile cu o bucla.",
                "Listele te ajuta sa scrii programe mai scurte si mai usor de extins. Cand apare un element nou, il adaugi in colectie fara sa schimbi tot codul.",
            ),
            "theory_takeaways": [
                "O lista grupeaza mai multe valori intr-un singur loc.",
                "Elementele din lista pot fi parcurse cu o bucla.",
                "Listele te ajuta sa organizezi date similare.",
            ],
            "warmup_prompt": "Ce ai pune intr-o lista daca ai construi un joc cu trei niveluri sau trei personaje?",
            "discussion_prompts": [
                "Cand este mai bine sa folosesti o lista decat mai multe variabile separate?",
                "Ce fel de elemente ai pastra intr-o lista pentru un quiz?",
                "Cum te ajuta o lista cand proiectul tau creste?",
            ],
            "story_anchor": "Byte aduna toate uneltele robotului intr-un inventar si vrea sa le gestioneze fara haos.",
            "home_extension": "Fa acasa o lista cu cinci obiecte pe care le-ai folosi intr-o misiune spatiala sau intr-un joc de aventura.",
            "collaboration_mode": "pairs",
            "content_tracks": ["Teorie + exemple", "Provocare de organizare"],
            "fun_fact": "Multe jocuri folosesc liste pentru inventar, scoruri si meniuri.",
            "hero_theme": "teal-lab",
            "hero_emoji": "📦",
            "objectives": [
                _objective(
                    "Sa intelegem rolul unei liste.",
                    "Concept",
                    "Pot explica de ce lista este utila pentru date asemanatoare.",
                ),
                _objective(
                    "Sa potrivim exemple de liste cu situatiile potrivite.",
                    "Practica",
                    "Pot recunoaste o colectie care ar trebui pusa intr-o lista.",
                ),
                _objective(
                    "Sa alegem ce date am grupa intr-un proiect propriu.",
                    "Reflectie",
                    "Pot propune o lista pentru jocul sau aplicatia mea.",
                ),
            ],
            "practice": _practice(
                "Inventarul robotului este imprastiat. Potriveste fiecare idee cu rolul potrivit.",
                "Trage fiecare cartonas unde crezi ca se potriveste.",
                "Inventarul este acum bine organizat.",
                [
                    ("list", "['cheie', 'harta', 'baterie']"),
                    ("item", "'harta'"),
                    ("loop", "for obiect in inventar"),
                    ("scorelist", "[120, 95, 87]"),
                ],
                [
                    ("Exemplu de lista de obiecte.", "list"),
                    ("Un singur element din inventar.", "item"),
                    ("Parcurgerea tuturor elementelor dintr-o lista.", "loop"),
                    ("Lista potrivita pentru punctaje.", "scorelist"),
                ],
            ),
            "tests": [
                _test(
                    "Cand este utila o lista?",
                    "Cand vrei sa pastrezi mai multe valori asemanatoare la un loc",
                    [
                        "Cand vrei sa afisezi un singur mesaj o data",
                        "Cand ai nevoie doar de o conditie `if`",
                        "Cand inchizi programul",
                    ],
                    "Listele sunt bune pentru colectii de valori de acelasi tip sau din acelasi grup.",
                    "Scrie trei elemente pe care le-ai pune intr-o lista pentru un joc.",
                    "O lista reduce numarul de variabile separate si te ajuta sa organizezi datele mai clar.",
                ),
                _test(
                    "Ce face `for nume in jucatori`?",
                    "Parcurge fiecare element din lista `jucatori`",
                    [
                        "Creeaza automat o lista noua",
                        "Sterge ultimul jucator",
                        "Compara doua liste intre ele",
                    ],
                    "Buclele si listele merg bine impreuna, pentru ca poti procesa fiecare element pe rand.",
                    "Imagineaza-ti o lista cu trei prieteni. Ce mesaj ai afisa pentru fiecare?",
                    "Aceasta bucla ia pe rand fiecare valoare din lista si o foloseste in blocul de cod.",
                ),
            ],
            "reflections": _default_reflections(
                "Code 5 · Liste care organizeaza",
                "Ce lista ai folosi prima intr-un joc, intr-un quiz sau intr-un robot virtual?",
            ),
        },
    ]
)


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


def curate_python_lessons(apps, schema_editor):
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

    subject = Subject.objects.filter(name="Coding Quest").order_by("id").first()
    if subject is None:
        subject = Subject.objects.create(
            name="Coding Quest",
            description="Lectii de programare explicate clar pentru copii, cu trasee vizuale 8-10 ani si cod real pentru 11+.",
        )
    subject.description = "Lectii de programare explicate clar pentru copii, cu trasee vizuale 8-10 ani si cod real pentru 11+."
    subject.save(update_fields=["description"])

    for blueprint in LESSON_BLUEPRINTS:
        lesson = Lesson.objects.filter(slug=blueprint["slug"]).first()
        if lesson is None:
            for legacy_slug in blueprint.get("legacy_slugs", []):
                lesson = Lesson.objects.filter(slug=legacy_slug).first()
                if lesson is not None:
                    break

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
        ("estudy", "0058_seed_python_extras"),
    ]

    operations = [
        migrations.RunPython(curate_python_lessons, migrations.RunPython.noop),
    ]
