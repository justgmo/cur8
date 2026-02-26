from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.models import User
from app.spotify.refresh import refresh_access_token

SPOTIFY_API = "https://api.spotify.com/v1"


def get_valid_access_token(user: User, db: Session) -> str:
    """Return valid access_token for user, refreshing if expired (with buffer)."""
    token = user.token
    if token is None:
        raise ValueError("No Spotify token for user")
    if (token.expires_at - datetime.now()).total_seconds() <= 60:
        return refresh_access_token(db, token)
    return token.access_token


class SpotifyClient:
    """Thin client for Spotify Web API with a valid access token."""

    def __init__(self, access_token: str):
        self._headers = {"Authorization": f"Bearer {access_token}"}

    def _get(self, path: str, params: dict | None = None) -> dict:
        r = httpx.get(f"{SPOTIFY_API}{path}", headers=self._headers, params=params or {}, timeout=10.0)
        if r.status_code == 401:
            raise ValueError("Token expired or invalid")
        r.raise_for_status()
        return r.json()

    def get_saved_tracks(self, limit: int = 50, offset: int = 0) -> dict:
        """Call GET /v1/me/tracks. Returns Spotify response with items, total, etc."""
        return self._get("/me/tracks", params={"limit": limit, "offset": offset})

    def get_track(self, spotify_track_id: str) -> dict:
        """Call GET /v1/tracks/{id}. Returns full track object (includes preview_url)."""
        return self._get(f"/tracks/{spotify_track_id}")

    def remove_saved_track(self, spotify_track_id: str) -> None:
        """Call DELETE /v1/me/tracks. Remove track from user's Spotify library"""
        r = httpx.delete(
            f"{SPOTIFY_API}/me/tracks",
            headers = self._headers,
            params = {"ids": spotify_track_id},
            timeout = 10.0,
        )
        if r.status_code == 401:
            raise ValueError("Token expired or invalid")
        r.raise_for_status()
