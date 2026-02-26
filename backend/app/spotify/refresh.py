from datetime import datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import SpotifyToken

settings = get_settings()
TOKEN_URL = "https://accounts.spotify.com/api/token"

BUFFER_SECONDS = 60


def refresh_access_token(db: Session, token: SpotifyToken) -> str:
    """Refresh Spotify token and update in DB."""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": token.refresh_token,
        "client_id": settings.spotify_client_id,
    }
    with httpx.Client() as client:
        resp = client.post(TOKEN_URL, data=data)
    if resp.status_code != 200:
        raise ValueError(f"Spotify refresh failed: {resp.text}")

    j = resp.json()
    token.access_token = j["access_token"]
    token.expires_at = datetime.now() + timedelta(seconds=int(j.get("expires_in", 3600)))
    if "refresh_token" in j:
        token.refresh_token = j["refresh_token"]
    db.commit()
    return token.access_token
