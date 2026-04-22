from __future__ import annotations

LESSON_GUIDES: dict[str, dict[str, object]] = {}


LESSON_GUIDES["code-1-bun-venit-in-python"] = {
    "examples_text": "Uita-te la exemple ca la pasi pe care robotul ii urmeaza in ordine. Fiecare linie are un rol clar: porneste, afiseaza, verifica.",
    "example_cards": [
        {
            "title": "Primul mesaj",
            "code": "print('Salut, echipa UNITEX!')",
            "note": "Programul porneste si afiseaza exact mesajul pe care l-ai scris.",
        },
        {
            "title": "Doi pasi, doua rezultate",
            "code": "print('Pornim robotul')\nprint('Verificam consola')",
            "note": "Python executa prima linie, apoi a doua. Ordinea nu este optionala.",
        },
        {
            "title": "Mesaj pentru testare",
            "code": "print('Totul functioneaza corect')",
            "note": "Afisarea te ajuta sa vezi imediat daca programul ajunge unde te astepti.",
        },
    ],
    "use_cases": [
        "cand vrei sa verifici rapid daca programul a pornit corect",
        "cand explici unui coleg ce face fiecare pas din cod",
        "cand ai nevoie de un mesaj clar pentru utilizator",
    ],
    "vocabulary": [
        "program: lista de instructiuni pe care calculatorul le executa",
        "consola: zona unde vezi mesajele si rezultatele programului",
        "print: comanda care afiseaza text sau valori pe ecran",
    ],
    "common_mistakes": [
        "scrii un mesaj fara ghilimele si Python nu il mai intelege ca text",
        "te astepti ca programul sa ghiceasca ordinea pasilor",
        "nu rulezi din nou codul dupa o schimbare mica",
    ],
    "mini_project": {
        "title": "Mini-proiect: Panou de pornire pentru Robo",
        "prompt": "Creeaza trei mesaje pe care Robo le afiseaza cand incepe o misiune.",
        "steps": [
            "afiseaza un mesaj de salut",
            "afiseaza numele misiunii",
            "afiseaza o regula simpla pentru jucator",
        ],
        "outcome": "La final ai o mini secventa clara de pornire, utila in orice joc sau aplicatie.",
    },
    "guided_code": "print('Salut!')\nprint('Misiunea incepe acum.')\nprint('Primul pas: verifica ecranul.')",
    "practice_context": "In practica nu cauti raspunsul la intamplare. Te uiti ce afiseaza fiecare linie si explici rolul ei.",
    "recap_questions": [
        "Ce se intampla prima data cand rulezi programul?",
        "Cum iti dai seama ca ordinea liniilor este buna?",
        "Ce mesaj util ai afisa la pornirea unui joc?",
    ],
}

LESSON_GUIDES["nivel-1-prieteni-cu-variabilele"] = {
    "examples_text": "Gandeste variabilele ca pe niste cutii etichetate. Daca eticheta este buna, stii imediat ce pastreaza fiecare cutie.",
    "example_cards": [
        {
            "title": "Numele jucatorului",
            "code": "nume_jucator = 'Mara'",
            "note": "Variabila tine minte numele si il poti folosi in multe locuri din joc.",
        },
        {
            "title": "Scor care creste",
            "code": "scor = 3\nscor = scor + 1",
            "note": "Valoarea din cutie se poate schimba atunci cand jucatorul castiga puncte.",
        },
        {
            "title": "Mesaj personalizat",
            "code": "mesaj = 'Bun venit, Mara!'",
            "note": "Variabila te ajuta sa pregatesti mesaje diferite pentru fiecare copil.",
        },
    ],
    "use_cases": [
        "cand vrei sa tii minte scorul intr-un joc",
        "cand programul trebuie sa afiseze numele copilului",
        "cand personajul are vieti, stele sau energie",
    ],
    "vocabulary": [
        "variabila: cutie cu nume care pastreaza o informatie",
        "valoare: lucrul pe care il pui in cutie",
        "actualizare: momentul in care schimbi ce se afla in variabila",
    ],
    "common_mistakes": [
        "alegi un nume prea vag, cum ar fi x sau data1",
        "uita ca valoarea se poate schimba pe parcursul jocului",
        "confunda numele variabilei cu mesajul pe care il afiseaza",
    ],
    "mini_project": {
        "title": "Mini-proiect: Fisa eroului",
        "prompt": "Imagineaza un personaj si pregateste trei variabile pentru el.",
        "steps": [
            "alege un nume pentru erou",
            "alege un scor de inceput",
            "alege un numar de vieti",
        ],
        "outcome": "Ai baza unui joc simplu in care personajul poate castiga puncte si pierde vieti.",
    },
    "practice_context": "Cand potrivesti piesele, verifica mereu daca vezi un nume de cutie, o valoare sau o schimbare de scor.",
    "recap_questions": [
        "Ce informatie ai salva prima intr-un joc creat de tine?",
        "Cum iti dai seama daca o variabila are nume bun?",
        "Cand ai schimba valoarea unei variabile?",
    ],
}

