from pydantic import BaseModel, Field
from typing import Literal


class IdeaInput(BaseModel):
    """Shape of the input JSON for the validation request."""
    idea: str = Field(..., min_length=1, description="A short description of the startup idea")


class TaskResponse(BaseModel):
    """Initial response after a task is submitted."""
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    message: str


__all__ = ["IdeaInput", "TaskResponse"]

# models/schemas.py (add this class)

class FinalReport(BaseModel):
    report: str