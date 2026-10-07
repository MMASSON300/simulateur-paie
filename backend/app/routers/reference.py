"""Routes CRUD d'administration des données de référence."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..database import get_db
from ..schemas import (
    ConstantIn,
    ConstantOut,
    GradeIn,
    GradeOut,
    IfseIn,
    IfseOut,
    SftIn,
    SftOut,
    TempsPartielIn,
    TempsPartielOut,
    TransfertIn,
    TransfertOut,
)
from .. import models

router = APIRouter(prefix="/api/reference", tags=["reference"], dependencies=[Depends(require_admin)])


def _get_or_404(db: Session, model, id: int):
    obj = db.get(model, id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Introuvable")
    return obj


# --- Grades ---

@router.get("/grades", response_model=list[GradeOut])
def list_grades(
    filiere: Optional[str] = None,
    cadre: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(models.Grade)
    if filiere:
        query = query.filter(models.Grade.filiere == filiere)
    if cadre:
        query = query.filter(models.Grade.cadre == cadre)
    if q:
        query = query.filter(models.Grade.grade.ilike(f"%{q}%"))
    return query.order_by(models.Grade.id).offset(offset).limit(limit).all()


@router.post("/grades", response_model=GradeOut, status_code=201)
def create_grade(payload: GradeIn, db: Session = Depends(get_db)):
    obj = models.Grade(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/grades/{id}", response_model=GradeOut)
def update_grade(id: int, payload: GradeIn, db: Session = Depends(get_db)):
    obj = _get_or_404(db, models.Grade, id)
    for k, v in payload.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/grades/{id}", status_code=204)
def delete_grade(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, models.Grade, id)
    db.delete(obj)
    db.commit()


# --- IFSE ---

@router.get("/ifse", response_model=list[IfseOut])
def list_ifse(
    regime: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(models.Ifse)
    if regime:
        query = query.filter(models.Ifse.regime == regime)
    if q:
        query = query.filter(models.Ifse.grade.ilike(f"%{q}%"))
    return query.order_by(models.Ifse.id).offset(offset).limit(limit).all()


@router.post("/ifse", response_model=IfseOut, status_code=201)
def create_ifse(payload: IfseIn, db: Session = Depends(get_db)):
    obj = models.Ifse(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/ifse/{id}", response_model=IfseOut)
def update_ifse(id: int, payload: IfseIn, db: Session = Depends(get_db)):
    obj = _get_or_404(db, models.Ifse, id)
    for k, v in payload.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/ifse/{id}", status_code=204)
def delete_ifse(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, models.Ifse, id)
    db.delete(obj)
    db.commit()


# --- SFT ---

@router.get("/sft", response_model=list[SftOut])
def list_sft(db: Session = Depends(get_db)):
    return db.query(models.SftParam).order_by(models.SftParam.enfants).all()


@router.put("/sft/{id}", response_model=SftOut)
def update_sft(id: int, payload: SftIn, db: Session = Depends(get_db)):
    obj = _get_or_404(db, models.SftParam, id)
    for k, v in payload.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


# --- Constantes ---

@router.get("/constants", response_model=list[ConstantOut])
def list_constants(db: Session = Depends(get_db)):
    return db.query(models.Constant).all()


@router.put("/constants/{cle}", response_model=ConstantOut)
def update_constant(cle: str, payload: ConstantIn, db: Session = Depends(get_db)):
    obj = db.get(models.Constant, cle)
    if obj is None:
        obj = models.Constant(cle=cle, valeur=payload.valeur)
        db.add(obj)
    else:
        obj.valeur = payload.valeur
    db.commit()
    db.refresh(obj)
    return obj


# --- Temps partiel ---

@router.get("/temps-partiel", response_model=list[TempsPartielOut])
def list_temps_partiel(db: Session = Depends(get_db)):
    return db.query(models.TempsPartiel).order_by(models.TempsPartiel.quotite.desc()).all()


@router.post("/temps-partiel", response_model=TempsPartielOut, status_code=201)
def create_temps_partiel(payload: TempsPartielIn, db: Session = Depends(get_db)):
    obj = models.TempsPartiel(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/temps-partiel/{id}", response_model=TempsPartielOut)
def update_temps_partiel(id: int, payload: TempsPartielIn, db: Session = Depends(get_db)):
    obj = _get_or_404(db, models.TempsPartiel, id)
    for k, v in payload.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/temps-partiel/{id}", status_code=204)
def delete_temps_partiel(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, models.TempsPartiel, id)
    db.delete(obj)
    db.commit()


# --- Transfert prime point ---

@router.get("/transfert", response_model=list[TransfertOut])
def list_transfert(db: Session = Depends(get_db)):
    return db.query(models.TransfertPrimePoint).all()


@router.post("/transfert", response_model=TransfertOut, status_code=201)
def create_transfert(payload: TransfertIn, db: Session = Depends(get_db)):
    obj = models.TransfertPrimePoint(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/transfert/{id}", response_model=TransfertOut)
def update_transfert(id: int, payload: TransfertIn, db: Session = Depends(get_db)):
    obj = _get_or_404(db, models.TransfertPrimePoint, id)
    for k, v in payload.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/transfert/{id}", status_code=204)
def delete_transfert(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, models.TransfertPrimePoint, id)
    db.delete(obj)
    db.commit()
