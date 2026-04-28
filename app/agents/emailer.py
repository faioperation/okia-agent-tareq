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
        fetch_url = f"{base_url}{cv_id}" if base_url.endswith('/') else f"{base_url}/{cv_id}"

        headers = {
            "Accept": "application/json",
            "ngrok-skip-browser-warning": "69420",
            settings.BACKEND_AUTH_HEADER_NAME: settings.BACKEND_AUTH_TOKEN 
        }

        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            try:
                # 1. Fetching logic
                response = await client.get(fetch_url)
                res_data = response.json().get('data', {})
                if isinstance(res_data, list) and len(res_data) > 0: res_data = res_data[0]

                # Extracting Name for Dynamic Greeting
                # If first_name is MD or empty, try to get something better
                first_name = res_data.get("header", {}).get("first_name", "Hiring Manager")
                if first_name.lower() in ["md", "mr", "ms"]:
                    # Fallback to a professional greeting if only title is found
                    salutation_name = "Hiring Manager"
                else:
                    salutation_name = first_name

                # 2. AI Generation
                print(f"DEBUG: Generating AI Content for {salutation_name}...")
                ai_res = await self.client.chat.completions.create(
                    model=settings.FAST_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPTS["emailer"]},
                        {"role": "user", "content": f"Candidate Data: {json.dumps(res_data)}"}
                    ],
                    response_format={"type": "json_object"}
                )
                
                ai_output = json.loads(ai_res.choices[0].message.content)

                # 3. Final Structure Assembly (Strictly matching your desired format)
                return {
                    "metadata": {
                        "candidate_id": cv_id,
                        "target_client": salutation_name,
                        "brand": "EDUKAI RECRUITMENT"
                    },
                    "email_content": {
                        "subject": ai_output.get("subject"),
                        "salutation": f"Dear {salutation_name},",
                        "intro_paragraph": ai_output.get("intro"),
                        "key_highlights": ai_output.get("highlights", []),
                        "impact_statement": ai_output.get("impact"),
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
                print(f"ERROR: {str(e)}")
                return {"error": str(e)}