export interface Options {
  filieres: string[]
  cadres_par_filiere: Record<string, string[]>
  grades_par_cadre: Record<string, string[]>
  regimes_ifse: string[]
  echelons: number[]
  statuts: string[]
  temps_partiel: number[]
}

export interface SimulationRequest {
  statut: string
  cdi: boolean
  duree_hebdo: number
  temps_partiel: number | null
  filiere: string | null
  cadre: string | null
  grade: string | null
  echelon: number | null
  nbi: number
  enfants: number
  indemnite_csg: number | null
  regime_indem: string | null
  montant_force: number | null
  prime_grand_age: boolean
  cti: boolean
  prime_annuelle: boolean
}

export interface ElementPaie {
  code: string
  libelle: string
  gain: number
}

export interface Cotisation {
  code: string
  libelle: string
  retenue: number
}

export interface SimulationResult {
  im: number
  quotite: number
  smic_indiciaire: number
  elements: ElementPaie[]
  salaire_brut: number
  cotisations: Cotisation[]
  salaire_net: number
  salaire_brut_annuel: number
  salaire_net_annuel: number
}

export interface Grade {
  id: number
  filiere: string | null
  cadre: string | null
  grade: string
  echelon: number
  im: number
  categorie: string | null
}

export interface Ifse {
  id: number
  code_regime: string | null
  regime: string
  grade_code: string | null
  grade: string
  montant: number
}

export interface Sft {
  id: number
  enfants: number
  element_fixe: number
  element_proportionnel: number | null
}

export interface Constant {
  cle: string
  valeur: number
}

export interface TempsPartiel {
  id: number
  quotite: number
  facteur: number
}

export interface Transfert {
  id: number
  categorie: string
  montant_annuel: number
}
