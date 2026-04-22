# UNITEX / Ecosystem - platforma educationala AI-first

UNITEX este o platforma educationala construita pe Django pentru copii, elevi, profesori, parinti si administratori. Brandul vizibil in interfata este UNITEX, iar proiectul tehnic este organizat in jurul aplicatiilor `unitex_school`, `unitexapp`, `inregistrare` si `estudy`.

Versiunea curenta include lectii digitale, dashboard-uri pe roluri, gamification, comunitate, clase, proiecte, analytics, asistenta AI si Robot Lab v2 cu lumi, skin-uri si runner separat pentru executia codului Python.

## Ce include versiunea curenta

### Platforma web

- Landing page UNITEX cu fluxuri de autentificare si inregistrare.
- Roluri principale: student, profesor, parinte si administrator.
- Dashboard-uri separate pentru fiecare rol.
- Profil utilizator, termeni si conditii, politica de cookie-uri.
- Liste de lectii, pagina de lectie, lectie speciala de alfabetizare digitala, overview si progres.
- World map educational, typing game, misiuni, leaderboard si notificari.
- Clase, teme, proiecte, forum comunitar si moderare comentarii.

### Curriculum si continut

- Domenii si trasee pentru Python, Web Foundations, Digital basics si Matematica pentru coderi.
- Modele pentru subject, course, module, lesson, topic tags, tests, code exercises si learning paths.
- Lectii seeduite prin migrari si comanda `seed_demo_data`.
- Metadate pentru varsta, dificultate, XP, obiective, takeaways, practica, reflectie si media.

### AI si invatare adaptiva

- Hint-uri AI pe lectii si exercitii.
- Explicatii pentru greseli in teste si cod.
- Follow-up socratic dupa raspunsuri gresite.
- Practica personalizata si recomandari.
- Guard pentru raspunsuri AI bazate pe contextul lectiei.
- Tracking cost AI pentru prompt/completion si estimari de token-uri.
- Insight summaries, risk scoring si early warning pentru profesori.

### Robot Lab v2

- 30 de niveluri JSON in `estudy/robot_lab/levels`: 5 lumi x 6 niveluri.
- Lumi: Gradina, Pestera de Gheata, Vulcanul, Statia Spatiala si Nucleul Final.
- Moduri UI: butoane vizuale, butoane + cod, cod ghidat si cod complet.
- Progres pe nivel, stele, XP, skill profile si istoric de incercari.
- Skin-uri robot: ZIPP, BLAZE, FROSTY, NOVA si OMEGA.
- Mentor feedback structurat prin RoboMentor si clasificare de erori tipice.
- Executie cod prin runner FastAPI separat sau fallback local in debug.

### Platforma, securitate si observabilitate

- API REST cu Django REST Framework si token auth.
- Rate limiting pe middleware si servicii.
- Idempotency pentru endpoint-uri POST critice.
- Audit trail pentru evenimente importante.
- Feature flags din baza de date sau `ESTUDY_FEATURE_FLAGS`.
- Cache LocMem implicit, Redis optional prin `REDIS_URL`.
- Export analytics in CSV si NDJSON compatibil BigQuery.
- OpenAPI generabil prin `sync_openapi`.

## Structura proiectului

- `unitex_school/` - setari Django, routing principal, WSGI/ASGI.
- `unitexapp/` - landing page si pagini publice.
- `inregistrare/` - autentificare, inregistrare, profil si pagini legale.
- `estudy/` - domeniul educational principal: modele, views, API, servicii, templates, migrari si teste.
- `estudy/robot_lab/levels/` - indexul si fisierele JSON pentru Robot Lab.
- `runner_service/` - serviciu FastAPI pentru executia izolata a codului Robot Lab.
- `docs/openapi.yaml` - schema OpenAPI generata sau stub local.
- `media/` si `staticfiles/` - fisiere generate/local runtime.

## Tehnologii

- Backend principal: Django 4.0.7.
- API: Django REST Framework + TokenAuthentication.
- Baza de date implicita: SQLite.
- Baza de date optionala: orice `DATABASE_URL` acceptat de `dj-database-url`.
- Cache implicit: Django LocMem.
- Cache optional: Redis prin `django-redis`.
- Runner cod: FastAPI, Uvicorn, Pydantic.
- Formatare/lint: Black, isort, flake8 prin `.pre-commit-config.yaml`.

## Cerinte locale

