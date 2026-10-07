"""Authentification simple par mot de passe + jeton signé (stdlib uniquement).

Le jeton est un HMAC-SHA256 horodaté signé avec le mot de passe administrateur.
Aucune dépendance supplémentaire n'est requise.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

from fastapi import Header, HTTPException

from .config import ADMIN_PASSWORD, SESSION_TTL


def _sign(payload: str) -> str:
    return hmac.new(ADMIN_PASSWORD.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def create_token() -> str:
    expiry = int(time.time()) + SESSION_TTL
    payload = str(expiry)
    sig = _sign(payload)
    raw = f"{payload}.{sig}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def verify_token(token: str | None) -> bool:
    if not token:
        return False
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        payload, sig = raw.rsplit(".", 1)
        if not hmac.compare_digest(_sign(payload), sig):
            return False
        return int(payload) > int(time.time())
    except (ValueError, TypeError, UnicodeDecodeError):
        return False


def check_password(password: str) -> bool:
    return hmac.compare_digest(password, ADMIN_PASSWORD)


def require_admin(authorization: str | None = Header(default=None)) -> None:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Authentification requise")
