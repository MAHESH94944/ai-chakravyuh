from fastapi import APIRouter, HTTPException
from models.schemas import IdeaInput, FinalReport
from coordinator.workflow import run_full_analysis, synthesize_final_report

router = APIRouter()


@router.post("/validate-idea", response_model=FinalReport)
def validate_idea(idea_input: IdeaInput):
    """
    Accepts a startup idea and returns a full, synthesized feasibility report.
    """
    if not idea_input.idea:
        raise HTTPException(status_code=400, detail="Idea text cannot be empty.")

    # Step 1: Run the full orchestration to gather data from all agents
    print("--- Calling Coordinator to run full analysis ---")
    analysis_context = run_full_analysis(idea=idea_input.idea, location=idea_input.location or None)
    
    if "error" in analysis_context:
        raise HTTPException(status_code=500, detail=analysis_context["error"])
    print("--- Coordinator finished data gathering ---")


    # Step 2: Synthesize the final report using all the collected data
    print("--- Calling Coordinator to synthesize final report ---")
    report_markdown = synthesize_final_report(analysis_context)
    
    if "Error:" in report_markdown:
        raise HTTPException(status_code=500, detail=report_markdown)
    print("--- Final report synthesized ---")

    return FinalReport(report=report_markdown)