from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID", "")
    firebase_db_url: str = os.getenv("FIREBASE_DB_URL", "")
    google_application_credentials: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    web_api_key: str = os.getenv("WEB_API_KEY", "")

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
