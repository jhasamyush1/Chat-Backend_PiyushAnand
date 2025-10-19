from fastapi import FastAPI
import firebase_admin
from firebase_admin import credentials, db
from app.core.config import get_settings
from app.routers import rooms, messages
from app.ws import rooms as ws_rooms

def init_firebase():
    settings = get_settings()
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.google_application_credentials)
        firebase_admin.initialize_app(cred, {
            "projectId": settings.firebase_project_id,
            "databaseURL": settings.firebase_db_url,
        })

def create_app() -> FastAPI:
    init_firebase()
    app = FastAPI(title="Chat Backend (FastAPI + Firebase)")
    app.include_router(rooms.router)
    app.include_router(messages.router)
    app.include_router(ws_rooms.router)
    return app

app = create_app()