LESSON_GUIDES["code-2-variabile-si-date"] = {
    "examples_text": "Acum nu doar creezi variabile, ci alegi si tipul potrivit de date pentru fiecare nevoie reala din proiect.",
    "example_cards": [
        {
            "title": "Text pentru mesaj",
            "code": "mesaj_start = 'Misiune pornita'",
            "note": "Textul este bun pentru titluri, instructiuni si nume.",
        },
        {
            "title": "Numar pentru scor",
            "code": "scor = 120",
            "note": "Scorul este numeric pentru ca vrei sa aduni, sa scazi sau sa compari.",
        },
        {
            "title": "Stare pentru acces",
            "code": "robot_activ = True",
            "note": "Uneori ai nevoie doar sa stii daca ceva este pornit sau oprit.",
        },
    ],
    "use_cases": [
        "cand proiectul tine minte cine joaca si ce a facut",
        "cand vrei sa alegi intre text, numar si stare simpla",
        "cand organizezi datele unui robot, joc sau quiz",
    ],
    "vocabulary": [
        "tip de date: felul informatiei pe care o pastrezi",
        "string: text scris intre ghilimele",
        "valoare booleana: raspuns simplu de tip da sau nu",
    ],
    "common_mistakes": [
        "folosesti text pentru ceva ce vrei sa calculezi ca numar",
        "alegi nume foarte asemanatoare si le confunzi usor",
        "nu te intrebi la ce va folosi variabila mai departe",
    ],
    "mini_project": {
        "title": "Mini-proiect: Panou de control",
        "prompt": "Pregateste datele esentiale pentru consola unui robot.",
        "steps": [
            "creeaza o variabila text pentru numele robotului",
            "creeaza o variabila numerica pentru energie",
            "creeaza o variabila de stare pentru misiune activa",
        ],
        "outcome": "Obtii un model de date simplu, clar si util pentru proiecte mai mari.",
    },
    "guided_code": "nume_robot = 'Nova-7'\nenergie = 45\nrobot_activ = True\nprint(nume_robot)\nprint(energie)\nprint(robot_activ)",
    "practice_context": "In practica, intreaba-te la fiecare cartonas: este text, numar sau stare? Dupa aceea devine mult mai usor sa alegi raspunsul corect.",
    "recap_questions": [
        "De ce are scorul nevoie de un numar, nu de un text?",
        "Ce nume bun ai alege pentru energia robotului?",
        "Cand ti-ar folosi o variabila de tip adevarat/fals?",
    ],
}

LESSON_GUIDES["junior-2-comenzi-pentru-robo"] = {
    "examples_text": "Un algoritm bun este ca o reteta usoara: incepi, urmezi pasii in ordine si ajungi la rezultat fara sa ghicesti nimic.",
    "example_cards": [
        {
            "title": "Drumul pana la usa",
            "code": "Porneste -> Mergi inainte -> Opreste-te",
            "note": "Pasii sunt putini, clari si usor de urmat.",
        },
        {
            "title": "Virajul corect",
            "code": "Porneste -> Intoarce la dreapta -> Mergi inainte",
            "note": "Daca schimbi ordinea, robotul ajunge in alt loc.",
        },
        {
            "title": "Plan pentru ghiozdan",
            "code": "Ia caietul -> Pune creionul -> Inchide ghiozdanul",
            "note": "Si lucrurile de zi cu zi pot fi explicate ca algoritmi.",
        },
    ],
    "use_cases": [
        "cand explici unui robot cum sa se miste",
        "cand scrii pasi pentru o activitate de clasa sau de acasa",
        "cand vrei sa vezi unde s-a stricat un plan",
    ],
    "vocabulary": [
        "algoritm: plan cu pasi pusi in ordine",
        "instructiune: un singur pas din plan",
        "ordine: aranjarea corecta a pasilor",
    ],
    "common_mistakes": [
        "sari peste un pas important",
        "pui un pas bun, dar prea devreme sau prea tarziu",
        "folosesti pasi prea vagi, pe care robotul nu ii poate intelege",
    ],
    "mini_project": {
        "title": "Mini-proiect: Traseu prin clasa",
        "prompt": "Scrie trei-patru pasi clari prin care Robo ajunge de la usa la tabla.",
        "steps": [
            "alege punctul de start",
            "spune directia pentru fiecare pas",
            "opreste traseul cand ajunge la destinatie",
        ],
        "outcome": "Ai un algoritm simplu pe care il poti verifica pas cu pas.",
    },
    "practice_context": "Cand asezi comenzile, gandeste-te daca robotul chiar ar putea urma fiecare pas fara sa fie confuz.",
    "recap_questions": [
        "Ce se strica mai repede: un pas gresit sau ordinea gresita?",
        "Unde ai folosi un algoritm in viata de zi cu zi?",
        "Cum i-ai explica unui coleg de ce pasii trebuie sa fie clari?",
    ],
}

