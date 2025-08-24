from .base_agent import BaseAgent
from core.clients import gemini_model
from models.schemas import TechnicalFeasibilityResult
import json
from typing import Dict, Any
import time


def _call_gemini(prompt: str, retries: int = 2, delay: float = 1.0) -> str:
    """Call the Gemini model with simple retry/backoff and return the raw text."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            # Use the existing wrapper on gemini_model (keeps compatibility with current client)
            resp = gemini_model.generate_content(prompt)
            text = getattr(resp, "text", None) or str(resp)
            return text
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(delay * attempt)
            else:
                raise
    raise last_err


class TechnicalFeasibilityAgent(BaseAgent):
    """
    Advanced TechnicalFeasibilityAgent. Produces a deep, multi-section technical
    assessment including architecture, data pipeline, infra, security, prototype
    plan, timeline, cost estimate, and team roles. Outputs are validated and
    repaired to a strict JSON format when necessary.
    """

    def run(self, idea: str) -> Dict[str, Any]:
        print(f"🛠 TechnicalFeasibilityAgent: analyzing idea: {idea}")

        # Primary prompt asks for a strict JSON containing detailed sections.
        primary_prompt = f"""
        You are a seasoned Chief Technology Officer and systems architect. Provide a detailed technical feasibility analysis for the startup idea below.

        Startup idea:
        "{idea}"

        Produce a single JSON object with the following keys:
        - key_challenges: list of top 5 technical risks or challenges (short bullets)
        - suggested_stack: an object with frontend, backend, database, cache, messaging, ai_ml, infra (cloud provider), and recommended managed services or OSS components
        - architecture_overview: short textual system architecture description (components and data flow)
        - data_pipeline: how data will be collected, stored, and processed (batch/streaming), privacy considerations
        - infra_scaling: scaling strategy (stateless/services, autoscaling, CDNs, sharding)
        - security_and_privacy: main security controls and compliance flags
        - integrations: list of likely third-party integrations and why
        - prototype_plan: step-by-step 90-day MVP plan with milestones
        - timeline_estimate: object with phases and durations
        - cost_estimate: rough monthly cost bands (dev, staging, prod)
        - team_roles: list of required roles to build the first product
        - non_functional_requirements: latency, throughput, availability targets
        - feasibility: one of ["feasible","feasible_with_research","high_risk"]
        - confidence_score: integer 0-100 (confidence in the assessment)

        Keep answers concise. Return only valid JSON. If any value is unknown, use a short explanation string.
        """

        try:
            raw = _call_gemini(primary_prompt, retries=2)
            cleaned = raw.strip().replace('```json', '').replace('```', '').strip()
            try:
                parsed = json.loads(cleaned)
            except Exception:
                # Attempt a repair pass asking Gemini to reformat into strict JSON
                repair_prompt = f"""
                The following output is intended to be strict JSON but may be malformed. Reformat it into valid JSON that matches the required keys.

                INPUT:
                {cleaned[:8000]}

                Return only the JSON object.
                """
                repair_raw = _call_gemini(repair_prompt, retries=1)
                repair_text = repair_raw.strip().replace('```json', '').replace('```', '').strip()
                parsed = json.loads(repair_text)

            # Minimal validation: ensure required keys exist
            if not isinstance(parsed, dict):
                return {"error": "Parsed response is not a JSON object"}

            # Ensure the two schema fields exist at minimum
            if "key_challenges" not in parsed or "suggested_stack" not in parsed:
                # try to coerce or reconstruct a minimal response
                minimal = {
                    "key_challenges": parsed.get("key_challenges") or parsed.get("challenges") or [],
                    "suggested_stack": parsed.get("suggested_stack") or parsed.get("stack") or {},
                }
                # merge back other keys if present
                for k, v in parsed.items():
                    if k not in minimal:
                        minimal[k] = v
                parsed = minimal

            # Validate using Pydantic model (will raise if types are wrong)
            try:
                tf = TechnicalFeasibilityResult.parse_obj(parsed)
                out = tf.dict()
                # include extra fields if present in parsed
                for k, v in parsed.items():
                    if k not in out:
                        out[k] = v
                out["feasibility_status"] = out.get("feasibility", "unknown")
                out["confidence_score"] = out.get("confidence_score", None)
                return out
            except Exception as ve:
                # If validation fails, attempt a last-ditch repair: ask Gemini to output only keys required by schema
                repair_prompt = f"""
                Reformat the following analysis into a strict JSON object containing at least these keys: key_challenges (list), suggested_stack (object with frontend, backend, database, ai_ml).

                INPUT:
                {json.dumps(parsed, indent=2)[:8000]}

                Return only the JSON.
                """
                repair_raw = _call_gemini(repair_prompt, retries=1)
                repair_text = repair_raw.strip().replace('```json', '').replace('```', '').strip()
                repaired = json.loads(repair_text)
                tf = TechnicalFeasibilityResult.parse_obj(repaired)
                out = tf.dict()
                # attach a flag that this was repaired
                out["repaired"] = True
                return out

        except Exception as e:
            print(f"TechnicalFeasibilityAgent failed: {e}")
            return {"error": f"Technical feasibility analysis failed: {e}"}
