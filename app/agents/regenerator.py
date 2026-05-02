import json
import httpx
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.prompts import SYSTEM_PROMPTS

class RegeneratorAgent:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def fetch_and_regenerate(self, record_id: str):
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
                    return {"error": f"Backend fetch failed: {response.status_code}"}

                full_res = response.json()
                payload = full_res.get('data', {})
                if isinstance(payload, list) and len(payload) > 0: payload = payload[0]

                candidate_info = payload.get('candidate', {})
                raw_text = candidate_info.get('rawExtractedText', '')
                real_email = candidate_info.get('emailAddress', 'N/A')
                real_phone = candidate_info.get('contactNumber', 'N/A')
                real_name = candidate_info.get('candidateName', 'Candidate')
                real_job = candidate_info.get('jobTitle', 'Professional')
                actual_candidate_id = payload.get('candidateId')

                prompt_content = (
                    f"Candidate ID: {actual_candidate_id}\n"
                    f"Full Name: {real_name}\n"
                    f"Job Title: {real_job}\n"
                    f"Real Contact: {real_email} / {real_phone}\n\n"
                    f"CV TEXT CONTENT:\n{raw_text}"
                )

                # AI Processing
                ai_response = await self.client.chat.completions.create(
                    model=settings.SMART_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPTS["regenerator"]},
                        {"role": "user", "content": prompt_content}
                    ],
                    response_format={"type": "json_object"}
                )
                
                ai_json = json.loads(ai_response.choices[0].message.content)
                
                return {
                    "qualified_cv": record_id,
                    "candidate_id": actual_candidate_id,
                    "structured_json": ai_json
                }

            except Exception as e:
                return {"error": f"Agent Logic Error: {str(e)}"}