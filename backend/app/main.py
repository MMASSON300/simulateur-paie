"""Point d'entrée FastAPI."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import auth, reference, simulation

app = FastAPI(title="Simulateur de salaire", version="1.2026.10")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(simulation.router)
app.include_router(reference.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Sert le frontend compilé lorsqu'il est présent (déploiement conteneurisé).
# En développement, le frontend est servi séparément par Vite.
STATIC_DIR = Path(os.getenv("STATIC_DIR", Path(__file__).resolve().parent.parent / "static"))
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
