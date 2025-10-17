# Briefly-backend
Collaborative agents for pulling context for meetings

## FastAPI backend (local dev)

### Requirements
- Python 3.11+
- PowerShell on Windows

### Setup (PowerShell)
```powershell
# From repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
```

### Run (auto-reload)
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Verify
```powershell
curl http://localhost:8000/health
curl http://localhost:8000/api/ping
```

Expected responses:
```json
{"status":"ok"}
{"message":"pong"}
```

### Project layout
```
app/
  __init__.py
  main.py
```

## Agent endpoint (MVP)

### POST /api/agent/act
Request body:
```json
{
  "goal": "Prep me for standup",
  "inputs": { "user": "matt" }
}
```

PowerShell test:
```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/agent/act -Method POST -Body (@{goal='Prep me for standup'; inputs=@{user='matt'}} | ConvertTo-Json) -ContentType 'application/json' | ConvertTo-Json -Compress
```

Response (mocked data example):
```json
{
  "result": {
    "summary": "Goal: Prep me for standup. GitHub PRs: Add summarizer endpoint, Refactor auth middleware. Jira assigned: BRF-101, BRF-88. Top blocker: Auth feature blocked by OAuth redirect."
  },
  "steps": [
    {"name": "fetch_github", "ok": true, "latencyMs": 50},
    {"name": "fetch_jira", "ok": true, "latencyMs": 0},
    {"name": "synthesize", "ok": true, "latencyMs": 0}
  ]
}
```