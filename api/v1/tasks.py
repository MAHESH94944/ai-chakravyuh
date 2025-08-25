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

    # Parse markdown to populate FinalReport fields with safe defaults
    import re
    from datetime import datetime

    # Executive summary: first paragraph (up to first blank line)
    paragraphs = re.split(r"\n\s*\n", report_markdown.strip())
    executive_summary = paragraphs[0].strip() if paragraphs else ""

    # Key findings: collect lines that start with '-' or '*'
    key_findings = []
    for line in report_markdown.splitlines():
        if line.strip().startswith(('-', '*')):
            key_findings.append(line.strip().lstrip('-* ').strip())

    # Recommendations section: try to extract after a 'Recommendations' header
    recommendations = []
    m = re.search(r"(?mi)^#+\s*Recommendations\s*$([\s\S]*)", report_markdown)
    if m:
        # take lines in the recommendations block
        for ln in m.group(1).splitlines():
            if ln.strip().startswith(('-', '*')):
                recommendations.append(ln.strip().lstrip('-* ').strip())

    # Confidence score: search for a percentage or number 0-100
    confidence_score = None
    m2 = re.search(r"(confidence|certainty)[:\s]*([0-9]{1,3}(?:\.[0-9]+)?)", report_markdown, re.I)
    if m2:
        try:
            confidence_score = float(m2.group(2))
        except Exception:
            confidence_score = None

    # Fallback defaults
    if confidence_score is None:
        confidence_score = 50.0
    if not key_findings:
        key_findings = [executive_summary[:200]] if executive_summary else []
    if not recommendations:
        recommendations = ["No specific recommendations generated; run targeted analysis for recommendations."]

    final = FinalReport(
        report=report_markdown,
        executive_summary=executive_summary,
        key_findings=key_findings,
        recommendations=recommendations,
        confidence_score=float(confidence_score),
        generated_at=datetime.utcnow()
    )

    return final