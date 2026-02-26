from datetime import datetime, timedelta
from uuid import UUID
from typing import Annotated
from urllib.parse import urlencode

import httpx
from app.auth.pkce import (generate_code_challenge, generate_code_verifier,
                           generate_state)
from app.auth.pkce_store import pop_pkce_verifier, save_pkce_state
from app.auth.session_store import create_session, delete_session, get_session
from app.config import get_settings
from app.db import get_db
from app.models import SpotifyToken, User
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

router = APIRouter()
settings = get_settings()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Load current user from session cookie."""
    session_id = request.cookies.get("cur8_session")
    user_id_str = get_session(session_id) if session_id else None
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).get(UUID(user_id_str))
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    spotify_user_id: str
    display_name: str | None
    avatar_url: str | None


@router.get("/redirect-uri")
def debug_redirect_uri() -> dict:
    """Temporary: returns the redirect_uri this app sends to Spotify. Compare with Spotify Dashboard."""
    return {"redirect_uri": settings.spotify_redirect_uri}


@router.get("/login")
def login() -> dict:
    """Build PKCE authorize URL for Spotify."""
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)
    state = generate_state()
    save_pkce_state(state, verifier)

    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
        "state": state,
        "scope": "user-library-read user-library-modify"
    }

    authorize_url = "https://accounts.spotify.com/authorize?" + urlencode(params)
    return {"authorization_url": authorize_url}


@router.get("/callback")
def callback(
    code: Annotated[str, Query(..., description="Authorization code from Spotify")],
    state: Annotated[str, Query(..., description="PKCE state value")],
    db: Session = Depends(get_db)
):
    """Exchange code for tokens, fetch profile, upsert user and token in DB."""
    verifier = pop_pkce_verifier(state)
    if verifier is None:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.spotify_redirect_uri,
        "client_id": settings.spotify_client_id,
        "code_verifier": verifier
    }

    with httpx.Client() as client:
        token_response = client.post(token_url, data=data)
    if token_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Spotify token exchange failed: {token_response.text}"
        )
    
    token_json = token_response.json()
    access_token = token_json["access_token"]
    refresh_token = token_json.get("refresh_token")
    scope = token_json.get("scope", "")
    expires_in = int(token_json.get("expires_in", 3600))
    expires_at = datetime.now() + timedelta(seconds=expires_in)

    if not refresh_token:
        raise HTTPException(
            status_code=502,
            detail="No refresh token returned from Spotify"
        )

    with httpx.Client(headers={"Authorization": f"Bearer {access_token}"}) as client:
        me_response = client.get("https://api.spotify.com/v1/me")
    if me_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch Spotify profile: {me_response.text}"
        )

    me = me_response.json()
    spotify_user_id = me["id"]
    display_name = me.get("display_name")
    images = me.get("images") or []
    avatar_url = images[0]["url"] if images else None

    # Upsert User and SpotifyToken in db
    user = db.query(User).filter_by(spotify_user_id=spotify_user_id).first()
    if user is None:
        user = User(
            spotify_user_id=spotify_user_id,
            display_name=display_name,
            avatar_url=avatar_url,
        )
        db.add(user)
        db.flush()  # so user.id is available

    token = db.query(SpotifyToken).filter_by(user_id=user.id).first()
    if token is None:
        token = SpotifyToken(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            scope=scope,
            expires_at=expires_at,
        )
        db.add(token)
    else:
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.scope = scope
        token.expires_at = expires_at

    db.commit()

    session_id = create_session(user.id)
    response = RedirectResponse(url=settings.frontend_url, status_code=302)
    is_prod = settings.environment == "production"
    response.set_cookie(
        key="cur8_session",
        value=session_id,
        httponly=True,
        samesite="none" if is_prod else "lax",  # none required for cross-origin (Vercel → Railway)
        path="/",
        max_age=7 * 24 * 3600,  # 7 days
        secure=is_prod,
    )
    return response


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    """Return current user (from session)."""
    return current_user


@router.post("/logout")
def logout(request: Request):
    """Invalid session and clear session cookie"""
    session_id = request.cookies.get("cur8_session")
    if session_id:
        delete_session(session_id)
    response = JSONResponse(content={"status": "ok"})
    is_prod = settings.environment == "production"
    response.delete_cookie(
        key="cur8_session",
        path="/",
        secure=is_prod,
        samesite="none" if is_prod else "lax",
    )
    return response