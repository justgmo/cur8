from datetime import datetime
from typing import Annotated
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.routes import get_current_user
from app.db import get_db
from app.models import Track, User, UserTrackState
from app.spotify import SpotifyClient, check_rate_limit, get_valid_access_token
from sqlalchemy.orm import Session
from app.tracks.service import get_next_track, sync_saved_tracks_for_user

router = APIRouter()


class SwipeBody(BaseModel):
    spotify_track_id: str
    action: str  # "keep" | "remove"

class TrackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    spotify_track_id: str
    name: str
    artists: str | None
    album_name: str | None
    artwork_url: str | None
    preview_url: str | None
    duration_ms: int | None


@router.get("/next", response_model=TrackResponse | None)
def get_next(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return next pending track for the current user; sync from Spotify if needed."""
    check_rate_limit(current_user.id)
    access_token = get_valid_access_token(current_user, db)
    client = SpotifyClient(access_token)
    next_track = get_next_track(current_user, db)
    if next_track is None:
        sync_saved_tracks_for_user(current_user, db, client)
        next_track = get_next_track(current_user, db)
    if next_track is None:
        return None
    # Backfill preview_url from Spotify if we don't have it (e.g. old rows or /me/tracks omitted it)
    if next_track.preview_url is None:
        try:
            spotify_track = client.get_track(next_track.spotify_track_id)
            if spotify_track.get("preview_url"):
                next_track.preview_url = spotify_track["preview_url"]
                db.commit()
        except Exception:
            pass
    return next_track


@router.post("/swipe")
def swipe(
    body: SwipeBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record keep or remove; for remove, also call Spotify to remove from library."""
    if body.action not in ("keep", "remove"):
        raise HTTPException(400, "action must be 'keep' or 'remove'")
    check_rate_limit(current_user.id)
    track = db.query(Track).filter_by(spotify_track_id=body.spotify_track_id).first()
    if not track:
        raise HTTPException(404, "Track not found")
    state = db.query(UserTrackState).filter_by(user_id=current_user.id, track_id=track.id).first()
    if not state or state.state != "pending":
        raise HTTPException(400, "Track not pending")
    state.state = "kept" if body.action == "keep" else "removed"
    state.updated_at = datetime.now()
    if body.action == "remove":
        access_token = get_valid_access_token(current_user, db)
        SpotifyClient(access_token).remove_saved_track(body.spotify_track_id)
    db.commit()
    return {"status": "ok"}


@router.get("/saved")
def saved_tracks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Return current user's saved tracks from Spotify (rate-limited)."""
    check_rate_limit(current_user.id)
    try:
        access_token = get_valid_access_token(current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    client = SpotifyClient(access_token)
    return client.get_saved_tracks(limit=limit, offset=offset)