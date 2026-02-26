from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Track, User, UserTrackState
from app.spotify import SpotifyClient, get_valid_access_token


def _track_from_spotify_item(item: dict) -> dict:
    """Build Track fields from Spotify /me/tracks item."""
    t = item["track"]
    artists = ", ".join(a["name"] for a in t.get("artists", []))
    images = t.get("album", {}).get("images") or []
    artwork = images[0]["url"] if images else None
    return {
        "spotify_track_id": t["id"],
        "name": t["name"],
        "artists": artists or None,
        "album_name": t.get("album", {}).get("name"),
        "artwork_url": artwork,
        "preview_url": t.get("preview_url"),
        "duration_ms": t.get("duration_ms"),
    }


def sync_saved_tracks_for_user(user: User, db: Session, spotify_client: SpotifyClient, limit: int = 50) -> None:
    """Fetch from Spotify, upsert Track and UserTrackState (pending) for user."""
    offset = 0
    while True:
        data = spotify_client.get_saved_tracks(limit=limit, offset=offset)
        items = data.get("items") or []
        if not items:
            break
        for item in items:
            tid = item["track"]["id"]
            fields = _track_from_spotify_item(item)
            track = db.query(Track).filter_by(spotify_track_id=tid).first()
            if track is None:
                track = Track(**fields)
                db.add(track)
                db.flush()
            else:
                # Backfill preview_url and other fields from Spotify (e.g. after adding preview_url column)
                for k, v in fields.items():
                    setattr(track, k, v)
            state = db.query(UserTrackState).filter_by(user_id=user.id, track_id=track.id).first()
            if state is None:
                state = UserTrackState(user_id=user.id, track_id=track.id, state="pending")
                db.add(state)
        offset += len(items)
        if len(items) < limit:
            break
    db.commit()
    

def get_next_track(user: User, db: Session) -> Track | None:
    """Return next pending track for user (random order)."""
    row = (
        db.query(Track)
        .join(UserTrackState, (UserTrackState.track_id == Track.id) & (UserTrackState.user_id == user.id))
        .filter(UserTrackState.state == "pending")
        .order_by(func.random())
        .first()
    )
    return row