LESSON_GUIDES["code-3-decizii-cu-if-si-else"] = {
    "examples_text": "Regulile de tip if/else sunt utile ori de cate ori programul trebuie sa aleaga intre doua drumuri clare.",
    "example_cards": [
        {
            "title": "Verificam bateria",
            "code": "if energie > 20:\n    porneste_misiunea()\nelse:\n    mergi_la_incarcare()",
            "note": "Programul nu ghiceste. El compara energia si alege actiunea potrivita.",
        },
        {
            "title": "Acces permis sau blocat",
            "code": "if cod_corect:\n    deschide_usa()\nelse:\n    afiseaza_eroare()",
            "note": "Conditia decide daca utilizatorul intra sau primeste feedback.",
        },
        {
            "title": "Premiu pentru scor mare",
            "code": "if scor >= 100:\n    print('Ai castigat badge-ul!')\nelse:\n    print('Mai incearca o runda.')",
            "note": "Aceeasi idee merge in jocuri, quizuri si sisteme de punctaj.",
        },
    ],
    "use_cases": [
        "cand un robot decide daca pleaca sau ramane la incarcare",
        "cand un quiz verifica daca raspunsul este corect",
        "cand o aplicatie trebuie sa afiseze doua rezultate diferite",
    ],
    "vocabulary": [
        "conditie: regula pe care o verifici",
        "ramura: unul dintre drumurile posibile din program",
        "comparatie: verificare intre doua valori sau stari",
    ],
    "common_mistakes": [
        "scrii o regula neclara si nu mai stii ce verifica",
        "uita sa definesti si varianta de rezerva din else",
        "confunda o comparatie cu o simpla atribuire de valoare",
    ],
    "mini_project": {
        "title": "Mini-proiect: Poarta inteligenta",
        "prompt": "Construieste o regula pentru o usa care se deschide doar cand robotul are acces.",
        "steps": [
            "alege variabila sau regula pe care o verifici",
            "scrie ce se intampla daca regula este adevarata",
            "scrie ce se intampla daca regula este falsa",
        ],
        "outcome": "Obtii un model simplu de decizie util in jocuri, roboti si aplicatii reale.",
    },
    "guided_code": "energie = 18\nif energie > 20:\n    print('Pornim misiunea')\nelse:\n    print('Mergem la incarcare')",
    "practice_context": "Nu invata pe de rost doar sintaxa. Gandeste-te mereu ce regula din viata reala traduci in cod.",
    "recap_questions": [
        "Ce regula simpla ai scrie pentru o usa automata?",
        "De ce este util sa ai si else, nu doar if?",
        "Cum iti dai seama daca o conditie este formulata clar?",
    ],
}

LESSON_GUIDES["junior-3-alegeri-cu-daca"] = {
    "examples_text": "Alegerile de tip daca apar peste tot: la semafor, la jocuri, in rutina zilnica. Important este sa vezi regula si ce urmeaza dupa ea.",
    "example_cards": [
        {
            "title": "Drum liber",
            "code": "Daca drumul e liber -> mergi inainte",
            "note": "Raspunsul la intrebare ii spune lui Robo ce face mai departe.",
        },
        {
            "title": "Obstacol pe traseu",
            "code": "Daca vezi un perete -> intoarce-te",
            "note": "Regula buna il ajuta pe robot sa nu se blocheze.",
        },
        {
            "title": "Semaforul",
            "code": "Daca e verde -> mergi\nDaca nu -> asteapta",
            "note": "Aici vezi clar ce inseamna sa pregatesti si varianta de rezerva.",
        },
    ],
    "use_cases": [
        "cand robotul trebuie sa evite un obstacol",
        "cand un joc alege intre castig si mai incearca",
        "cand explici unui copil o regula simpla de comportament",
    ],
    "vocabulary": [
        "regula: intrebare care te ajuta sa alegi",
        "alegere: drumul pe care il iei dupa raspuns",
        "rezerva: planul pregatit pentru cazul in care raspunsul nu este bun",
    ],
    "common_mistakes": [
        "spui regula, dar nu spui ce urmeaza dupa ea",
        "nu pregatesti varianta pentru raspunsul nu",
        "faci regula prea lunga si greu de urmarit",
    ],
    "mini_project": {
        "title": "Mini-proiect: Semafor pentru Robo",
        "prompt": "Alege doua culori si spune ce face Robo pentru fiecare.",
        "steps": [
            "alege culoarea pentru mers",
            "alege culoarea pentru asteptare",
            "spune actiunea pentru fiecare situatie",
        ],
        "outcome": "Ai creat o regula simpla si usor de explicat, exact cum folosesc programele deciziile.",
    },
    "practice_context": "Cand potrivesti regula si actiunea, imagineaza-ti scena reala: ce vede Robo si ce face imediat dupa aceea.",
    "recap_questions": [
        "Ce regula simpla ai folosi pentru un semafor?",
        "De ce este util sa ai si planul de rezerva?",
        "Cum i-ai explica unui coleg ce este o conditie?",
    ],
}

