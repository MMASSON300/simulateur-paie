"""Moteur de calcul de paie — transcription fidèle des formules du classeur Excel.

Chaque formule du classeur (feuille ``Simulation``) est reproduite ici. Le moteur
est volontairement indépendant de la persistance : il reçoit les données de
référence sous forme de structures Python simples (voir ``ReferenceData``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# Valeurs codées en dur dans les formules Excel (constantes de la réglementation).
TAUX_RESIDENCE = 0.03
TAUX_INDEMNITE_CSG = 0.0076  # 0,76 %
TAUX_RAFP = 0.05
TAUX_CNRACL = 0.111
TAUX_SS_VIEILLESSE_TOTALITE = 0.004
TAUX_SS_VIEILLESSE_PLAFONNEE = 0.069
TAUX_IRCANTEC_A = 0.024
TAUX_IRCANTEC_B = 0.0706
TAUX_CSG = 0.024
TAUX_RDS = 0.005
TAUX_CSG_DEDUCTIBLE = 0.068
ABATTEMENT_CSG = 0.9825

# Constantes structurelles du calcul (exprimées en indice dans le fichier).
SEUIL_SFT_BAS = 454
SEUIL_SFT_HAUT = 722
HEURES_MENSUELLES_REF = 35 * 52 / 12  # 151,666... heures


@dataclass
class ReferenceData:
    """Données de référence extraites du classeur."""

    valeur_point: float
    plafond_ss: float
    smic: float
    prime_pfa_mensuel: float
    prime_segur_mensuel: float
    prime_pga_mensuel: float

    temps_partiel: dict[float, float] = field(default_factory=dict)  # quotité -> facteur
    transfert_prime_point: dict[str, float] = field(default_factory=dict)  # catégorie -> annuel
    sft: dict[int, tuple[float, Optional[float]]] = field(default_factory=dict)  # enfants -> (fixe, proportionnel)

    # Lookups pré-indexés (clé concaténée identique à celle d'Excel).
    im_lookup: dict[str, float] = field(default_factory=dict)  # grade+échelon -> IM
    categorie_lookup: dict[str, str] = field(default_factory=dict)  # grade -> catégorie
    ifse_lookup: dict[str, float] = field(default_factory=dict)  # régime+grade -> montant


def _lookup_im(ref: ReferenceData, grade: str, echelon: int) -> float:
    return ref.im_lookup.get(f"{grade}{int(echelon)}", 0.0)


def _lookup_categorie(ref: ReferenceData, grade: str) -> str:
    return ref.categorie_lookup.get(grade, "")


def _lookup_ifse(ref: ReferenceData, regime: str, grade: str) -> float:
    return ref.ifse_lookup.get(f"{regime}{grade}", 0.0)


def _quotite(ref: ReferenceData, duree_hebdo: float, temps_partiel: Optional[float]) -> float:
    """Facteur appliqué aux éléments de rémunération (temps de travail)."""
    base = duree_hebdo / 35.0
    if temps_partiel is None or temps_partiel == "":
        return base
    facteur = ref.temps_partiel.get(float(temps_partiel), 1.0)
    return base * facteur


def _sft_montant(
    ref: ReferenceData,
    enfants: int,
    im_nbi: float,
    traitement: float,
) -> float:
    if enfants <= 0:
        return 0.0
    row = ref.sft.get(enfants)
    if row is None:
        return 0.0
    fixe, prop = row
    if prop is None:
        return fixe  # 1 enfant : élément fixe uniquement
    if im_nbi <= SEUIL_SFT_BAS:
        return SEUIL_SFT_BAS * ref.valeur_point * prop + fixe
    if im_nbi > SEUIL_SFT_HAUT:
        return SEUIL_SFT_HAUT * ref.valeur_point * prop + fixe
    plancher = SEUIL_SFT_BAS * ref.valeur_point * prop + fixe
    return max(traitement * prop + fixe, plancher)


def compute(ref: ReferenceData, inp: dict[str, Any]) -> dict[str, Any]:
    """Calcule le bulletin complet à partir des entrées.

    ``inp`` attend les champs suivants (équivalents aux cellules de saisie) :
        statut (str), cdi (bool), duree_hebdo (float), temps_partiel (float|None),
        filiere (str), cadre (str), grade (str), echelon (int), nbi (float),
        enfants (int), indemnite_csg (float|None), regime_indem (str|None),
        montant_force (float|None), prime_grand_age (bool), cti (bool),
        prime_annuelle (bool).
    """

    statut = inp.get("statut") or ""
    cdi = bool(inp.get("cdi", False))
    duree_hebdo = float(inp.get("duree_hebdo") or 35)
    temps_partiel = inp.get("temps_partiel")
    grade = inp.get("grade") or ""
    echelon = int(inp.get("echelon") or 0)
    nbi = float(inp.get("nbi") or 0)
    enfants = int(inp.get("enfants") or 0)
    indemnite_csg = inp.get("indemnite_csg")
    regime_indem = inp.get("regime_indem")
    montant_force = inp.get("montant_force")
    prime_grand_age = bool(inp.get("prime_grand_age", False))
    cti = bool(inp.get("cti", False))
    prime_annuelle = bool(inp.get("prime_annuelle", False))

    est_titulaire = statut == "Titulaire"
    est_non_titulaire = statut == "Non titulaire"

    # --- Indice majoré (G11) ---
    im = _lookup_im(ref, grade, echelon)

    # --- Quotité de service ---
    quotite = _quotite(ref, duree_hebdo, temps_partiel)

    # --- Gains (éléments de paie) ---
    h24 = im * ref.valeur_point * quotite  # Traitement de base indiciaire
    h25 = nbi * ref.valeur_point * quotite  # NBI
    h26 = (h24 + h25) * TAUX_RESIDENCE  # Indemnité de résidence

    # Indemnité différentielle SMIC
    smic_indiciaire = im * ref.valeur_point
    h27 = (ref.smic - smic_indiciaire) * quotite if smic_indiciaire < ref.smic else 0.0

    # Supplément familial de traitement
    h28 = _sft_montant(ref, enfants, im + nbi, h24 + h25)

    # IFSE
    if montant_force not in (None, ""):
        ifse_base = float(montant_force)
    elif regime_indem not in (None, ""):
        ifse_base = _lookup_ifse(ref, regime_indem, grade)
    else:
        ifse_base = 0.0
    h29 = ifse_base * quotite

    # Prime grand âge (PGA)
    h31 = ref.prime_pga_mensuel * quotite if prime_grand_age else 0.0

    # CTI (complément Ségur)
    h32 = ref.prime_segur_mensuel * quotite if cti else 0.0

    # Transfert prime point (négatif, titulaires uniquement)
    h33 = 0.0
    if est_titulaire:
        cat = _lookup_categorie(ref, grade)
        annuel = ref.transfert_prime_point.get(cat, 0.0)
        h33 = -(annuel / 12.0) * quotite

    # Indemnité compensatrice hausse CSG (dépend de h24..h32, h33)
    h30 = 0.0
    if est_titulaire:
        if indemnite_csg not in (None, ""):
            h30 = float(indemnite_csg)
        else:
            base_csg = h24 + h25 + h26 + h29 + h27 + h28 + h31 + h32 - h33
            h30 = base_csg * TAUX_INDEMNITE_CSG
    elif est_non_titulaire and cdi:
        h30 = float(indemnite_csg) if indemnite_csg not in (None, "") else 0.0

    # Prime de fin d'année (PFA)
    h34 = ref.prime_pfa_mensuel * quotite if prime_annuelle else 0.0

    # --- Salaire brut (H35) ---
    h35 = h24 + h25 + h26 + h27 + h28 + h29 + h30 + h31 + h32 + h34 + h33

    # --- Cotisations ---
    if est_titulaire:
        base_rafp = min(h35 - (h24 + h25), 0.2 * h24)
        h37 = base_rafp * TAUX_RAFP  # RAFP
        h38 = (h24 + h25) * TAUX_CNRACL  # CNRACL
    else:
        h37 = 0.0
        h38 = 0.0

    if est_non_titulaire:
        h39 = h35 * TAUX_SS_VIEILLESSE_TOTALITE
        h40 = min(h35, ref.plafond_ss) * TAUX_SS_VIEILLESSE_PLAFONNEE
        h41 = min(h35, ref.plafond_ss) * TAUX_IRCANTEC_A
        base_b = max(h35 - ref.plafond_ss, 0.0)
        h42 = base_b * TAUX_IRCANTEC_B
    else:
        h39 = h40 = h41 = h42 = 0.0

    base_csg_rds = h35 * ABATTEMENT_CSG
    h43 = base_csg_rds * TAUX_CSG
    h44 = base_csg_rds * TAUX_RDS
    h45 = base_csg_rds * TAUX_CSG_DEDUCTIBLE

    # --- Salaire net (avant PAS) ---
    h46 = h35 - h37 - h38 - h39 - h40 - h41 - h42 - h43 - h44 - h45

    # --- Montants annuels (prime de fin d'année toujours incluse, cf. feuille PFA) ---
    if prime_annuelle:
        brut_annuel = h35 * 12
        net_annuel = h46 * 12
    else:
        annuel = compute(ref, {**inp, "prime_annuelle": True})
        brut_annuel = annuel["salaire_brut"] * 12
        net_annuel = annuel["salaire_net"] * 12

    return {
        "im": im,
        "quotite": quotite,
        "smic_indiciaire": smic_indiciaire,
        "elements": [
            {"code": "traitement", "libelle": "Traitement de base indiciaire", "gain": h24},
            {"code": "nbi", "libelle": "NBI", "gain": h25},
            {"code": "residence", "libelle": "Indemnité de résidence", "gain": h26},
            {"code": "smic", "libelle": "Indemnité différentielle SMIC", "gain": h27},
            {"code": "sft", "libelle": "Supplément familial de traitement", "gain": h28},
            {"code": "ifse", "libelle": "Indem Fonction Sujétion et Expertise", "gain": h29},
            {"code": "csg", "libelle": "Indemnité compensatrice hausse CSG", "gain": h30},
            {"code": "pga", "libelle": "Prime grand âge", "gain": h31},
            {"code": "segur", "libelle": "Complément Traitement indiciaire Ségur", "gain": h32},
            {"code": "tpp", "libelle": "Transfert prime point", "gain": h33},
            {"code": "pfa", "libelle": "Prime fin d'année", "gain": h34},
        ],
        "salaire_brut": h35,
        "cotisations": [
            {"code": "rafp", "libelle": "RAFP", "retenue": h37},
            {"code": "cnracl", "libelle": "CNRACL", "retenue": h38},
            {"code": "ss_vieillesse_totalite", "libelle": "SS Vieillesse totalité", "retenue": h39},
            {"code": "ss_vieillesse_plafonnee", "libelle": "SS Vieillesse plafonnée", "retenue": h40},
            {"code": "ircantec_a", "libelle": "IRCANTEC Tranche A", "retenue": h41},
            {"code": "ircantec_b", "libelle": "IRCANTEC Tranche B", "retenue": h42},
            {"code": "csg", "libelle": "CSG", "retenue": h43},
            {"code": "rds", "libelle": "RDS", "retenue": h44},
            {"code": "csg_deductible", "libelle": "CSG déductible", "retenue": h45},
        ],
        "salaire_net": h46,
        "salaire_brut_annuel": brut_annuel,
        "salaire_net_annuel": net_annuel,
    }
