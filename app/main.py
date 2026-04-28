import uvicorn
import json
import asyncio
from fastapi import FastAPI, Request, HTTPException, Depends
from app.core.config import settings
from app.agents.extractor import ExtractorAgent
from app.agents.regenerator import RegeneratorAgent
from app.agents.emailer import EmailerAgent

# Initialize FastAPI App
app = FastAPI(title=settings.PROJECT_NAME)

# Initialize Agents
extractor = ExtractorAgent()
regenerator = RegeneratorAgent()
emailer = EmailerAgent()

# --- Security Logic ---
async def verify_token(request: Request):
    """
    Checks for the custom security token in the request headers.
    """
    token = request.headers.get(settings.API_SECURITY_HEADER_NAME)
    if token != settings.API_SECURITY_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid Security Token")
    return token

# --- Helper Logic ---
async def get_payload(request: Request):
    """
    Manually parses the raw request body as JSON to bypass Content-Type requirements.
    """
    try:
        body = await request.body()
        return json.loads(body) if body else {}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

# --- Routes ---

@app.get("/")
async def root():
    return {"status": "Edukai AI Agent is active"}

# Agent 1: Bulk Qualify (Analyzes and scores 1-500 CVs)
@app.post(f"{settings.API_V1_STR}/ai/qualify", dependencies=[Depends(verify_token)])
async def qualify_cvs(request: Request):
    payload = await get_payload(request)
    rules = payload.get("rules", {})
    
    if not rules:
        raise HTTPException(status_code=400, detail="Rules are required for qualification.")

    # Process and return results directly to Postman
    results = await extractor.fetch_bulk_and_process_task(rules)
    
    return {
        "status": "success", 
        "processed_count": len(results) if isinstance(results, list) else 0,
        "data": results
    }

# Agent 2: Individual CV Regeneration (ID-based)
@app.post(f"{settings.API_V1_STR}/ai/cv-generate/{{record_id}}", dependencies=[Depends(verify_token)])
async def finalize_cv_generation(record_id: str, request: Request):
    """
    Triggered by Record ID.
    Returns 'qualified_cv' as the Record ID and 'data' as the AI structured JSON.
    """
    print(f"DEBUG: Triggering generation for Record ID: {record_id}")

    # The regenerator now returns a dict containing both IDs and the structured JSON
    result = await regenerator.fetch_and_regenerate(record_id)
    
    # Handle failures during fetch or AI processing
    if isinstance(result, dict) and "error" in result:
        return {
            "status": "failed",
            "qualified_cv": record_id,
            "error_detail": result["error"]
        }

    # Final response mapping
    # qualified_cv = The ID of the quality check record (from URL)
    # data.metadata.candidate_id = The actual Profile ID of the candidate
    return {
        "status": "success",
        "qualified_cv": result.get("qualified_cv"), 
        "data": result.get("structured_json")
    }
# Agent 3: Email Generation (ID-based)
emailer_agent = EmailerAgent()

@app.post(f"{settings.API_V1_STR}/ai/mailGen/{{cv_id}}", dependencies=[Depends(verify_token)])
async def generate_email_handler(cv_id: str, request: Request):
    """
    Fetches generated CV by ID and returns professional pitch email.
    """
    print(f"DEBUG: Request received for Email Generation: {cv_id}")
    
    email_result = await emailer_agent.fetch_and_generate_email(cv_id)
    
    if isinstance(email_result, dict) and "error" in email_result:
        raise HTTPException(status_code=500, detail=email_result["error"])

    return {
        "status": "success",
        "cv_id": cv_id,
        "data": email_result
    }

# --- Entry Point ---
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8080, 
        reload=True, 
        reload_dirs=["app"]
    )