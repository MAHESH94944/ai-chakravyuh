from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import tasks
import os

app = FastAPI(
    title="Startup Validator AI",
    description="An advanced, evidence-based multi-agent system to validate startup ideas.",
    version="2.0.0"
)

# --- CORS configuration ---
# Read allowed origins from environment so the frontend (localhost or ngrok) can be allowed.
# Example: ALLOWED_ORIGINS="http://localhost:5173,https://my-staging.app" or set to "*" (not recommended with allow_credentials).
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
if raw_origins.strip() == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

# If wildcard is used, do not allow credentials per the CORS spec (browsers will ignore wildcard + credentials).
allow_credentials = True
if allowed_origins == ["*"]:
    allow_credentials = False

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
# Include the endpoints from your tasks.py file
app.include_router(tasks.router, prefix="/api/v1")

# --- Basic Health Check Endpoint ---
@app.get("/", tags=["Health Check"])
def read_root():
    """A simple health check endpoint to confirm the API is running."""
    return {"status": "ok", "message": "Startup Validator API is running."}