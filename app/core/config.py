from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str
    OPENAI_API_KEY: str
    API_SECURITY_HEADER_NAME: str
    API_SECURITY_TOKEN: str
    FAST_MODEL: str
    SMART_MODEL: str
    REDIS_URL: str
    API_V1_STR: str = "/api/v1"
    GET_CV_DATA_FOR_QUALIFICATION_API: str
    BACKEND_AUTH_HEADER_NAME: str
    BACKEND_AUTH_TOKEN: str
    GET_CV_DATA_FOR_REGENERATION_API: str = ""
    GET_GENERATED_CV_API: str = ""


    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()