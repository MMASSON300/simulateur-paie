"""Construction des données de référence (``ReferenceData``) à partir du JSON de seed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .engine import ReferenceData

SEED_DIR = Path(__file__).parent / "seed_data"


def _load(name: str) -> Any:
    with open(SEED_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def build_reference_from_json() -> ReferenceData:
    grades = _load("grades.json")
    ifse = _load("ifse.json")
    sft = _load("sft.json")
    const = _load("constants.json")

    im_lookup = {f"{g['grade']}{int(g['echelon'])}": float(g["im"]) for g in grades}
    categorie_lookup = {g["grade"]: g["categorie"] for g in grades}
    ifse_lookup = {f"{i['regime']}{i['grade']}": float(i["montant"]) for i in ifse}

    temps_partiel = {float(t["quotite"]): float(t["facteur"]) for t in const["temps_partiel"]}
    transfert = {t["categorie"]: float(t["montant_annuel"]) for t in const["transfert_prime_point"]}
    sft_map = {
        int(s["enfants"]): (float(s["element_fixe"]), s["element_proportionnel"])
        for s in sft
    }

    return ReferenceData(
        valeur_point=float(const["valeur_point"]),
        plafond_ss=float(const["plafond_ss"]),
        smic=float(const["smic"]),
        prime_pfa_mensuel=float(const["prime_pfa_mensuel"]),
        prime_segur_mensuel=float(const["prime_segur_mensuel"]),
        prime_pga_mensuel=float(const["prime_pga_mensuel"]),
        temps_partiel=temps_partiel,
        transfert_prime_point=transfert,
        sft=sft_map,
        im_lookup=im_lookup,
        categorie_lookup=categorie_lookup,
        ifse_lookup=ifse_lookup,
    )


def build_reference_from_db(db) -> ReferenceData:
    """Construit les données de référence à partir des tables en base."""
    from . import models

    grades = db.query(models.Grade).all()
    ifse = db.query(models.Ifse).all()
    sft = db.query(models.SftParam).all()
    temps = db.query(models.TempsPartiel).all()
    transferts = db.query(models.TransfertPrimePoint).all()
    constants = {c.cle: c.valeur for c in db.query(models.Constant).all()}

    return ReferenceData(
        valeur_point=constants["valeur_point"],
        plafond_ss=constants["plafond_ss"],
        smic=constants["smic"],
        prime_pfa_mensuel=constants["prime_pfa_mensuel"],
        prime_segur_mensuel=constants["prime_segur_mensuel"],
        prime_pga_mensuel=constants["prime_pga_mensuel"],
        temps_partiel={t.quotite: t.facteur for t in temps},
        transfert_prime_point={t.categorie: t.montant_annuel for t in transferts},
        sft={s.enfants: (s.element_fixe, s.element_proportionnel) for s in sft},
        im_lookup={f"{g.grade}{g.echelon}": g.im for g in grades},
        categorie_lookup={g.grade: g.categorie for g in grades},
        ifse_lookup={f"{i.regime}{i.grade}": i.montant for i in ifse},
    )
