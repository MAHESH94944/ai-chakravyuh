from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import tasks

app = FastAPI(
    title="Startup Validator AI",
    description="An advanced, evidence-based multi-agent system to validate startup ideas.",
    version="2.0.0"
)

# --- Middleware ---
# Setup CORS to allow your React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
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