LESSON_GUIDES["nivel-2-aventuri-cu-buclele"] = {
    "examples_text": "Buclele sunt bune cand stii ca acelasi pas apare de multe ori. Scopul lor nu este sa complice lucrurile, ci sa scurteze si sa clarifice codul.",
    "example_cards": [
        {
            "title": "Patru miscari identice",
            "code": "for pas in range(4):\n    robot_danseaza()",
            "note": "Aceeasi actiune se repeta de patru ori fara sa fie scrisa de patru ori.",
        },
        {
            "title": "Cat timp exista energie",
            "code": "while energie > 0:\n    mergi_inainte()\n    energie = energie - 1",
            "note": "Bucla continua pana cand regula nu mai este adevarata.",
        },
        {
            "title": "Iesire rapida",
            "code": "if obstacol:\n    break",
            "note": "Uneori trebuie sa iesi imediat din repetitie, nu sa mergi pana la capat.",
        },
    ],
    "use_cases": [
        "cand un robot repeta o miscare intr-un labirint sau dans",
        "cand parcurgi mai multe obiecte, jucatori sau intrebari",
        "cand vrei sa economisesti cod si sa eviti copierea inutila",
    ],
    "vocabulary": [
        "bucla: secventa care repeta pasi",
        "iteratie: o singura trecere prin bucla",
        "conditie de oprire: regula care spune cand se termina repetitia",
    ],
    "common_mistakes": [
        "nu actualizezi starea si bucla devine infinita",
        "folosesti while cand de fapt stii deja de cate ori repeti",
        "nu explici ce se repeta si de ce",
    ],
    "mini_project": {
        "title": "Mini-proiect: Antrenorul lui Loopster",
        "prompt": "Creeaza o mica rutina de repetitii pentru un robot dansator.",
        "steps": [
            "alege o miscare care se repeta",
            "spune de cate ori se repeta sau pana cand",
            "adauga o conditie clara de oprire",
        ],
        "outcome": "Inveti sa gandesti repetitia ca pe o economie de cod si de efort.",
    },
    "guided_code": "for pas in range(3):\n    print('Robo face un pas')\n\nenergie = 2\nwhile energie > 0:\n    print('Continuam misiunea')\n    energie = energie - 1",
    "practice_context": "Cand alegi intre for si while, intreaba-te mai intai: stiu de cate ori se repeta sau depinde de o conditie?",
    "recap_questions": [
        "Cand ai folosi for in loc de while?",
        "Ce face o conditie de oprire buna?",
        "Cum ai explica unui coleg de ce o bucla infinita este periculoasa?",
    ],
}

LESSON_GUIDES["junior-4-repetitii-care-ajuta"] = {
    "examples_text": "Repetitia este buna cand faci acelasi lucru de mai multe ori. Ea te ajuta sa fii ordonat si sa nu te incurci la numaratoare.",
    "example_cards": [
        {
            "title": "Trei sarituri",
            "code": "Sari -> Sari -> Sari",
            "note": "Vezi usor ca aceeasi actiune apare de mai multe ori.",
        },
        {
            "title": "Trei pasi inainte",
            "code": "Mergi -> Mergi -> Mergi",
            "note": "Robo nu are nevoie de trei planuri diferite pentru aceeasi miscare.",
        },
        {
            "title": "Numaram si ne oprim",
            "code": "1, 2, 3 -> Stop",
            "note": "La repetitie conteaza si momentul in care spui gata.",
        },
    ],
    "use_cases": [
        "cand un robot merge de mai multe ori inainte",
        "cand repeti o miscare intr-un dans sau intr-un joc",
        "cand vrei sa explici aceiasi pasi fara sa ii rescrii mereu",
    ],
    "vocabulary": [
        "repetitie: refacerea aceluiasi pas de mai multe ori",
        "numaratoare: metoda prin care verifici cate repetitii ai facut",
        "oprire: momentul in care repetitia se termina",
    ],
    "common_mistakes": [
        "uita sa spui de cate ori se repeta pasul",
        "nu anunti cand trebuie sa se opreasca",
        "alegi o actiune diferita de fiecare data si nu mai este repetitie reala",
    ],
    "mini_project": {
        "title": "Mini-proiect: Spectacolul lui Robo",
        "prompt": "Alege o miscare si spune cum se repeta de trei ori pentru scena finala.",
        "steps": [
            "alege miscarea",
            "spune de cate ori se repeta",
            "spune cand se termina dansul",
        ],
        "outcome": "Copilul vede usor ca repetitia inseamna economie si ordine, nu doar numarare.",
    },
    "practice_context": "Cand vezi aceeasi miscare de mai multe ori, intreaba-te imediat daca nu cumva ai gasit o repetitie.",
    "recap_questions": [
        "Ce pas ai repeta intr-un joc cu Robo?",
        "De ce este important sa stii cand se termina repetitia?",
        "Unde vezi repetitii in viata de zi cu zi?",
    ],
}

