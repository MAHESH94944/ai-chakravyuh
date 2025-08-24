from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import tasks  # Import the tasks router

# Local import to avoid issues when running tests without full envs
from core.config import settings


app = FastAPI(
    title="Startup Idea Validator API",
    description="An AI-powered multi-agent system to validate startup ideas.",
    version="0.1.0",
)

# Configure CORS from settings (allow localhost dev + optional env-configured origins)
_allowed = []
if getattr(settings, "ALLOWED_ORIGINS", None):
    # ALLOWED_ORIGINS may be a comma-separated string
    _allowed = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
else:
    # sensible defaults for local frontend dev and common ngrok patterns
    _allowed = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]
    # Allow ngrok tunnels (wildcard) if running behind ngrok during dev
    _allowed.append("https://*.ngrok-free.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include the router from api/v1/tasks.py
# All routes defined in that file will now be part of our app,
# prefixed with /api/v1
app.include_router(tasks.router, prefix="/api/v1")
# Also expose the same endpoints at the root (no prefix) for backwards compatibility
app.include_router(tasks.router, prefix="")


@app.on_event("startup")
async def _startup_event():
    # Access settings to trigger any validation/initialization.
    # This will also fail fast if required API keys are missing when using
    # the pydantic-settings implementation.
    if getattr(settings, "DEBUG", False):
        print("Starting in DEBUG mode")


@app.get("/")
async def read_root():
    """A simple endpoint to confirm the API is running."""
    return {"status": "ok", "message": "Welcome to the Startup Idea Validator API!"}


__all__ = ["app"]