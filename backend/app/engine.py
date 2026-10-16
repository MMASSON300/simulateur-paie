"""Moteur de calcul de paie — transcription fidèle des formules du classeur Excel.

Chaque formule du classeur (feuille ``Simulation``) est reproduite ici. Le moteur
est volontairement indépendant de la persistance : il reçoit les données de
référence sous forme de structures Python simples (voir ``ReferenceData``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# Taux et coefficients de la réglementation. Valeurs par défaut, modifiables
# via l'interface d'administration (onglet « Constantes »).
TAUX_DEFAUT: dict[str, float] = {
    "taux_residence": 0.03,
    "taux_indemnite_csg": 0.0076,  # 0,76 %
    "taux_rafp": 0.05,
    "taux_cnracl": 0.111,
    "taux_ss_vieillesse_totalite": 0.004,
    "taux_ss_vieillesse_plafonnee": 0.069,
    "taux_ircantec_a": 0.024,
    "taux_ircantec_b": 0.0706,
    "taux_csg": 0.024,
    "taux_rds": 0.005,
    "taux_csg_deductible": 0.068,
    "abattement_csg": 0.9825,
    "plafond_rafp_primes": 0.20,
}

# Libellés affichés dans l'administration.
TAUX_LIBELLES: dict[str, str] = {
    "taux_residence": "Taux — indemnité de résidence",
    "taux_indemnite_csg": "Taux — indemnité compensatrice CSG",
    "taux_rafp": "Taux RAFP",
    "taux_cnracl": "Taux CNRACL",
    "taux_ss_vieillesse_totalite": "Taux SS Vieillesse totalité",
    "taux_ss_vieillesse_plafonnee": "Taux SS Vieillesse plafonnée",
    "taux_ircantec_a": "Taux IRCANTEC tranche A",
    "taux_ircantec_b": "Taux IRCANTEC tranche B",
    "taux_csg": "Taux CSG (non déductible)",
    "taux_rds": "Taux RDS (CRDS)",
    "taux_csg_deductible": "Taux CSG déductible",
    "abattement_csg": "Abattement d'assiette CSG/RDS (0,9825 = 98,25 %)",
    "plafond_rafp_primes": "Plafond primes RAFP (part du traitement)",
}

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

    taux: dict[str, float] = field(default_factory=dict)  # clé -> taux (surcharge TAUX_DEFAUT)
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
    # Recherche insensible a la casse (comme VLOOKUP d'Excel).
    return ref.ifse_lookup.get(f"{regime}{grade}".lower(), 0.0)


def _quotite(ref: ReferenceData, duree_hebdo: float, temps_partiel: Optional[float]) -> float:
    """Facteur appliqué aux éléments de rémunération (temps de travail)."""
    base = duree_hebdo / 35.0
    if temps_partiel is None or temps_partiel == "":
        return base
    facteur = ref.temps_partiel.get(float(temps_partiel), 1.0)
    return base * facteur


def _quotite_plafond(duree_hebdo: float, temps_partiel: Optional[float]) -> float:
    """Quotité appliquée au plafond de la sécurité sociale.

    Utilise la QUOTITÉ de temps partiel (ex. 0,8 pour 80 %), et non le facteur
    de conversion du barème (ex. 6/7). Le plafond plein correspond à une quotité de 1.
    """
    base = duree_hebdo / 35.0
    if temps_partiel is None or temps_partiel == "":
        return base
    return base * float(temps_partiel)


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

    # Taux et coefficients (surchargeables via l'administration > Constantes).
    t = {**TAUX_DEFAUT, **ref.taux}

    # --- Indice majoré (G11) ---
    im = _lookup_im(ref, grade, echelon)

    # --- Quotité de service ---
    quotite = _quotite(ref, duree_hebdo, temps_partiel)

    # --- Gains (éléments de paie) ---
    h24 = im * ref.valeur_point * quotite  # Traitement de base indiciaire
    h25 = nbi * ref.valeur_point * quotite  # NBI
    h26 = (h24 + h25) * t["taux_residence"]  # Indemnité de résidence

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
            h30 = base_csg * t["taux_indemnite_csg"]
    elif est_non_titulaire and cdi:
        h30 = float(indemnite_csg) if indemnite_csg not in (None, "") else 0.0

    # Prime de fin d'année (PFA)
    h34 = ref.prime_pfa_mensuel * quotite if prime_annuelle else 0.0

    # --- Salaire brut (H35) ---
    h35 = h24 + h25 + h26 + h27 + h28 + h29 + h30 + h31 + h32 + h34 + h33

    # --- Cotisations ---
    if est_titulaire:
        base_rafp = min(h35 - (h24 + h25), t["plafond_rafp_primes"] * h24)
        h37 = base_rafp * t["taux_rafp"]  # RAFP
        h38 = (h24 + h25) * t["taux_cnracl"]  # CNRACL
    else:
        h37 = 0.0
        h38 = 0.0

    if est_non_titulaire:
        # Le plafond de la securite sociale est proratise par la QUOTITE de
        # temps partiel (ex. 0,8 pour 80 %), et non par le facteur du bareme.
        plafond = ref.plafond_ss * _quotite_plafond(duree_hebdo, temps_partiel)
        h39 = h35 * t["taux_ss_vieillesse_totalite"]
        h40 = min(h35, plafond) * t["taux_ss_vieillesse_plafonnee"]
        # IRCANTEC : le supplément familial de traitement (h28) est exclu de l'assiette.
        assiette_ircantec = h35 - h28
        h41 = min(assiette_ircantec, plafond) * t["taux_ircantec_a"]
        base_b = max(assiette_ircantec - plafond, 0.0)
        h42 = base_b * t["taux_ircantec_b"]
    else:
        h39 = h40 = h41 = h42 = 0.0

    base_csg_rds = h35 * t["abattement_csg"]
    h43 = base_csg_rds * t["taux_csg"]
    h44 = base_csg_rds * t["taux_rds"]
    h45 = base_csg_rds * t["taux_csg_deductible"]

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
            {
                "code": "residence",
                "libelle": "Indemnité de résidence",
                "gain": h26,
                "taux": t["taux_residence"],
            },
            {"code": "smic", "libelle": "Indemnité différentielle SMIC", "gain": h27},
            {"code": "sft", "libelle": "Supplément familial de traitement", "gain": h28},
            {"code": "ifse", "libelle": "Indem Fonction Sujétion et Expertise", "gain": h29},
            {
                "code": "csg",
                "libelle": "Indemnité compensatrice hausse CSG",
                "gain": h30,
                "taux": t["taux_indemnite_csg"],
            },
            {"code": "pga", "libelle": "Prime grand âge", "gain": h31},
            {"code": "segur", "libelle": "Complément Traitement indiciaire Ségur", "gain": h32},
            {"code": "tpp", "libelle": "Transfert prime point", "gain": h33},
            {"code": "pfa", "libelle": "Prime fin d'année", "gain": h34},
        ],
        "salaire_brut": h35,
        "cotisations": [
            {"code": "rafp", "libelle": "RAFP", "retenue": h37, "taux": t["taux_rafp"]},
            {"code": "cnracl", "libelle": "CNRACL", "retenue": h38, "taux": t["taux_cnracl"]},
            {
                "code": "ss_vieillesse_totalite",
                "libelle": "SS Vieillesse totalité",
                "retenue": h39,
                "taux": t["taux_ss_vieillesse_totalite"],
            },
            {
                "code": "ss_vieillesse_plafonnee",
                "libelle": "SS Vieillesse plafonnée",
                "retenue": h40,
                "taux": t["taux_ss_vieillesse_plafonnee"],
            },
            {"code": "ircantec_a", "libelle": "IRCANTEC Tranche A", "retenue": h41, "taux": t["taux_ircantec_a"]},
            {"code": "ircantec_b", "libelle": "IRCANTEC Tranche B", "retenue": h42, "taux": t["taux_ircantec_b"]},
            {"code": "csg", "libelle": "CSG", "retenue": h43, "taux": t["taux_csg"]},
            {"code": "rds", "libelle": "RDS", "retenue": h44, "taux": t["taux_rds"]},
            {
                "code": "csg_deductible",
                "libelle": "CSG déductible",
                "retenue": h45,
                "taux": t["taux_csg_deductible"],
            },
        ],
        "salaire_net": h46,
        "salaire_brut_annuel": brut_annuel,
        "salaire_net_annuel": net_annuel,
    }
