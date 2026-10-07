"""Routes de simulation."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..engine import compute
from ..reference import build_reference_from_db
from ..schemas import Options, SimulationRequest, SimulationResponse
from .. import models

router = APIRouter(prefix="/api", tags=["simulation"])


@router.post("/simuler", response_model=SimulationResponse)
def simuler(payload: SimulationRequest, db: Session = Depends(get_db)):
    ref = build_reference_from_db(db)
    return compute(ref, payload.model_dump())


@router.get("/options", response_model=Options)
def options(db: Session = Depends(get_db)):
    grades = db.query(models.Grade).all()
    ifse = db.query(models.Ifse).all()
    temps = db.query(models.TempsPartiel).order_by(models.TempsPartiel.quotite.desc()).all()

    filieres = sorted({g.filiere for g in grades if g.filiere})
    cadres_par_filiere: dict[str, list[str]] = {}
    grades_par_cadre: dict[str, list[str]] = {}
    for g in grades:
        if not g.filiere or not g.cadre:
            continue
        cadres_par_filiere.setdefault(g.filiere, [])
        if g.cadre not in cadres_par_filiere[g.filiere]:
            cadres_par_filiere[g.filiere].append(g.cadre)
        grades_par_cadre.setdefault(g.cadre, [])
        if g.grade not in grades_par_cadre[g.cadre]:
            grades_par_cadre[g.cadre].append(g.grade)

    regimes = sorted({i.regime for i in ifse if i.regime})

    return {
        "filieres": filieres,
        "cadres_par_filiere": cadres_par_filiere,
        "grades_par_cadre": grades_par_cadre,
        "regimes_ifse": regimes,
        "echelons": list(range(1, 14)),
        "statuts": ["Titulaire", "Non titulaire"],
        "temps_partiel": [t.quotite for t in temps],
    }
