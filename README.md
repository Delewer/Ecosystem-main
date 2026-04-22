# Ecosystem - Platforma educationala AI-first

Ecosystem este o platforma educationala construita pe Django, orientata pe invatare adaptiva, gamification, analytics si asistenta AI, cu module dedicate pentru elevi, profesori, parinti si administratori.

## Ce contine proiectul

- Aplicatie web principala cu dashboard-uri pe roluri.
- API REST pentru lectii, comentarii, rating, progres si Robot Lab.
- Straturi de servicii pentru logica de business (fara logica critica in views).
- Sistem separat de executie cod pentru Robot Lab (`runner_service`).
- Set extins de teste pentru fluxuri critice.

## Imbunatatiri implementate (stare actuala)

### AI si invatare adaptiva

- Explicatii pentru greseli in teste si cod.
- Follow-up socratic pentru invatare ghidata.
- Generare de practica personalizata.
- Rezumate de insight pentru profesor/parinte.
- Gard pentru halucinatii AI (context + filtrare raspuns).
- Tracking cost AI (prompt/completion, estimare token-uri).

### Securitate si robustete

- Rate limiting global (middleware + servicii).
- Idempotency pentru endpoint-uri critice de tip `POST`.
- Audit trail imutabil pentru evenimente importante.
- Detectie anti-cheat pentru anumite scenarii de evaluare.
- Permisiuni pe actiuni si roluri.

### Community si moderare

- Sistem de reputatie.
- Rol de contributor de incredere.
- Moderare automata pentru comentarii.
- Like-uri pe comentarii.
- Raspunsuri curate de profesor.
- Pagina de moderare comentarii pentru staff.

### Gamification avansata

- Evenimente sezoniere.
- Leaderboard pe skill-uri.
- XP decay optional.
- Perks cosmetice avatar.
- Token-uri de streak freeze.

### Analytics si BI

- Funnel analytics.
- Cohort analysis.
- Risk scoring predictiv.
- Early-warning pentru profesori.
- Export analytics in CSV si format BigQuery (NDJSON + schema).

### Offline si PWA

- Politica de conflict pentru sincronizare progres offline.
- Coada de progres offline in DB (`OfflineProgressQueue`).
- Fisiere PWA de baza incluse (`service-worker.js`, `manifest.webmanifest`).

### Robot Lab (Python Missions)

- Niveluri JSON in `estudy/robot_lab/levels`.
- API pentru niveluri, rulare, progres si mentor feedback.
- Clasificare erori tipice + mentor AI structurat (RoboMentor).
- Profil de skill pe utilizator si progres pe nivel.
- Runner separat FastAPI pentru executie cod ne-incredere.

### Developer Experience

- Feature flags cu rollout procentual.
- `BaseServiceResult` pentru contract uniform in servicii.
- Comenzi de management:
  - `seed_demo_data`
  - `sync_openapi`
  - `export_analytics`
  - `fix_empty_slugs`

## Arhitectura (high-level)

- `estudy/`: domeniul educational principal (models, views, api, services, templates).
- `inregistrare/`: autentificare, profil, fluxuri account.
- `unitexapp/`: pagini publice/landing si UI shared.
- `unitex_school/`: configurari Django.
- `runner_service/`: sandbox de executie pentru Robot Lab (FastAPI).
- `docs/openapi.yaml`: schema OpenAPI sincronizabila din cod.

## Tehnologii

- Backend principal: Django 4.0.7
- API: Django REST Framework + Token auth
- Runner cod: FastAPI + Uvicorn
- Baza de date: SQLite (dev), `DATABASE_URL` pentru override (ex: PostgreSQL)
- Cache: LocMem (default) sau Redis (`REDIS_URL`)

## Cerinte locale

- Python 3.10+ recomandat
- `pip` actualizat
- (Optional) Redis pentru cache/rate limit distribuit

## Instalare aplicatie Django

```bash
git clone <repo-url>
cd Ecosystem-main
python -m venv .venv
```

Activare virtualenv:

- Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

- Linux/macOS:

```bash
source .venv/bin/activate
```

Instalare dependinte de baza (in lipsa unui `requirements.txt` in radacina):

```bash
pip install --upgrade pip
pip install "Django==4.0.7" "djangorestframework>=3.14,<3.16" "Pillow>=10,<12" "dj-database-url>=2,<3" "django-redis>=5,<6" "sentry-sdk>=2,<3" "PyYAML>=6,<7"
```

