import base64
import hashlib
import os

def generate_code_verifier(length: int = 64) -> str:
    """Return PKCE code verifier (random, url-safe base64)."""
    return base64.urlsafe_b64encode(os.urandom(length)).decode("utf-8").rstrip("=")


def generate_state(length: int = 32) -> str:
    """Return PKCE state (random, url-safe base64)."""
    return base64.urlsafe_b64encode(os.urandom(length)).decode("utf-8").rstrip("=")


def generate_code_challenge(verifier: str) -> str:
    """Return S256 code challenge from verifier."""
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")