from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .db import Base

class User(Base):
    """User relation for SQL"""
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spotify_user_id = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    track_states = relationship("UserTrackState", back_populates="user")
    token = relationship("SpotifyToken", back_populates="user", uselist=False)


class SpotifyToken(Base):
    """SpotifyToken relation for SQL"""
    __tablename__ = "spotify_tokens"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="token")


class Track(Base):
    """Track relation for SQL"""
    __tablename__ = "tracks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spotify_track_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    artists = Column(String, nullable=True)
    album_name = Column(String, nullable=True)
    artwork_url = Column(String, nullable=True)
    preview_url = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    user_states = relationship("UserTrackState", back_populates="track")

class UserTrackState(Base):
    """Per-user, per track: pending | kept | removed"""
    __tablename__ = "user_track_states"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    track_id = Column(UUID(as_uuid=True), ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    state = Column(String(20), nullable=False)  # "pending" | "kept" | "removed"
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="track_states")
    track = relationship("Track", back_populates="user_states")