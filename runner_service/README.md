# Robot Lab Runner Service

Internal FastAPI service for executing untrusted Robot Lab code in isolation.

## Run locally

```bash
cd runner_service
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8101
```

## Environment variables

- `ROBOT_RUNNER_TOKEN` (optional): expected bearer token from Django.

## API

- `GET /health`
- `POST /v1/execute`