- Python 3.10+.
- `pip` actualizat.
- Redis optional, doar daca setezi `REDIS_URL`.
- Nu exista `requirements.txt` in radacina in aceasta versiune; dependintele aplicatiei Django se instaleaza manual sau se pot muta ulterior intr-un fisier dedicat.

## Instalare aplicatie Django

```bash
git clone <repo-url>
cd Ecosystem-main
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instaleaza dependintele pentru aplicatia Django:

```bash
pip install --upgrade pip
pip install "Django==4.0.7" "djangorestframework>=3.14,<3.16" "Pillow>=10,<12" "dj-database-url>=2,<3" "django-redis>=5,<6" "sentry-sdk>=2,<3" "PyYAML>=6,<7"
```

Pregateste baza de date:

```bash
python manage.py migrate
python manage.py seed_demo_data
python manage.py createsuperuser
```

Porneste serverul Django:

```bash
python manage.py runserver
```

Adrese utile local:

- `http://127.0.0.1:8000/` - landing UNITEX.
- `http://127.0.0.1:8000/register/` - inregistrare.
- `http://127.0.0.1:8000/login/` - autentificare.
- `http://127.0.0.1:8000/estudy/` - dashboard router.
- `http://127.0.0.1:8000/admin/` - Django admin.

## Configurare prin variabile de mediu

Configurare minima pentru dezvoltare:

```bash
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=change-me
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
TIME_ZONE=Europe/Chisinau
LANGUAGE_CODE=ro
```

Variabile de mediu citite direct de `unitex_school/settings.py`:

- `DATABASE_URL` - override pentru baza de date.
- `REDIS_URL` - activeaza cache Redis.
- `SENTRY_DSN` - activeaza Sentry.
- `UNITEX_TEACHER_CODE` - codul cerut la inregistrarea unui profesor.
- `ROBOT_RUNNER_URL` - URL-ul runner-ului Robot Lab.
- `ROBOT_RUNNER_TOKEN` - bearer token comun intre Django si runner.
- `ROBOT_RUNNER_TIMEOUT_MS` - timeout pentru apelul catre runner.
- `ESTUDY_AUDIT_TRAIL_ENABLED` - activeaza/dezactiveaza audit trail.
- `ESTUDY_AI_COST_*` - provider, model, moneda, rate si estimari AI.

Setari Django utile, dar nelegate direct la environment in aceasta versiune:

- `ESTUDY_RATE_LIMIT_ENABLED`
- `ESTUDY_IDEMPOTENCY_ENABLED`
- `ESTUDY_FEATURE_FLAGS`
- `ESTUDY_XP_DECAY_*`
- `ESTUDY_SEASONAL_POINTS_PER_LESSON`
- `ESTUDY_OPENAPI_*`

Nota: setarile email SMTP sunt hardcodate in `unitex_school/settings.py` in aceasta versiune. In productie trebuie mutate in variabile de mediu.

## Robot Lab runner

In dezvoltare, daca `ROBOT_RUNNER_URL` este gol si `DJANGO_DEBUG=True`, aplicatia incearca fallback local prin `runner_service.app.engine`. Pentru un mediu mai apropiat de productie, porneste runner-ul separat.

Din `runner_service/`:

```bash
cd runner_service
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instalare si start:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8101
```

Configureaza Django:

```bash
ROBOT_RUNNER_URL=http://127.0.0.1:8101
ROBOT_RUNNER_TOKEN=<aceeasi-valoare-ca-in-runner>
```

Endpoint-uri runner:

- `GET /health`
- `POST /v1/execute`

## Feature flags

Feature flags pot fi definite in baza de date prin modelul `FeatureFlag` sau in settings prin `ESTUDY_FEATURE_FLAGS`.

Flag-uri folosite in cod:

- `robot_lab_enabled` - activeaza Robot Lab; default-ul curent in views/API este `True`.
- `coop_mode_enabled` - activeaza sesiunile cooperative.
- `streak_leaderboard_enabled` - activeaza leaderboard-ul pe streak-uri.

Exemplu pentru activare Robot Lab din shell:

```bash
python manage.py shell -c "from estudy.models import FeatureFlag; FeatureFlag.objects.update_or_create(key='robot_lab_enabled', defaults={'enabled': True, 'rollout_percentage': 100, 'description': 'Enable Robot Lab'})"
```

## Comenzi utile

Seed demo data:

```bash
python manage.py seed_demo_data
```

Sincronizare OpenAPI:

