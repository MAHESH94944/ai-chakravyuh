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

POST /api/v1/validate-idea (idea + optional location)

Request body (JSON) — two fields:

- idea (string) — required. Short description of the startup idea.
- location (object) — optional. Two accepted shapes:
  - text-only: {"text": "Alandi, Pune, Maharashtra, India"}
  - coordinates: {"lat": 18.6211, "lon": 73.9209}

Example payloads:

1. With free-form location text:

```json
{
  "idea": "An AI-powered app for personalized workout and meal plans.",
  "location": { "text": "Alandi, Pune, Maharashtra, India" }
}
```

2. With coordinates:

```json
{
  "idea": "An AI-powered app for personalized workout and meal plans.",
  "location": { "lat": 18.6211, "lon": 73.9209 }
}
```

Response (example):

```json
{
  "report": "# Startup Feasibility Report: AI Personal Stylist\n\n... full markdown report ..."
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

- Quick test payloads (copy/paste into Swagger UI `/docs` -> POST /validate-idea)

- Raw sample you provided (note: this first example contains an extra `additionalProp1` and will not validate cleanly):

```json
{
  "idea": "string",
  "location": {
    "additionalProp1": {}
  }
}
```

- Corrected test payload (use this in the Swagger UI or in your frontend). This uses the requested location string for Alandi, Pune, Maharashtra, India:

```json
{
  "idea": "A decentralized platform for freelancers to get instant micro-payments for completed tasks",
  "location": { "text": "Alandi, Pune, Maharashtra, India" }
}
```

How to test in the running server:

1. Open the FastAPI docs at `http://127.0.0.1:8000/docs` (or your ngrok/public URL + `/docs`).
2. Find the POST `/validate-idea` operation.
3. Click "Try it out", paste the JSON from above, then click "Execute".
4. The response body will contain the generated report (usually a markdown string inside the JSON response).

Notes:

- The app is FastAPI (Swagger UI at `/docs`). If you expect Flask, the same JSON can be used when hitting the Flask endpoint, but this repo serves FastAPI.
- If you want me to run a POST and show a real response from your local server, tell me which URL to target (local or ngrok) and I'll run the request.
- Implement `tools/web_search.py` (Tavily client) and `agents/market_research.py` — unlocks cross-agent flows.
- Implement `coordinator/workflow.py` to call agents and persist results.
- Add `core/database.py` to log tasks and agent responses to MongoDB.
- Add background processing (FastAPI BackgroundTasks, Celery, or RQ) to process tasks asynchronously.
- Add unit tests (agents + API) and CI integration.

If you'd like, I can implement the web-search client and Market Research agent next.

---

---

## Frontend integration guide (for React)

This section is written for the frontend team. It lists the available endpoints, the exact request/response shapes, simple examples using fetch/axios, and notes about errors and CORS.

### Local dev server

- Base URL (local): http://127.0.0.1:8000
- Swagger UI / interactive docs: http://127.0.0.1:8000/docs

Remote (ngrok): https://25cf9a8e730f.ngrok-free.app

Start the server in the backend folder:

```bash
source venv/Scripts/activate   # Windows bash/Git Bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Implemented endpoints (stable)

1. Health / root

- Method: GET
- Path: `/`
- Description: Simple health check. Returns a JSON with status and welcome message.
- Request: none
- Response example (200):

```json
{ "status": "ok", "message": "Welcome to the Startup Idea Validator API!" }
```

2. Validate idea (full analysis)

- Method: POST
- Path: `/api/v1/validate-idea`
- Description: Submits a startup idea and returns a synthesized feasibility report. Current implementation runs the full coordinator workflow and returns a final report (Markdown string) synchronously.
- Request body (JSON):

```json
{
  "idea": "An AI personal stylist app that suggests outfits from a user's existing wardrobe."
}
```

- Successful response (200) - `FinalReport`:

```json
{
  "report": "# Startup Feasibility Report: AI Personal Stylist\n\n... full markdown report ..."
}
```

- Errors you may encounter:
  - 400 Bad Request: invalid or empty `idea` field.
  - 500 Internal Server Error: agent/tool failures (examples: web-search error, LLM error). The response body contains an error detail string.

Notes: The endpoint currently returns the final report synchronously. If the analysis becomes long-running later, we may switch to an async pattern (enqueue -> poll) and the frontend will be updated accordingly.

### Planned endpoints (not implemented yet)

These are suggested endpoints the frontend may rely on in the future:

- `POST /api/v1/validate-idea` (async mode) — returns a `task_id` and `pending` status. Frontend can poll:
  - `GET /api/v1/tasks/{task_id}` — returns task status and partial/complete outputs.
- `GET /api/v1/tasks` — list recent tasks and statuses.

If you want async behavior now, tell me and I can add a task queue + task endpoints.

### Example frontend usage (React)

Fetch (native):

```js
// Set the base URL to either LOCAL_BASE_URL or REMOTE_BASE_URL (ngrok)
const LOCAL_BASE_URL = "http://127.0.0.1:8000";
const REMOTE_BASE_URL = "https://25cf9a8e730f.ngrok-free.app";

const idea =
  "An AI personal stylist app that suggests outfits from a user's existing wardrobe.";

fetch(`${LOCAL_BASE_URL}/api/v1/validate-idea`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ idea }),
})
  .then((res) => {
    if (!res.ok) throw new Error("Server error " + res.status);
    return res.json();
  })
  .then((data) => {
    // data.report is a Markdown string
    console.log("Report received", data.report);
  })
  .catch((err) => console.error(err));
```

Axios example:

```js
import axios from "axios";

async function submitIdea(idea) {
  try {
    const res = await axios.post("http://127.0.0.1:8000/api/v1/validate-idea", {
      idea,
    });
    // res.data.report contains the markdown report
    return res.data.report;
  } catch (err) {
    console.error("API error", err?.response?.data || err.message);
    throw err;
  }
}
```

Displaying the report

- The backend returns Markdown in `report`. Use a Markdown renderer (for example `react-markdown`) to render it in the UI.

Security & CORS

- During local development, enable CORS in the backend so the React dev server (usually http://localhost:3000) can call the API. To enable CORS add the following to `main.py`:

```py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)
```

Environment keys (backend)

- The backend reads API keys from `.env` via `core/config.py`. For local dev, create `.env` at the project root with:

```
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
GROQ_API_KEY="YOUR_GROQ_API_KEY"
TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
```

Frontend UX notes / suggestions

- The analysis may take a few seconds (or longer) depending on agent/tool usage. Consider showing a loading spinner and a message like "Analyzing your idea — this may take up to 30 seconds." If we switch to async task processing, implement progress polling.
- The returned report is Markdown: provide a copy/download button and a "Regenerate" action to re-run analysis.

Debugging tips for frontend devs

- Use the Swagger UI at `/docs` to try requests and inspect responses.
- If you get CORS errors, add the `CORSMiddleware` snippet above and restart the backend.
- For 500 errors: check backend logs (console where `uvicorn` runs) for the agent error details.

## Contact / Next steps

- If you want async endpoints (task enqueue + polling), say "implement async tasks" and I'll add a simple BackgroundTasks or Redis/Celery-backed queue and the task status endpoints.
- If you want mock endpoints for frontend development (to work without API keys), I can add a `/mock/validate-idea` route that returns canned JSON immediately.

---

This README is focused on frontend integration. If you want a combined developer README (run & test instructions, env setup, CI), I can add that as well.

```

```
