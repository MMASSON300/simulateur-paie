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


def seed(force: bool = False) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not force and db.query(models.Grade).count() > 0:
            print("Base déjà initialisée — seed ignoré (utilisez --force pour réinitialiser).")
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

        const = _load("constants.json")
        for k in CONST_KEYS:
            db.add(models.Constant(cle=k, valeur=const[k]))

        db.commit()
        print("Base seedée :")
        print(f"  grades    : {db.query(models.Grade).count()}")
        print(f"  ifse      : {db.query(models.Ifse).count()}")
        print(f"  sft       : {db.query(models.SftParam).count()}")
        print(f"  constants : {db.query(models.Constant).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    seed(force="--force" in sys.argv)