LESSON_GUIDES["code-5-liste-care-organizeaza"] = {
    "examples_text": "Listele devin utile atunci cand proiectul are mai multe obiecte de acelasi fel. In loc de multe variabile separate, folosesti o singura colectie ordonata.",
    "example_cards": [
        {
            "title": "Inventar de obiecte",
            "code": "inventar = ['cheie', 'harta', 'baterie']",
            "note": "Toate obiectele importante stau impreuna si sunt usor de parcurs.",
        },
        {
            "title": "Jucatori intr-un quiz",
            "code": "jucatori = ['Ana', 'Matei', 'Daria']",
            "note": "Lista te ajuta sa procesezi aceeasi actiune pentru mai multi copii.",
        },
        {
            "title": "Parcurgerea tuturor elementelor",
            "code": "for obiect in inventar:\n    print(obiect)",
            "note": "Bucla si lista lucreaza bine impreuna cand vrei sa treci prin toate valorile.",
        },
    ],
    "use_cases": [
        "cand jocul are inventar, niveluri sau mai multi jucatori",
        "cand quizul are mai multe intrebari sau raspunsuri",
        "cand vrei sa adaugi usor elemente noi fara sa refaci tot codul",
    ],
    "vocabulary": [
        "lista: colectie de mai multe valori puse intr-un singur loc",
        "element: o singura valoare din lista",
        "parcurgere: trecerea pe rand prin toate elementele",
    ],
    "common_mistakes": [
        "faci prea multe variabile separate pentru obiecte de acelasi fel",
        "nu te gandesti ce au elementele in comun",
        "uiti ca lista trebuie sa te ajute sa lucrezi mai ordonat, nu mai complicat",
    ],
    "mini_project": {
        "title": "Mini-proiect: Rucsacul exploratorului",
        "prompt": "Construieste o lista cu lucrurile de care ai nevoie intr-o misiune.",
        "steps": [
            "alege trei obiecte importante",
            "grupeaza-le intr-o lista",
            "gandeste ce mesaj ai afisa pentru fiecare",
        ],
        "outcome": "Intelegi clar de ce listele sunt bune pentru inventar si organizare.",
    },
    "guided_code": "inventar = ['cheie', 'harta', 'baterie']\nfor obiect in inventar:\n    print('Robo foloseste:', obiect)",
    "practice_context": "Cauta mai intai ideea comuna dintre elemente. Daca sunt de acelasi fel, lista este adesea raspunsul bun.",
    "recap_questions": [
        "Ce ai pune intr-o lista pentru un joc?",
        "Cand este mai buna o lista decat mai multe variabile separate?",
        "Cum te ajuta o bucla sa parcurgi toate elementele?",
    ],
}

