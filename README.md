# Briefly Backend

AI-powered meeting preparation assistant that aggregates context from GitHub, Jira, and Notion to provide synthesized briefings.

## 🚀 Features

- **Voice-activated meeting prep** - Ask "Prep me for standup" and get a comprehensive briefing
- **Multi-source integration** - GitHub PRs, Jira issues, and Notion meeting notes
- **Agentic AI architecture** - Built with LangGraph for parallel data fetching and intelligent synthesis
- **Voice-optimized output** - Briefings designed for easy listening while multitasking
- **CORS enabled** - Ready for React Native/web frontend integration

## 📋 Prerequisites

- Python 3.11+
- OpenAI API key
- Anthropic API key
- Arcade API key (for GitHub, Jira, Notion integrations)

## 🛠️ Local Development Setup

### 1. Clone and Setup Virtual Environment

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
```

```bash
# Linux/Mac
python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ARCADE_API_KEY=your_arcade_api_key_here
```

### 3. Run the Server

```powershell
# PowerShell (Windows)
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

```bash
# Bash (Linux/Mac)
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Verify Installation

```bash
# Check health endpoint
curl http://localhost:8001/health

# Expected: {"status":"healthy"}
```

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### Meeting Prep (Main Endpoint)
```bash
POST /summarize
Content-Type: application/json

{
  "transcript": "Prep me for standup"
}
```

**PowerShell Example:**
```powershell
Invoke-RestMethod -Uri http://localhost:8001/summarize -Method POST -Body (@{transcript='Prep me for standup'} | ConvertTo-Json) -ContentType 'application/json'
```

**cURL Example:**
```bash
curl -X POST http://localhost:8001/summarize \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Prep me for standup"}'
```

**Response:**
```json
{
  "result": {
    "summary": "Meeting Prep Summary for: 'Prep me for standup'\n\n==================================================\n\nGitHub - Found 5 pull request(s):\n  1. PR #17473: React Devtools Component...\n  ...",
    "classification": {
      "is_git": true,
      "is_jira": true,
      "is_meeting_notes": true
    }
  },
  "steps": [
    {
      "name": "graph_execute",
      "ok": true,
      "latencyMs": 2340
    }
  ]
}
```

## 🏗️ Architecture

### LangGraph Workflow

```
┌─────────────┐
│ Coordinator │ (Intent Classification)
└──────┬──────┘
       │
    ┌──┴──┬──────────┬────────────┐
    │     │          │            │
┌───▼───┐ │ ┌────▼────┐  ┌─────▼─────┐
│GitHub │ │ │  Jira   │  │  Notion   │
└───┬───┘ │ └────┬────┘  └─────┬─────┘
    │     │      │              │
    └─────┼──────┴──────────────┘
          │
    ┌─────▼──────┐
    │ Synthesizer│ (LLM-powered summary)
    └────────────┘
```

### Key Components

- **Coordinator Node**: Rule-based intent classification
- **GitHub Node**: Fetches PRs via Arcade API
- **Jira Node**: Fetches issues via Arcade API
- **Notion Node**: Fetches meeting notes via Arcade API
- **Synthesis Node**: Formats and synthesizes all data into voice-optimized briefing

## 🐳 Docker Deployment

### Build and Run Locally

```bash
# Build
docker build -t briefly-backend .

# Run
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e ANTHROPIC_API_KEY=your_key \
  -e ARCADE_API_KEY=your_key \
  briefly-backend
```

## ☁️ Railway Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed Railway deployment instructions.

**Quick Deploy:**

1. Push code to GitHub
2. Connect repository to Railway
3. Add environment variables in Railway dashboard
4. Railway auto-deploys from Dockerfile

## 📁 Project Structure

```
Briefly-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app & routes
│   ├── tools.py                   # Utility functions
│   └── graph/
│       ├── __init__.py
│       └── meeting_prep_graph.py  # LangGraph workflow
├── .env                           # Environment variables (gitignored)
├── .gitignore
├── Dockerfile
├── .dockerignore
├── railway.json
├── requirements.txt
├── README.md
└── DEPLOYMENT.md
```

## 🔒 Security Notes

- Never commit `.env` file or API keys
- Update CORS origins for production (currently set to `allow_origins=["*"]`)
- Use environment variables for all sensitive configuration

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o-mini | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude Sonnet | Yes |
| `ARCADE_API_KEY` | Arcade API key for tool integrations | Yes |
| `PORT` | Server port (auto-set by Railway) | No (default: 8000) |

## 🧪 Testing

```bash
# Run health check
curl http://localhost:8001/health

# Test meeting prep
curl -X POST http://localhost:8001/summarize \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Prep me for standup"}'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## 📄 License

MIT License

## 🙋 Support

For issues or questions, please open an issue on GitHub.
