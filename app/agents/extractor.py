import asyncio
import json
import httpx
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.prompts import SYSTEM_PROMPTS
from app.engine.logic import ScoringEngine

class ExtractorAgent:
    def __init__(self):
        # Initialize OpenAI Client and Symbolic Logic Engine
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.engine = ScoringEngine()
        # Limit parallel AI requests to 20 to avoid rate limits and system overload
        self.semaphore = asyncio.Semaphore(20)

    async def extract_and_qualify(self, candidate_id, cv_text, rules):
        """
        Neural Extraction (AI) + Symbolic Evaluation (Logic) for a single CV.
        Uses a semaphore to control concurrent API calls.
        """
        async with self.semaphore:
            if not cv_text or len(cv_text.strip()) < 10:
                return {
                    "candidate_id": candidate_id,
                    "result": False,
                    "score": 0,
                    "experience": 0,
                    "missing_data": ["No valid text provided"],
                    "analysis_summary": "Empty CV content."
                }
                
            try:
                # Neural Layer: Extract facts from raw text
                response = await self.client.chat.completions.create(
                    model=settings.FAST_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPTS["extractor"]},
                        {"role": "user", "content": cv_text}
                    ],
                    response_format={"type": "json_object"}
                )
                
                extracted_data = json.loads(response.choices[0].message.content)
                
                # Symbolic Layer: Deterministic Logic Engine
                evaluation = self.engine.evaluate(extracted_data, rules)
                
                return {
                    "candidate_id": candidate_id,
                    **evaluation
                }
                
            except Exception as e:
                return {
                    "candidate_id": candidate_id,
                    "result": False,
                    "score": 0,
                    "error": f"AI Processing Error: {str(e)}"
                }

    async def fetch_bulk_and_process_task(self, rules: dict):
        """
        Fetches, processes (with 5 min timeout), pushes to backend, 
        and RETURNS results for Postman response.
        """
        headers = {
            "ngrok-skip-browser-warning": "69420",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            settings.BACKEND_AUTH_HEADER_NAME: settings.BACKEND_AUTH_TOKEN 
        }
        
        async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
            try:
                # 1. Fetch data from backend
                print(f"DEBUG: Connecting to Backend API to fetch CVs...")
                response = await client.get(settings.GET_CV_DATA_FOR_QUALIFICATION_API)
                
                if response.status_code != 200:
                    return {"error": f"Backend fetch failed with status {response.status_code}"}

                full_res = response.json()
                candidates = full_res.get('data', [])

                if not candidates:
                    return {"message": "No candidates found in backend response"}

                # 2. Create tasks for parallel execution
                tasks = []
                for person in candidates:
                    c_id = person.get('id')
                    c_text = person.get('rawExtractedText') or ""
                    tasks.append(self.extract_and_qualify(c_id, c_text, rules))

                # 3. Process all CVs with a strict 5-minute timeout
                print(f"DEBUG: Processing {len(candidates)} CVs...")
                try:
                    results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=300.0)
                except asyncio.TimeoutError:
                    print("CRITICAL: Bulk processing timed out after 5 minutes.")
                    return {"error": "Processing timed out after 5 minutes"}

                # 4. Post results back to Backend (Callback)
                # We do this so the backend database updates automatically
                try:
                    callback_payload = {
                        "status": "success",
                        "total_processed": len(results),
                        "data": results
                    }
                    print(f"DEBUG: Pushing results to backend callback...")
                    await client.post(
                        settings.POST_QUALIFICATION_RESULTS_API, 
                        json=callback_payload
                    )
                except Exception as cb_err:
                    print(f"WARNING: Callback to backend failed: {str(cb_err)}")

                # 5. Return results to main.py so they appear in Postman
                return results

            except Exception as e:
                print(f"CRITICAL ERROR: {str(e)}")
                return {"error": f"Internal agent error: {str(e)}"}