LESSON_GUIDES["junior-5-detectivii-de-buguri"] = {
    "examples_text": "Detectivii de bug-uri nu se grabesc. Ei observa intai diferenta dintre ce trebuia sa se intample si ce a aparut de fapt.",
    "example_cards": [
        {
            "title": "Mesaj gresit",
            "code": "Robo spune alt text decat voiai",
            "note": "Prima intrebare este: ce trebuia sa afiseze si ce a afisat?",
        },
        {
            "title": "Pas lipsa",
            "code": "Robo pleaca fara sa porneasca",
            "note": "Uneori problema nu este pasul gresit, ci pasul care lipseste.",
        },
        {
            "title": "Ordine gresita",
            "code": "Afisare inainte de pregatire",
            "note": "Bug-ul apare si atunci cand pasii buni sunt asezati prost.",
        },
    ],
    "use_cases": [
        "cand un joc afiseaza alt rezultat decat te asteptai",
        "cand robotul face alt traseu decat planul initial",
        "cand vrei sa le arati copiilor ca greseala se poate repara calm",
    ],
    "vocabulary": [
        "bug: greseala mica intr-un program",
        "indiciu: semn care te ajuta sa gasesti problema",
        "reparatie: pasul mic prin care corectezi bug-ul",
    ],
    "common_mistakes": [
        "te grabesti si schimbi prea multe lucruri deodata",
        "nu spui clar ce trebuia sa se intample",
        "te superi pe greseala in loc sa o observi calm",
    ],
    "mini_project": {
        "title": "Mini-proiect: Fisa detectivului",
        "prompt": "Alege o greseala simpla si noteaza cum ai cauta-o in trei pasi.",
        "steps": [
            "spune ce trebuia sa se intample",
            "spune ce s-a intamplat de fapt",
            "alege primul lucru pe care il verifici",
        ],
        "outcome": "Copilul invata o metoda utila, nu doar un raspuns de memorat.",
    },
    "practice_context": "Cand potrivesti indiciul cu problema, imagineaza-ti ce ai observa pe ecran sau pe traseu.",
    "recap_questions": [
        "Cum iti dai seama ca ai gasit un bug?",
        "Ce verifici mai intai cand apare o greseala?",
        "De ce este bine sa repari cate un lucru pe rand?",
    ],
}

LESSON_GUIDES["code-6-repara-codul"] = {
    "examples_text": "Debuggingul bun inseamna metoda. Nu incerci zece lucruri la intamplare, ci verifici semnele si izolezi problema.",
    "example_cards": [
        {
            "title": "Nume scris gresit",
            "code": "energie_robot\nenergii_robot",
            "note": "O singura litera diferita poate rupe tot fluxul programului.",
        },
        {
            "title": "Paranteza lipsa",
            "code": "print('Pornim misiunea'",
            "note": "Uneori eroarea este mica vizual, dar foarte importanta pentru interpretarea codului.",
        },
        {
            "title": "Regula gresita",
            "code": "scor = scor - 1",
            "note": "Daca rezultatul este invers fata de ce asteptai, ai probabil o eroare de logica.",
        },
    ],
    "use_cases": [
        "cand un program porneste, dar da rezultate gresite",
        "cand vrei sa repari clar si fara stres un exercitiu de cod",
        "cand lucrezi in echipa si trebuie sa explici ce ai verificat",
    ],
    "vocabulary": [
        "debugging: procesul de cautare si reparare a erorilor",
        "eroare de sintaxa: problema de scriere a codului",
        "eroare de logica: problema in felul in care gandesti regula sau calculul",
    ],
    "common_mistakes": [
        "schimbi prea multe linii deodata si nu mai stii ce a reparat problema",
        "nu compari rezultatul asteptat cu cel obtinut",
        "nu testezi imediat dupa o schimbare mica",
    ],
    "mini_project": {
        "title": "Mini-proiect: Checklist de debugging",
        "prompt": "Construieste o lista scurta de verificari pe care le faci cand ceva nu merge.",
        "steps": [
            "verific numele variabilelor",
            "verific parantezele si semnele",
            "verific daca regula produce rezultatul asteptat",
        ],
        "outcome": "Obtii o metoda utila pentru orice exercitiu viitor, nu doar pentru lectia curenta.",
    },
    "guided_code": "scor = 10\nbonus = 5\nscor = scor + bonus\nprint(scor)",
    "practice_context": "In practica, incearca sa spui cu voce tare ce problema are fiecare exemplu. Asta te obliga sa gandesti clar.",
    "recap_questions": [
        "Ce tip de eroare ti se pare mai usor de vazut: de scriere sau de logica?",
        "De ce este util sa testezi dupa fiecare schimbare mica?",
        "Cum ai explica unui coleg diferenta dintre sintaxa si logica?",
    ],
}

