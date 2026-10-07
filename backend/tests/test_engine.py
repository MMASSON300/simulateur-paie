"""Vérification du moteur contre les valeurs mises en cache par Excel."""

import math

from app.engine import compute
from app.reference import build_reference_from_json

ref = build_reference_from_json()

DEFAUT = {
    "statut": "Non titulaire",
    "cdi": False,
    "duree_hebdo": 35,
    "temps_partiel": None,
    "filiere": "Administrative",
    "cadre": "Attachés_territoriaux",
    "grade": "Rédacteur",
    "echelon": 6,
    "nbi": 25,
    "enfants": 0,
    "indemnite_csg": None,
    "regime_indem": None,
    "montant_force": None,
    "prime_grand_age": False,
    "cti": False,
    "prime_annuelle": False,
}


def approx(a, b, tol=1e-6):
    assert math.isclose(a, b, rel_tol=tol, abs_tol=tol), f"{a} != {b}"


def test_non_titulaire():
    r = compute(ref, DEFAUT)
    approx(r["im"], 386)
    approx(r["salaire_brut"], 2083.9604574)
    approx(r["salaire_net"], 1683.2096515408361)
    # détail des gains (valeurs cachees)
    gains = {e["code"]: e["gain"] for e in r["elements"]}
    approx(gains["traitement"], 1900.19308)
    approx(gains["nbi"], 123.0695)
    approx(gains["residence"], 60.6978774)
    approx(gains["smic"], 0)
    approx(gains["sft"], 0)
    approx(gains["ifse"], 0)
    approx(gains["csg"], 0)
    approx(gains["pga"], 0)
    approx(gains["segur"], 0)
    approx(gains["tpp"], 0)
    approx(gains["pfa"], 0)
    cot = {c["code"]: c["retenue"] for c in r["cotisations"]}
    approx(cot["ss_vieillesse_totalite"], 8.3358418296)
    approx(cot["ss_vieillesse_plafonnee"], 143.7932715606)
    approx(cot["ircantec_a"], 50.0150509776)
    approx(cot["ircantec_b"], 0)
    approx(cot["csg"], 49.139787585492)
    approx(cot["rds"], 10.237455746977501)
    approx(cot["csg_deductible"], 139.229398158894)
    # Montants annuels : PFA toujours incluse (feuille PFA), cf. L33/L34 cachees
    approx(r["salaire_brut_annuel"], 26467.525488799998)
    approx(r["salaire_net_annuel"], 21377.754168490035)


def test_non_titulaire_pfa():
    r = compute(ref, {**DEFAUT, "prime_annuelle": True})
    approx(r["salaire_brut"], 2205.6271240666665)
    approx(r["salaire_net"], 1781.4795140408362)


def test_sft():
    # 2 enfants, IM+NBI = 411 -> bande <= 454
    r = compute(ref, {**DEFAUT, "enfants": 2})
    approx(r["elements"][4]["gain"], 77.7182636)

    # 3 enfants -> 194.03536960000002
    r = compute(ref, {**DEFAUT, "enfants": 3})
    approx(r["elements"][4]["gain"], 194.03536960000002)


def test_titulaire_sanity():
    r = compute(ref, {**DEFAUT, "statut": "Titulaire", "cdi": False})
    gains = {e["code"]: e["gain"] for e in r["elements"]}
    # Transfert prime point : catégorie B -> 278/12 * quotité
    approx(gains["tpp"], -(278 / 12) * 1.0)
    # Indemnité CSG = 0,76% de la base (titulaire, pas d'override)
    # Base Excel : h24+h25+h26+h29+h27+h28+h31+h32 - h33
    base = (
        gains["traitement"] + gains["nbi"] + gains["residence"] + gains["ifse"]
        + gains["smic"] + gains["sft"] + gains["pga"] + gains["segur"] - gains["tpp"]
    )
    approx(gains["csg"], base * 0.0076)
    cot = {c["code"]: c["retenue"] for c in r["cotisations"]}
    approx(cot["cnracl"], (gains["traitement"] + gains["nbi"]) * 0.111)
    # RAFP = min(brut - (traitement+nbi), 20% traitement) * 5%
    brut = r["salaire_brut"]
    traitement = gains["traitement"] + gains["nbi"]
    base_rafp = min(brut - traitement, 0.2 * gains["traitement"])
    approx(cot["rafp"], base_rafp * 0.05)
    # Pas de cotisations contractuelles pour un titulaire
    for code in ("ss_vieillesse_totalite", "ss_vieillesse_plafonnee", "ircantec_a", "ircantec_b"):
        approx(cot[code], 0)


if __name__ == "__main__":
    test_non_titulaire()
    test_non_titulaire_pfa()
    test_sft()
    test_titulaire_sanity()
    print("Tous les tests du moteur sont passés.")
