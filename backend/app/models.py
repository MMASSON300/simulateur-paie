"""Modèles ORM des données de référence."""

from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filiere: Mapped[str] = mapped_column(String, nullable=True)
    cadre: Mapped[str] = mapped_column(String, nullable=True)
    grade: Mapped[str] = mapped_column(String, index=True)
    echelon: Mapped[int] = mapped_column(Integer)
    im: Mapped[float] = mapped_column(Float)
    categorie: Mapped[str] = mapped_column(String, nullable=True)


class Ifse(Base):
    __tablename__ = "ifse"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code_regime: Mapped[str] = mapped_column(String, nullable=True)
    regime: Mapped[str] = mapped_column(String, index=True)
    grade_code: Mapped[str] = mapped_column(String, nullable=True)
    grade: Mapped[str] = mapped_column(String, index=True)
    montant: Mapped[float] = mapped_column(Float)


class SftParam(Base):
    __tablename__ = "sft_params"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enfants: Mapped[int] = mapped_column(Integer, unique=True)
    element_fixe: Mapped[float] = mapped_column(Float)
    element_proportionnel: Mapped[float | None] = mapped_column(Float, nullable=True)


class Constant(Base):
    __tablename__ = "constants"

    cle: Mapped[str] = mapped_column(String, primary_key=True)
    valeur: Mapped[float] = mapped_column(Float)


class TempsPartiel(Base):
    __tablename__ = "temps_partiel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotite: Mapped[float] = mapped_column(Float, unique=True)
    facteur: Mapped[float] = mapped_column(Float)


class TransfertPrimePoint(Base):
    __tablename__ = "transfert_prime_point"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    categorie: Mapped[str] = mapped_column(String, unique=True)
    montant_annuel: Mapped[float] = mapped_column(Float)
