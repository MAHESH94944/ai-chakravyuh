# Startup Idea Validator — Backend

This repository contains the backend for an AI-powered, multi-agent "Startup Idea Validator".
The system is organized so the Coordinator agent orchestrates a set of specialized agents
that each return structured JSON. The Coordinator synthesizes a final report.

## What I implemented so far

- Project skeleton with main FastAPI app: `main.py`.
- Configuration loader: `core/config.py` (pydantic-settings with a dotenv fallback).
- API schemas: `models/schemas.py` (Pydantic models `IdeaInput` and `TaskResponse`).
- API endpoint: `api/v1/tasks.py` with `POST /api/v1/validate-idea` (returns a generated task_id and pending status).

Uvicorn was started successfully and the app responded to requests at http://127.0.0.1:8000.

## Repo layout (relevant files)

```
startup-validator-backend/
├── api/
│   └── v1/tasks.py        # FastAPI router with /validate-idea
├── agents/                # agent implementations (planned)
├── coordinator/           # orchestration logic (planned)
├── core/config.py         # settings loader (pydantic-settings + dotenv fallback)
├── models/schemas.py      # Pydantic request/response models
├── tools/web_search.py    # web-search tool (planned)
├── main.py                # FastAPI app wiring
└── requirements.txt
```

## How to run locally

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/Scripts/activate
```

2. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add API key placeholders:

```ini
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
GROQ_API_KEY="YOUR_GROQ_API_KEY_HERE"
TAVILY_API_KEY="YOUR_TAVILY_API_KEY_HERE"
```

4. Run the server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. Open Swagger UI: http://127.0.0.1:8000/docs

## API usage example

POST /api/v1/validate-idea
Request body:

```json
{ "idea": "An AI-powered app for personalized workout and meal plans." }
```

Response (example):

```json
{
  "task_id": "<uuid>",
  "status": "pending",
  "message": "Your startup idea has been received and is being analyzed."
}
```

## Agent roster (design)

1. Coordinator Agent — orchestrates workflow, collects agent outputs, synthesizes final Markdown report. (Recommended LLM: Gemini)
2. Market Research Agent — generates web search queries (Groq) and calls the web-search tool (Tavily) to gather competitors, market size, target audience.
3. User Persona Agent — creates a one-paragraph fictional user story. (Gemini)
4. Technical Feasibility Agent — lists technical challenges and suggests a technology stack. (Gemini)
5. Finance Agent — estimates costs and revenue streams based on market data. (Gemini)
6. Risk Agent — identifies top risks from market and technical outputs. (Gemini)
7. Critic Agent — critiques Finance and Risk outputs for blind spots. (Gemini)

Each agent returns structured JSON (examples available in project notes). The Coordinator synthesizes them into a final report.

## What's next (recommended)

- Implement `tools/web_search.py` (Tavily client) and `agents/market_research.py` — unlocks cross-agent flows.
- Implement `coordinator/workflow.py` to call agents and persist results.
- Add `core/database.py` to log tasks and agent responses to MongoDB.
- Add background processing (FastAPI BackgroundTasks, Celery, or RQ) to process tasks asynchronously.
- Add unit tests (agents + API) and CI integration.

If you'd like, I can implement the web-search client and Market Research agent next.

---

```

```
