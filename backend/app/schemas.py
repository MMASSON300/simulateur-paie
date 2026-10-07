"""Schémas Pydantic (entrées/sorties de l'API)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str


class SimulationRequest(BaseModel):
    statut: str
    cdi: bool = False
    duree_hebdo: float = 35
    temps_partiel: Optional[float] = None
    filiere: Optional[str] = None
    cadre: Optional[str] = None
    grade: Optional[str] = None
    echelon: Optional[int] = None
    nbi: float = 0
    enfants: int = 0
    indemnite_csg: Optional[float] = None
    regime_indem: Optional[str] = None
    montant_force: Optional[float] = None
    prime_grand_age: bool = False
    cti: bool = False
    prime_annuelle: bool = False


class ElementPaie(BaseModel):
    code: str
    libelle: str
    gain: float


class Cotisation(BaseModel):
    code: str
    libelle: str
    retenue: float


class SimulationResponse(BaseModel):
    im: float
    quotite: float
    smic_indiciaire: float
    elements: list[ElementPaie]
    salaire_brut: float
    cotisations: list[Cotisation]
    salaire_net: float
    salaire_brut_annuel: float
    salaire_net_annuel: float


# --- Schémas CRUD (données de référence) ---

class GradeIn(BaseModel):
    filiere: Optional[str] = None
    cadre: Optional[str] = None
    grade: str
    echelon: int
    im: float
    categorie: Optional[str] = None


class GradeOut(GradeIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class IfseIn(BaseModel):
    code_regime: Optional[str] = None
    regime: str
    grade_code: Optional[str] = None
    grade: str
    montant: float


class IfseOut(IfseIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SftIn(BaseModel):
    enfants: int
    element_fixe: float
    element_proportionnel: Optional[float] = None


class SftOut(SftIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ConstantIn(BaseModel):
    cle: str
    valeur: float


class ConstantOut(ConstantIn):
    model_config = ConfigDict(from_attributes=True)


class TempsPartielIn(BaseModel):
    quotite: float
    facteur: float


class TempsPartielOut(TempsPartielIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class TransfertIn(BaseModel):
    categorie: str
    montant_annuel: float


class TransfertOut(TransfertIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class Options(BaseModel):
    filieres: list[str]
    cadres_par_filiere: dict[str, list[str]]
    grades_par_cadre: dict[str, list[str]]
    regimes_ifse: list[str]
    echelons: list[int]
    statuts: list[str]
    temps_partiel: list[float]
