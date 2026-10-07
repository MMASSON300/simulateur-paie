"""Route d'authentification administrateur."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth import check_password, create_token, require_admin
from ..schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    if not check_password(payload.password):
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    return {"token": create_token()}


@router.get("/verify")
def verify(_: None = Depends(require_admin)):
    return {"status": "ok"}
