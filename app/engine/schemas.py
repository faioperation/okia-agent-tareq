from pydantic import BaseModel
from typing import List, Optional

class EdukaiCV(BaseModel):
    first_name: str
    last_name: str = ""
    professional_titles: str
    location: str
    email: str
    phone: str
    professional_profile: str
    employment_history: List[dict]
    education_qualifications: List[dict]
    skills: List[str]