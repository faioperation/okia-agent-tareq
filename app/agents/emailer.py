import json
import httpx
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.prompts import SYSTEM_PROMPTS

class EmailerAgent:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def fetch_and_generate_email(self, cv_id: str):
        base_url = settings.GET_GENERATED_CV_API
        if not base_url.endswith('/'): base_url += '/'
        fetch_url = f"{base_url}{cv_id}"

        headers = {
            "Accept": "application/json",
            "ngrok-skip-browser-warning": "69420",
            settings.BACKEND_AUTH_HEADER_NAME: settings.BACKEND_AUTH_TOKEN 
        }

        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            try:
                # 1. Fetch CV data from Backend
                response = await client.get(fetch_url)
                full_res = response.json()
                cv_json = full_res.get('data', {})
                if isinstance(cv_json, list) and len(cv_json) > 0: cv_json = cv_json[0]

                # Extract Candidate Name for Greeting
                first_name = cv_json.get("header", {}).get("first_name", "Hiring Manager")

                # 2. AI Generation
                ai_res = await self.client.chat.completions.create(
                    model=settings.FAST_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPTS["emailer"]},
                        {"role": "user", "content": f"CV DATA: {json.dumps(cv_json)}"}
                    ],
                    response_format={"type": "json_object"}
                )
                ai_data = json.loads(ai_res.choices[0].message.content)

                # 3. Assemble the FINAL Nested JSON structure as per your request
                return {
                    "metadata": {
                        "candidate_id": cv_id,
                        "target_client": first_name,
                        "brand": "EDUKAI RECRUITMENT"
                    },
                    "email_content": {
                        "subject_options": ai_data.get("subject_options", []),
                        "subject": ai_data.get("subject"),
                        "salutation": f"Dear {first_name},",
                        "intro_paragraph": ai_data.get("intro"),
                        "key_highlights": [
                            {"icon": "✅", "title": "Extensive Expertise", "description": ai_data.get("expertise_desc")},
                            {"icon": "🎓", "title": "Project Delivery", "description": ai_data.get("project_desc")},
                            {"icon": "💡", "title": "Technical Proficiency", "description": ai_data.get("technical_desc")},
                            {"icon": "🤝", "title": "Soft Skills and Collaboration", "description": ai_data.get("soft_skills_desc")}
                        ],
                        "impact_statement": ai_data.get("impact"),
                        "closing_statement": "Best regards,\nEdukai Recruitment Team",
                        "nb_footer": "NB. If you have another vacancy for another role, simply drop me an email with your requirement(s) and I will send you our best matched candidates. (this is a generic email so journey times to your school for your chosen candidate(s) would have to be explored before an interview/trial is arranged)"
                    },
                    "signature_block": {
                        "name": "Kai Smith",
                        "designation": "Director, Edukai Recruitment",
                        "contact": {
                            "phone": "0203 987 9981",
                            "mobile": "07542 870 343",
                            "website": "www.edukai.co.uk",
                            "address": "Unit A3, Broomleigh Business Park, Worsley Bridge Rd, London, SE26 5BN"
                        }
                    }
                }

            except Exception as e:
                return {"error": f"Emailer Agent Error: {str(e)}"}