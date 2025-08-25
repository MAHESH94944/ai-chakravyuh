from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import tasks
import os
import logging

logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="Startup Validator AI",
    description="An advanced, evidence-based multi-agent system to validate startup ideas.",
    version="2.0.0"
)

# --- CORS configuration ---
# Read allowed origins from environment so the frontend (localhost or ngrok) can be allowed.
# Example: ALLOWED_ORIGINS="http://localhost:5173,https://my-staging.app" or set to "*" (not recommended with allow_credentials).
raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if not raw_origins.strip():
    # No explicit ALLOWED_ORIGINS set -> allow all origins in development for convenience.
    # Credentials are disabled to avoid wildcard+credentials issues.
    allowed_origins = ["*"]
    allow_credentials = False
    logger = logging.getLogger("uvicorn.error")
    logger.warning("ALLOWED_ORIGINS not set; defaulting to wildcard '*' for development (credentials disabled). Set ALLOWED_ORIGINS in production.)")
else:
    if raw_origins.strip() == "*":
        allowed_origins = ["*"]
    else:
        allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
    # If wildcard is used, do not allow credentials per the CORS spec
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


@app.on_event("startup")
async def _startup_log():
    # Log the allowed origins so it's visible in server logs for debugging
    logger.info(f"CORS allowed_origins: {allowed_origins}")


# Debug endpoint to verify routing and CORS behavior from the frontend/ngrok
@app.get("/api/v1/ping", tags=["Health Check"])
async def ping(request: Request):
    """Simple ping that echoes configured allowed origins and caller Origin header."""
    origin = request.headers.get('origin')
    return {
        "status": "ok",
        "allowed_origins": allowed_origins,
        "request_origin": origin
    }

# --- API Routers ---
# Include the endpoints from your tasks.py file
app.include_router(tasks.router, prefix="/api/v1")

# --- Basic Health Check Endpoint ---
@app.get("/", tags=["Health Check"])
def read_root():
    """A simple health check endpoint to confirm the API is running."""
    return {"status": "ok", "message": "Startup Validator API is running."}