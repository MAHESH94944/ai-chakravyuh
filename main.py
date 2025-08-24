from fastapi import FastAPI
from api.v1 import tasks  # Import the tasks router

# Local import to avoid issues when running tests without full envs
from core.config import settings


app = FastAPI(
    title="Startup Idea Validator API",
    description="An AI-powered multi-agent system to validate startup ideas.",
    version="0.1.0",
)


# Include the router from api/v1/tasks.py
# All routes defined in that file will now be part of our app,
# prefixed with /api/v1
app.include_router(tasks.router, prefix="/api/v1")


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