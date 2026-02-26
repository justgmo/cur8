from app.auth import routes as auth_routes
from app.tracks import routes as tracks_routes
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db

settings = get_settings()

app = FastAPI(title="Cur8")

# CORS Middleware (allow_origins = comma-separated frontend URLs, e.g. https://cur8-vercel.vercel.app)
_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes and endpoints
@app.get("/health", tags=["meta"])
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}

app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(tracks_routes.router, prefix="/tracks", tags=["tracks"])