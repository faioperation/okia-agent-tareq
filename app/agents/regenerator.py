# app/agents/regenerator.py

import json
import httpx
from datetime import datetime
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.prompts import SYSTEM_PROMPTS

class RegeneratorAgent:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def fetch_and_regenerate(self, record_id: str):
        # dynamic URL from settings
        base_url = settings.GET_CV_DATA_FOR_REGENERATION_API
        if not base_url.endswith('/'): base_url += '/'
        fetch_url = f"{base_url}{record_id}"

        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            settings.BACKEND_AUTH_HEADER_NAME: settings.BACKEND_AUTH_TOKEN 
        }
        if "ngrok" in fetch_url.lower(): headers["ngrok-skip-browser-warning"] = "69420"

        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            try:
                response = await client.get(fetch_url)
                if response.status_code != 200:
                    return {"error": f"Backend returned {response.status_code}"}

                full_res = response.json()
                payload = full_res.get('data', {})
                if isinstance(payload, list) and len(payload) > 0: payload = payload[0]

                actual_record_id = payload.get('id')  
                actual_candidate_id = payload.get('candidateId') 
                
                candidate_info = payload.get('candidate', {})
                raw_text = candidate_info.get('rawExtractedText', '')
                c_name = candidate_info.get('candidateName', 'Candidate')

                if not raw_text:
                    return {"error": "rawExtractedText not found"}

                # AI Processing
                ai_response = await self.client.chat.completions.create(
                    model=settings.SMART_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPTS["regenerator"]},
                        {"role": "user", "content": f"Candidate ID: {actual_candidate_id}\nName: {c_name}\nCV Text: {raw_text}"}
                    ],
                    response_format={"type": "json_object"}
                )
                
                ai_json = json.loads(ai_response.choices[0].message.content)
                
                return {
                    "qualified_cv": actual_record_id,
                    "candidate_id": actual_candidate_id,
                    "structured_json": ai_json
                }

            except Exception as e:
                return {"error": f"Logic Error: {str(e)}"}