```bash
python manage.py sync_openapi --format yaml --output docs/openapi.yaml
```

Export analytics CSV:

```bash
python manage.py export_analytics --kind event_log --format csv --output analytics_event_log.csv
```

Export analytics BigQuery:

```bash
python manage.py export_analytics --kind event_log --format bigquery --output analytics_event_log.ndjson
```

Kind-uri suportate la export:

- `event_log`
- `lesson_analytics`
- `lesson_progress`
- `test_attempt`

Fix pentru lectii fara slug:

```bash
python manage.py fix_empty_slugs
```

## Rute web principale

- `/` - landing UNITEX.
- `/register/`, `/login/`, `/logout/` - auth principal.
- `/auth/signup/`, `/auth/profile/`, `/auth/edit_profile/` - cont utilizator.
- `/auth/termeni-si-conditii/`, `/auth/politica-cookie/` - pagini legale.
- `/estudy/` - router dashboard.
- `/estudy/dashboard/student/`
- `/estudy/dashboard/teacher/`
- `/estudy/dashboard/admin/`
- `/estudy/dashboard/parent/`
- `/estudy/lessons/`
- `/estudy/world-map/`
- `/estudy/typing-game/`
- `/estudy/missions/`
- `/estudy/leaderboard/`
- `/estudy/notifications/`
- `/estudy/classrooms/`
- `/estudy/projects/`
- `/estudy/community/`
- `/estudy/moderate/comments/`
- `/estudy/robot-lab/worlds/`
- `/estudy/robot-lab/game/<level_id>/`
- `/estudy/robot-lab/teacher/`

## Endpoint-uri API principale

Prefix principal: `/estudy/api/`. Exista si aliasul `/estudy/api/v1/`.

- `POST /estudy/api/token/`
- `GET|POST /estudy/api/lessons/<lesson_slug>/comments/`
- `GET|PUT|PATCH|DELETE /estudy/api/comments/<pk>/`
- `GET|POST /estudy/api/comments/<comment_id>/replies/`
- `POST /estudy/api/comments/<comment_id>/like/`
- `POST /estudy/api/lessons/<lesson_slug>/rate/`
- `GET|PUT|PATCH|DELETE /estudy/api/ratings/<pk>/`
- `GET /estudy/api/lessons/<lesson_slug>/stats/`
- `GET /estudy/api/analytics/`
- `GET /estudy/api/analytics/<lesson_slug>/`
- `GET /estudy/api/progress/`
- `POST /estudy/api/robot-lab/mentor/`
- `GET /estudy/api/robot-lab/levels/`
- `GET /estudy/api/robot-lab/levels/<level_id>/`
- `POST /estudy/api/robot-lab/runs/`
- `GET /estudy/api/robot-lab/progress/`
- `GET /estudy/api/robot-lab/worlds/`
- `GET /estudy/api/robot-lab/skins/`
- `POST /estudy/api/robot-lab/skins/select/`

Schema API se regenereaza cu:

```bash
python manage.py sync_openapi
```

Fisierul `docs/openapi.yaml` poate fi un stub daca aceasta comanda nu a fost rulata dupa ultimele schimbari.

## Testare

Ruleaza testele Django:

```bash
python manage.py test
```

Ruleaza testele runner-ului:

```bash
cd runner_service
python -m unittest -q
```

Verificari optionale:

```bash
python manage.py check
pre-commit run --all-files
```

## Roadmap si datorii cunoscute

- Mutarea dependintelor Django intr-un `requirements.txt` sau `pyproject.toml` la radacina.
- Mutarea credentialelor SMTP din settings in variabile de mediu.
- Sandbox de productie mai strict pentru runner: container/gVisor, limite de CPU/memorie si retea blocata.
- CI complet pentru lint, teste, migrari si verificari de securitate.
- OpenAPI regenerat automat in CI.
- Flux offline/PWA cu retry/backoff si indicatori vizuali mai completi.

## Note pentru productie

Inainte de productie:

- seteaza `DJANGO_DEBUG=False`;
- seteaza `DJANGO_SECRET_KEY` din secret manager sau variabile de mediu;
- configureaza `ALLOWED_HOSTS` si `CSRF_TRUSTED_ORIGINS`;
- foloseste baza de date si cache de productie;
- porneste `runner_service` izolat de procesul Django;
- configureaza `ROBOT_RUNNER_TOKEN`;
- muta credentialele email in variabile de mediu;
- ruleaza migrarile si testele inainte de deploy.
