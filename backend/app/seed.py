"""Chargement des données de référence (JSON de seed) dans la base.

Le seed est idempotent : il ne s'exécute que si la base est vide, afin de ne pas
écraser les données modifiées via l'interface d'administration.

Usage :
    python -m app.seed           # seed seulement si la base est vide
    python -m app.seed --force   # réinitialise la base
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .database import Base, SessionLocal, engine
from .engine import TAUX_DEFAUT
from . import models

SEED_DIR = Path(__file__).parent / "seed_data"

CONST_KEYS = (
    "valeur_point",
    "plafond_ss",
    "smic",
    "prime_pfa_mensuel",
    "prime_segur_mensuel",
    "prime_pga_mensuel",
)


def _load(name: str):
    with open(SEED_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _ensure_constants(db) -> None:
    """Ajoute les constantes manquantes (grille + taux de cotisations)."""
    const = _load("constants.json")
    wanted: dict[str, float] = {k: float(const[k]) for k in CONST_KEYS}
    wanted.update({k: float(v) for k, v in TAUX_DEFAUT.items()})
    existing = {c.cle for c in db.query(models.Constant).all()}
    added = 0
    for cle, valeur in wanted.items():
        if cle not in existing:
            db.add(models.Constant(cle=cle, valeur=valeur))
            added += 1
    if added:
        db.commit()


def seed(force: bool = False) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not force and db.query(models.Grade).count() > 0:
            _ensure_constants(db)
            print("Base déjà initialisée — données de référence conservées ; constantes vérifiées.")
            return

        # Purge
        for m in (
            models.Grade,
            models.Ifse,
            models.SftParam,
            models.Constant,
            models.TempsPartiel,
            models.TransfertPrimePoint,
        ):
            db.query(m).delete()

        for g in _load("grades.json"):
            db.add(models.Grade(**g))
        for i in _load("ifse.json"):
            db.add(models.Ifse(**i))
        for s in _load("sft.json"):
            db.add(models.SftParam(**s))
        for t in _load("constants.json")["temps_partiel"]:
            db.add(models.TempsPartiel(**t))
        for t in _load("constants.json")["transfert_prime_point"]:
            db.add(models.TransfertPrimePoint(**t))

        db.commit()
        _ensure_constants(db)  # constantes de la grille + taux de cotisations
        print("Base seedée :")
        print(f"  grades    : {db.query(models.Grade).count()}")
        print(f"  ifse      : {db.query(models.Ifse).count()}")
        print(f"  sft       : {db.query(models.SftParam).count()}")
        print(f"  constants : {db.query(models.Constant).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    seed(force="--force" in sys.argv)
