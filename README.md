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
curl http://localhost:8000/healthz
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
  api/
    __init__.py
    routes.py
```