LESSON_GUIDES["junior-6-poveste-interactiva"] = {
    "examples_text": "Un proiect mic devine interesant cand mai multe idei simple lucreaza impreuna: personaj, alegere, scor si pasi repetati.",
    "example_cards": [
        {
            "title": "Personajul principal",
            "code": "nume_erou = 'Robo'",
            "note": "Variabila te ajuta sa tii minte cine este personajul din poveste.",
        },
        {
            "title": "O alegere importanta",
            "code": "Daca alegi usa rosie -> intri in laborator",
            "note": "Conditia schimba directia povestii si o face interactiva.",
        },
        {
            "title": "Stele castigate",
            "code": "stele = stele + 1",
            "note": "Scorul face aventura mai vie si ii arata copilului ca a progresat.",
        },
    ],
    "use_cases": [
        "cand construiesti o poveste cu alegeri pentru copii",
        "cand vrei sa legi intr-un proiect idei invatate separat",
        "cand pregatesti o prezentare simpla si creativa",
    ],
    "vocabulary": [
        "proiect: ceva mai mare construit din mai multe idei mici",
        "personaj: eroul care trece prin aventura",
        "progres: semnul ca povestea merge mai departe",
    ],
    "common_mistakes": [
        "incerci sa faci o poveste prea mare din prima",
        "nu explici clar ce parte tine de nume, ce parte tine de alegere si ce parte tine de scor",
        "aduni prea multe idei fara un plan scurt",
    ],
    "mini_project": {
        "title": "Mini-proiect: Aventurile lui Robo",
        "prompt": "Schiteaza o poveste interactiva cu inceput, o alegere si un final.",
        "steps": [
            "alege numele eroului",
            "alege o regula care schimba drumul",
            "adauga o recompensa simpla, cum ar fi o stea",
        ],
        "outcome": "Copilul vede ca programarea poate spune povesti, nu doar rezolva exercitii.",
    },
    "practice_context": "Cauta rolul fiecarui element: cine este personajul, ce regula schimba povestea si ce arata progresul.",
    "recap_questions": [
        "Ce ai pastra intr-o variabila in povestea ta?",
        "Unde ai folosi o regula de tip daca?",
        "Cum ai arata copilului ca a progresat in aventura?",
    ],
}

LESSON_GUIDES["nivel-3-super-puteri-cu-functii"] = {
    "examples_text": "Functiile sunt cea mai buna unealta atunci cand acelasi tip de actiune apare in mai multe locuri din proiect si vrei sa ramana curat.",
    "example_cards": [
        {
            "title": "Salut personalizat",
            "code": "def saluta(nume):\n    return f'Salut, {nume}!'",
            "note": "Functia primeste o valoare si intoarce un rezultat gata de folosit.",
        },
        {
            "title": "Calcul de bonus",
            "code": "def bonus(scor, multiplicator):\n    return scor * multiplicator",
            "note": "Acelasi calcul poate fi refolosit ori de cate ori ai nevoie.",
        },
        {
            "title": "Afisare clara",
            "code": "rezultat = bonus(50, 2)\nprint(rezultat)",
            "note": "Functia produce rezultatul, iar restul programului decide cum il foloseste.",
        },
    ],
    "use_cases": [
        "cand un joc face de mai multe ori acelasi calcul",
        "cand separi afisarea, scorul si regulile in parti clare",
        "cand vrei cod mai usor de citit, testat si reparat",
    ],
    "vocabulary": [
        "functie: bloc de cod cu un scop clar",
        "parametru: informatie pe care o trimiti functiei",
        "return: rezultatul pe care functia il trimite inapoi",
    ],
    "common_mistakes": [
        "dai functiei un nume prea vag si nu mai stii ce face",
        "uiti ca parametrii sunt diferiti la fiecare apel",
        "folosesti functii, dar nu te gandesti ce rezultat trebuie sa intoarca",
    ],
    "mini_project": {
        "title": "Mini-proiect: Biblioteca de super-puteri",
        "prompt": "Construieste doua functii simple pe care le-ai folosi intr-un joc sau intr-un robot.",
        "steps": [
            "alege o functie pentru salut sau afisare",
            "alege o functie pentru calcul sau verificare",
            "gandeste ce parametri si ce rezultat are fiecare",
        ],
        "outcome": "Inveti sa organizezi proiectul in bucati reutilizabile si usor de prezentat.",
    },
    "guided_code": "def calculeaza_bonus(scor, multiplicator):\n    return scor * multiplicator\n\nrezultat = calculeaza_bonus(50, 2)\nprint(rezultat)",
    "practice_context": "Nu memora functiile doar ca sintaxa. Intreaba-te mereu: ce problema rezolva aceasta functie si ce rezultat trimite inapoi?",
    "recap_questions": [
        "Ce tip de actiune merita pusa intr-o functie?",
        "Cum te ajuta parametrii sa refolosesti aceeasi idee?",
        "De ce este important return?",
    ],
}