Migrate + superuser:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Pornire server:

```bash
python manage.py runserver
```

## Configurare minima (variabile de mediu)

Exemplu minim pentru dezvoltare:

```bash
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=change-me
ALLOWED_HOSTS=127.0.0.1,localhost
TIME_ZONE=Europe/Chisinau
LANGUAGE_CODE=ro
```

Variabile importante pentru functionalitati extinse:

- `DATABASE_URL`
- `REDIS_URL`
- `ROBOT_RUNNER_URL`
- `ROBOT_RUNNER_TOKEN`
- `ROBOT_RUNNER_TIMEOUT_MS`
- `ESTUDY_AUDIT_TRAIL_ENABLED`
- `ESTUDY_RATE_LIMIT_ENABLED`
- `ESTUDY_IDEMPOTENCY_ENABLED`
- `ESTUDY_AI_COST_*`

## Rulare Robot Lab Runner (serviciu separat)

Din `runner_service/`:

```bash
cd runner_service
python -m venv .venv
```

Activare:

- Windows:

```powershell
.venv\Scripts\Activate.ps1
```

- Linux/macOS:

```bash
source .venv/bin/activate
```

Instalare + start:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8101
```

Seteaza in aplicatia Django:

```bash
ROBOT_RUNNER_URL=http://127.0.0.1:8101
ROBOT_RUNNER_TOKEN=<aceeasi-valoare-ca-in-runner>
```

## Activare feature flag pentru Robot Lab

Robot Lab este protejat de flag-ul `robot_lab_enabled`.

```bash
python manage.py shell -c "from estudy.models import FeatureFlag; FeatureFlag.objects.update_or_create(key='robot_lab_enabled', defaults={'enabled': True, 'rollout_percentage': 100, 'description': 'Enable Robot Lab'})"
```

## Comenzi utile

Sincronizare OpenAPI:

```bash
python manage.py sync_openapi
```

Seed demo data:

```bash
python manage.py seed_demo_data
```

Export analytics CSV:

```bash
python manage.py export_analytics --kind event_log --format csv --output analytics_event_log.csv
```

Export analytics BigQuery:

```bash
python manage.py export_analytics --kind event_log --format bigquery --output analytics_event_log.ndjson
```

## Endpoint-uri API principale

Prefix principal: `/estudy/api/` (si alias `/estudy/api/v1/`)

- `POST /estudy/api/token/`
- `GET|POST /estudy/api/lessons/{lesson_slug}/comments/`
- `POST /estudy/api/comments/{comment_id}/like/`
- `POST /estudy/api/lessons/{lesson_slug}/rate/`
- `GET /estudy/api/lessons/{lesson_slug}/stats/`
- `GET /estudy/api/progress/`
- `POST /estudy/api/robot-lab/mentor/`
- `GET /estudy/api/robot-lab/levels/`
- `GET /estudy/api/robot-lab/levels/{level_id}/`
- `POST /estudy/api/robot-lab/runs/`
- `GET /estudy/api/robot-lab/progress/`

Schema API:

- `docs/openapi.yaml` (fara garantie sa fie la zi daca nu rulezi `sync_openapi`)

## Testare

Rulare teste Django:

```bash
python manage.py test
```

Rulare teste runner:

```bash
cd runner_service
python -m unittest -q
```

## Ce este inca in roadmap

- Sandbox de productie complet hardenizat (gVisor/Docker cu limite stricte de resurse si retea blocata complet).
- AI orchestrator central cu politici de raspuns.
- Versionare lectii + A/B testing.
- Peer review avansat (flux complet conflict/plagiarism).
- Retry/backoff si indicatori vizuali completi pentru offline sync.
- CI mai strict (lint + test + scan security + migrari rollback-safe).

## Fisiere de context utile

- `improve.md` - checklist extins de platforma si reguli arhitecturale.
- `game.md` - concept si directii pentru Robot Lab.
- `robot_lab_ai_agent_spec.txt` - specificatie agent AI pentru Robot Lab.
- `runner_service/README.md` - detalii runner FastAPI.

## Nota de siguranta

Inainte de productie:

- muta toate credentialele sensibile in variabile de mediu,
- seteaza `DJANGO_DEBUG=False`,
- configureaza corect `ALLOWED_HOSTS` si `CSRF_TRUSTED_ORIGINS`,
- foloseste baza de date si cache de productie.