LESSON_GUIDES["code-8-functii-pentru-jocuri"] = {
    "examples_text": "Intr-un proiect de joc, functiile nu sunt decor. Ele tin in ordine tot ce altfel s-ar amesteca: startul, scorul, verificarea raspunsurilor, finalul.",
    "example_cards": [
        {
            "title": "Pornirea jocului",
            "code": "def afiseaza_bun_venit():\n    print('Bine ai venit in quiz!')",
            "note": "Fiecare functie trebuie sa aiba o singura responsabilitate clara.",
        },
        {
            "title": "Verificarea raspunsului",
            "code": "def verifica_raspuns(corect, primit):\n    return corect == primit",
            "note": "Functia raspunde la o intrebare precisa si se poate testa usor.",
        },
        {
            "title": "Rezultatul final",
            "code": "def afiseaza_rezultat(scor):\n    print(f'Scor final: {scor}')",
            "note": "Afisarea finala poate fi separata de calculul scorului.",
        },
    ],
    "use_cases": [
        "cand imparti un joc in componente usor de inteles",
        "cand vrei sa repari doar o parte a proiectului, nu totul",
        "cand explici in echipa cine se ocupa de ce",
    ],
    "vocabulary": [
        "responsabilitate: lucrul clar pe care il face o functie",
        "apel: momentul in care folosesti functia",
        "modular: proiect impartit in bucati clare",
    ],
    "common_mistakes": [
        "faci o functie foarte mare, care face prea multe lucruri",
        "nu alegi un nume care sa arate scopul functiei",
        "amesteci logica jocului cu afisarea rezultatelor",
    ],
    "mini_project": {
        "title": "Mini-proiect: Schita unui quiz",
        "prompt": "Imparte un mini quiz in functii simple si clare.",
        "steps": [
            "functie de start",
            "functie de verificare a raspunsului",
            "functie de afisare a rezultatului",
        ],
        "outcome": "Copilul sau adolescentul invata sa gandeasca organizarea proiectului, nu doar linii separate de cod.",
    },
    "guided_code": "def afiseaza_bun_venit():\n    print('Bine ai venit!')\n\ndef afiseaza_rezultat(scor):\n    print(f'Scor final: {scor}')\n\nafiseaza_bun_venit()\nafiseaza_rezultat(3)",
    "practice_context": "Cand vezi o functie, intreaba-te daca ai putea explica in cinci cuvinte ce face. Daca nu, probabil e prea incarcata.",
    "recap_questions": [
        "Ce functii ai crea pentru un quiz simplu?",
        "Cum te ajuta functiile cand apare un bug?",
        "Ce inseamna ca o functie are un scop clar?",
    ],
}

LESSON_GUIDES["code-9-mini-proiect-quiz-robot"] = {
    "examples_text": "Acesta este momentul in care ideile separate se leaga. Un proiect bun inseamna structura, claritate si verificare, nu doar multe linii de cod.",
    "example_cards": [
        {
            "title": "Lista de intrebari",
            "code": "intrebari = ['Q1', 'Q2', 'Q3']",
            "note": "Listele tin materialul impreuna si fac proiectul usor de extins.",
        },
        {
            "title": "Scorul curent",
            "code": "scor = 0",
            "note": "Variabila de scor iti arata progresul jucatorului in timp real.",
        },
        {
            "title": "Verificarea raspunsului",
            "code": "def verifica_raspuns(corect, primit):\n    return corect == primit",
            "note": "Functia separa logica verificarii de restul proiectului.",
        },
    ],
    "use_cases": [
        "cand construiesti primul proiect coerent pe care il poti arata altora",
        "cand vrei sa unesti variabile, liste, conditii si functii",
        "cand inveti sa gandesti produsul final, nu doar exercitiul de moment",
    ],
    "vocabulary": [
        "componenta: o parte clara din proiect",
        "flux: ordinea in care trece utilizatorul prin proiect",
        "testare: verificarea ca fiecare parte face ce trebuie",
    ],
    "common_mistakes": [
        "incepi direct sa scrii cod fara schema proiectului",
        "nu separi datele, regulile si afisarea",
        "uiti sa verifici daca proiectul este usor de folosit de altcineva",
    ],
    "mini_project": {
        "title": "Mini-proiect: Quiz Robot complet",
        "prompt": "Planifica un quiz mic, dar clar, pe care sa il poti explica unui coleg sau unui parinte.",
        "steps": [
            "pregateste lista de intrebari",
            "pregateste scorul si regula de verificare",
            "pregateste mesajul final pentru utilizator",
        ],
        "outcome": "Nu inveti doar Python, ci si cum sa structurezi un proiect util si prezentabil.",
    },
    "guided_code": "intrebari = ['Python citeste codul de sus in jos?', 'O lista poate grupa mai multe valori?']\nscor = 0\n\ndef verifica_raspuns(corect, primit):\n    return corect == primit\n\nprint('Quiz Robot pregatit!')",
    "practice_context": "In practica gandeste-te la rolul fiecarei piese. Daca stii de ce exista, o vei folosi corect si in proiectul tau propriu.",
    "recap_questions": [
        "Ce componente minime are un quiz clar?",
        "Unde folosesti lista, variabila si functia?",
        "Ce ai verifica inainte sa prezinti proiectul altora?",
    ],
}


def get_lesson_learning_guide(slug: str) -> dict[str, object]:
    guide = LESSON_GUIDES.get(slug, {})
    return guide if isinstance(guide, dict) else {}
