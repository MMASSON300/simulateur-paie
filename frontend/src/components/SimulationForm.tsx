import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import type { ElementPaie, Options, SimulationRequest, SimulationResult } from '../types'

interface FormState {
  statut: string
  cdi: boolean
  duree_hebdo: string
  temps_partiel: string
  filiere: string
  cadre: string
  grade: string
  echelon: string
  nbi: string
  enfants: string
  indemnite_csg: string
  regime_indem: string
  montant_force: string
  prime_grand_age: boolean
  cti: boolean
  prime_annuelle: boolean
}

const INITIAL: FormState = {
  statut: 'Titulaire',
  cdi: false,
  duree_hebdo: '35',
  temps_partiel: '',
  filiere: '',
  cadre: '',
  grade: '',
  echelon: '1',
  nbi: '0',
  enfants: '0',
  indemnite_csg: '',
  regime_indem: '',
  montant_force: '',
  prime_grand_age: false,
  cti: false,
  prime_annuelle: false,
}

function toNum(v: string): number | null {
  if (v === '') return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

function buildRequest(f: FormState): SimulationRequest {
  return {
    statut: f.statut,
    cdi: f.cdi,
    duree_hebdo: toNum(f.duree_hebdo) ?? 35,
    temps_partiel: toNum(f.temps_partiel),
    filiere: f.filiere || null,
    cadre: f.cadre || null,
    grade: f.grade || null,
    echelon: toNum(f.echelon) ?? 0,
    nbi: toNum(f.nbi) ?? 0,
    enfants: Math.round(toNum(f.enfants) ?? 0),
    indemnite_csg: toNum(f.indemnite_csg),
    regime_indem: f.regime_indem || null,
    montant_force: toNum(f.montant_force),
    prime_grand_age: f.prime_grand_age,
    cti: f.cti,
    prime_annuelle: f.prime_annuelle,
  }
}

function fmt(n: number): string {
  return n.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €'
}

const REGLES: Record<string, string> = {
  traitement: 'INM × point d’indice',
  nbi: 'Points NBI × point d’indice',
  smic: 'Complément différentiel SMIC',
  sft: 'Selon nombre d’enfants',
  ifse: 'Primes statutaires',
  pga: 'Prime grand âge',
  segur: 'Complément CTI Ségur',
  tpp: 'Transfert prime point',
  pfa: 'Prime de fin d’année',
}

function pct(n: number): string {
  return n.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' %'
}

function regleFor(e: ElementPaie): string {
  if (e.code === 'residence') return `${pct(e.taux ?? 0)} du traitement + NBI`
  if (e.code === 'csg') return `${pct(e.taux ?? 0)} de la base indem.`
  return REGLES[e.code] ?? ''
}

const RETRAITE_CODES = [
  'rafp',
  'cnracl',
  'ss_vieillesse_totalite',
  'ss_vieillesse_plafonnee',
  'ircantec_a',
  'ircantec_b',
]
const CSG_CODES = ['csg', 'rds', 'csg_deductible']

interface Props {
  options: Options | null
}

export default function SimulationForm({ options }: Props) {
  const [form, setForm] = useState<FormState>(INITIAL)
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => {
      const next = { ...prev, [key]: value }
      if (key === 'filiere') {
        next.cadre = ''
        next.grade = ''
      } else if (key === 'cadre') {
        next.grade = ''
      }
      if (key === 'statut' || key === 'cdi') {
        const statut = key === 'statut' ? (value as string) : prev.statut
        const cdi = key === 'cdi' ? (value as boolean) : prev.cdi
        if (!(statut === 'Titulaire' || (statut === 'Non titulaire' && cdi))) {
          next.indemnite_csg = ''
        }
      }
      // Les régimes IFSE dépendent du grade : on retire un régime devenu invalide.
      const allowed = next.grade ? options?.regimes_par_grade[next.grade] ?? [] : []
      if (next.regime_indem && !allowed.includes(next.regime_indem)) {
        next.regime_indem = ''
      }
      return next
    })
  }

  useEffect(() => {
    if (!options) return
    setResult(null)
    setError(null)
    const timer = setTimeout(() => {
      api
        .simuler(buildRequest(form))
        .then(setResult)
        .catch((e) => setError(e.message))
    }, 150)
    return () => clearTimeout(timer)
  }, [form, options])

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 2800)
    return () => clearTimeout(t)
  }, [toast])

  const decomposition = useMemo(() => {
    if (!result) return { net: 0, retraite: 0, csg: 0, totalRetenues: 0 }
    const brut = result.salaire_brut || 1
    const retraite = result.cotisations
      .filter((c) => RETRAITE_CODES.includes(c.code))
      .reduce((s, c) => s + c.retenue, 0)
    const csg = result.cotisations
      .filter((c) => CSG_CODES.includes(c.code))
      .reduce((s, c) => s + c.retenue, 0)
    const totalRetenues = result.cotisations.reduce((s, c) => s + c.retenue, 0)
    return {
      net: (result.salaire_net / brut) * 100,
      retraite: (retraite / brut) * 100,
      csg: (csg / brut) * 100,
      totalRetenues,
    }
  }, [result])

  if (!options) return <div className="card card-pad loading">Chargement des options…</div>

  const cadres = form.filiere ? options.cadres_par_filiere[form.filiere] ?? [] : []
  const grades = form.cadre ? options.grades_par_cadre[form.cadre] ?? [] : []
  const showCsg = form.statut === 'Titulaire' || (form.statut === 'Non titulaire' && form.cdi)
  const regimesDisponibles = form.grade ? options.regimes_par_grade[form.grade] ?? [] : []

  const paramsList: [string, string][] = [
    ['Statut', form.statut],
    ['Durée hebdomadaire de base', form.duree_hebdo ? `${form.duree_hebdo} h` : ''],
    [
      'Temps partiel',
      form.temps_partiel ? `${Math.round(Number(form.temps_partiel) * 100)} %` : 'Temps plein',
    ],
    ['Filière', form.filiere],
    ["Cadre d'emploi", form.cadre],
    ['Grade', form.grade],
    ['Échelon', form.echelon],
    ['NBI', form.nbi ? `${form.nbi} points` : ''],
    ["Nombre d'enfants", form.enfants],
    ['Régime indemnitaire (IFSE)', form.regime_indem],
    ['Montant IFSE forcé', form.montant_force ? `${form.montant_force} €` : ''],
    ...(showCsg
      ? ([
          [
            'Indemnité compensatrice CSG',
            form.indemnite_csg ? `${form.indemnite_csg} €` : 'Automatique',
          ],
        ] as [string, string][])
      : []),
    ['Prime grand âge', form.prime_grand_age ? 'Oui' : 'Non'],
    ['Complément CTI (Ségur)', form.cti ? 'Oui' : 'Non'],
    ['Prime annuelle lissée', form.prime_annuelle ? 'Oui' : 'Non'],
  ]

  const reset = () => {
    setForm(INITIAL)
    setToast('Paramètres réinitialisés.')
  }

  const copy = () => {
    if (!result) return
    const text = [
      'Simulation de salaire — Mairie d\'Ivry-sur-Seine',
      `Statut : ${form.statut}${form.cdi ? ' (CDI)' : ''}`,
      `Grade : ${form.grade || '—'} (échelon ${form.echelon})`,
      `Indice majoré : ${result.im}`,
      '',
      'Éléments de paie :',
      ...result.elements.map((e) => `  - ${e.libelle} : ${fmt(e.gain)}`),
      `  Salaire brut : ${fmt(result.salaire_brut)}`,
      '',
      'Cotisations :',
      ...result.cotisations.map((c) => `  - ${c.libelle} : ${fmt(c.retenue)}`),
      '',
      `Net à payer (avant PAS) : ${fmt(result.salaire_net)}`,
      `Net annuel (PFA incluse) : ${fmt(result.salaire_net_annuel)}`,
    ].join('\n')
    navigator.clipboard.writeText(text).then(
      () => setToast('Synthèse copiée dans le presse-papier.'),
      () => setToast('Copie impossible dans ce navigateur.'),
    )
  }

  return (
    <div className="grid">
      {/* Colonne gauche — Paramètres */}
      <div className="col col-form">
        <div className="card">
          <div className="card-pad">
            <div className="card-head">
              <h2>
                <span className="icon" style={{ color: 'var(--gov-blue)' }}>
                  badge
                </span>
                Paramètres de l’agent
              </h2>
              <span className="chip">Point : 4,92278 €</span>
            </div>

            <div className="form-grid">
              <div className="field">
                <label>Statut</label>
                <div className="segmented cols-2">
                  <button
                    className={form.statut === 'Titulaire' ? 'active' : ''}
                    onClick={() => set('statut', 'Titulaire')}
                  >
                    Titulaire
                  </button>
                  <button
                    className={form.statut === 'Non titulaire' ? 'active' : ''}
                    onClick={() => set('statut', 'Non titulaire')}
                  >
                    Contractuel
                  </button>
                </div>
              </div>

              {form.statut === 'Non titulaire' && (
                <label className="check">
                  <input
                    type="checkbox"
                    checked={form.cdi}
                    onChange={(e) => set('cdi', e.target.checked)}
                  />
                  <span>
                    <span className="check-label">CDI</span>{' '}
                    <span className="check-sub">(à cocher si Indemnité Compensatrice CSG)</span>
                  </span>
                </label>
              )}

              <div className="field">
                <label>Durée hebdomadaire de base de l'emploi</label>
                <input
                  type="number"
                  value={form.duree_hebdo}
                  onChange={(e) => set('duree_hebdo', e.target.value)}
                />
              </div>

              <div className="field">
                <label>Si temps partiel</label>
                <div className="segmented cols-3">
                  {options.temps_partiel.map((q) => (
                    <button
                      key={q}
                      className={form.temps_partiel === String(q) ? 'active' : ''}
                      onClick={() =>
                        set('temps_partiel', form.temps_partiel === String(q) ? '' : String(q))
                      }
                    >
                      {Math.round(q * 100)} %
                    </button>
                  ))}
                </div>
                <span className="hint">Aucun = temps plein</span>
              </div>

              <div className="field">
                <label>NBI (points)</label>
                <input type="number" value={form.nbi} onChange={(e) => set('nbi', e.target.value)} />
              </div>

              <div className="field">
                <label>Filière</label>
                <select value={form.filiere} onChange={(e) => set('filiere', e.target.value)}>
                  <option value="">— Sélectionner —</option>
                  {options.filieres.map((f) => (
                    <option key={f}>{f}</option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label>Cadre d’emploi</label>
                <select value={form.cadre} onChange={(e) => set('cadre', e.target.value)}>
                  <option value="">— Sélectionner —</option>
                  {cadres.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div className="row">
                <div className="field">
                  <label>Grade</label>
                  <select value={form.grade} onChange={(e) => set('grade', e.target.value)}>
                    <option value="">— Sélectionner —</option>
                    {grades.map((g) => (
                      <option key={g}>{g}</option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>Échelon</label>
                  <select value={form.echelon} onChange={(e) => set('echelon', e.target.value)}>
                    {options.echelons.map((e) => (
                      <option key={e} value={e}>
                        {e}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="row">
                <div className="field">
                  <label>Nombre d’enfants</label>
                  <input
                    type="number"
                    min={0}
                    max={10}
                    value={form.enfants}
                    onChange={(e) => set('enfants', e.target.value)}
                  />
                </div>
                {showCsg && (
                  <div className="field">
                    <label>Indemnité compensatrice CSG</label>
                    <input
                      type="number"
                      value={form.indemnite_csg}
                      onChange={(e) => set('indemnite_csg', e.target.value)}
                      placeholder={form.statut === 'Titulaire' ? 'Auto (0,76 %)' : 'Montant mensuel'}
                    />
                    <span className="hint">
                      {form.statut === 'Titulaire'
                        ? 'Laissez vide pour le calcul automatique (0,76 % de la base).'
                        : 'Montant manuel appliqué aux contractuels en CDI.'}
                    </span>
                  </div>
                )}
              </div>

              <div className="field">
                <label>Régime indemnitaire (IFSE)</label>
                <select value={form.regime_indem} onChange={(e) => set('regime_indem', e.target.value)}>
                  <option value="">— Sélectionner —</option>
                  {regimesDisponibles.map((r) => (
                    <option key={r}>{r}</option>
                  ))}
                </select>
                {!form.grade && <span className="hint">Sélectionnez d'abord un grade.</span>}
                {form.grade && regimesDisponibles.length === 0 && (
                  <span className="hint">Aucun régime IFSE pour ce grade.</span>
                )}
              </div>

              <div className="field">
                <label>Montant IFSE forcé</label>
                <input
                  type="number"
                  value={form.montant_force}
                  onChange={(e) => set('montant_force', e.target.value)}
                  placeholder="Optionnel (€/mois)"
                />
              </div>

              <div className="field">
                <label>Primes et compléments</label>
                <div className="form-grid" style={{ gap: 8 }}>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={form.prime_grand_age}
                      onChange={(e) => set('prime_grand_age', e.target.checked)}
                    />
                    <span className="check-label">Prime grand âge</span>
                  </label>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={form.cti}
                      onChange={(e) => set('cti', e.target.checked)}
                    />
                    <span className="check-label">Complément de traitement indiciaire (Ségur)</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="note">
          <span className="icon">account_balance</span>
          <span>
            Calcul conforme aux grilles des fonctionnaires territoriaux (titulaires CNRACL et
            contractuels IRCANTEC). La prime de fin d’année est toujours incluse dans le montant
            annuel.
          </span>
        </div>
      </div>

      {/* Colonne droite — Résultats */}
      <div className="col col-results">
        {error && <div className="error-banner">{error}</div>}

        {result && (
          <>
            <div className="print-params">
              <h2>Paramètres saisis</h2>
              <div className="print-params-grid">
                {paramsList.map(([label, value]) => (
                  <div className="pp-item" key={label}>
                    <span className="pp-label">{label}</span>
                    <span className="pp-value">{value || '—'}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="synthesis">
              <div className="synthesis-top">
                <div>
                  <span className="synthesis-label">
                    <span className="dot" />
                    Net à payer (avant prélèvement à la source)
                  </span>
                  <div className="synthesis-net">{fmt(result.salaire_net)}</div>
                  <div className="synthesis-caption">Montant versé chaque mois à l’agent</div>
                </div>
                <div className="synthesis-side">
                  <div>
                    <span className="k">Salaire Brut Mensuel</span>
                    <div className="v">{fmt(result.salaire_brut)}</div>
                  </div>
                  <div>
                    <span className="k">Brut annuel (PFA incluse)</span>
                    <div className="v muted">{fmt(result.salaire_brut_annuel)}</div>
                  </div>
                </div>
              </div>

              <div className="decomp">
                <div className="decomp-head">
                  <span>Décomposition du brut</span>
                  <span className="rate">
                    Taux global de retenues :{' '}
                    <strong style={{ color: 'var(--primary)' }}>
                      {result.salaire_brut
                        ? ((decomposition.totalRetenues / result.salaire_brut) * 100).toFixed(1)
                        : '0.0'}
                      %
                    </strong>
                  </span>
                </div>
                <div className="decomp-bar">
                  <div className="seg" style={{ width: `${decomposition.net}%`, background: 'var(--secondary)' }} />
                  <div className="seg" style={{ width: `${decomposition.retraite}%`, background: 'var(--gov-blue)' }} />
                  <div className="seg" style={{ width: `${decomposition.csg}%`, background: '#94a3b8' }} />
                </div>
                <div className="decomp-legend">
                  <span>
                    <span className="swatch" style={{ background: 'var(--secondary)' }} />
                    Net disponible
                  </span>
                  <span>
                    <span className="swatch" style={{ background: 'var(--gov-blue)' }} />
                    Retraite & vieillesse
                  </span>
                  <span>
                    <span className="swatch" style={{ background: '#94a3b8' }} />
                    CSG / RDS
                  </span>
                </div>
              </div>
            </div>

            <label className="check check--highlight" style={{ marginBottom: 12 }}>
              <input
                type="checkbox"
                checked={form.prime_annuelle}
                onChange={(e) => set('prime_annuelle', e.target.checked)}
              />
              <span className="check-label">
                Cochez pour application de la Prime annuelle lissée mensuellement
              </span>
            </label>

            <div className="card">
              <div className="card-pad">
                <div className="card-head">
                  <h2>
                    <span className="icon" style={{ color: 'var(--gov-blue)' }}>
                      receipt_long
                    </span>
                    Détail du bulletin de traitement
                  </h2>
                  <span className="chip">IM : {result.im}</span>
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table className="bulletin">
                    <thead>
                      <tr>
                        <th>Éléments de rémunération</th>
                        <th>Règle</th>
                        <th>Montant</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.elements.map((e) => (
                        <tr key={e.code}>
                          <td className="libelle">{e.libelle}</td>
                          <td className="regle">{regleFor(e)}</td>
                          <td className={`montant${e.gain < 0 ? ' neg' : ''}`}>{fmt(e.gain)}</td>
                        </tr>
                      ))}
                      <tr className="total">
                        <td>TOTAL RÉMUNÉRATION BRUTE</td>
                        <td className="regle">—</td>
                        <td className="montant">{fmt(result.salaire_brut)}</td>
                      </tr>
                    </tbody>
                    <thead>
                      <tr>
                        <th>Cotisations & retenues salariales</th>
                        <th>Taux</th>
                        <th>Part salariale</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.cotisations.map((c) => (
                        <tr key={c.code}>
                          <td className="libelle">{c.libelle}</td>
                          <td className="regle">{pct(c.taux)}</td>
                          <td className="montant neg">{fmt(-c.retenue)}</td>
                        </tr>
                      ))}
                      <tr className="total">
                        <td>TOTAL RETENUES</td>
                        <td className="regle">
                          {result.salaire_brut
                            ? ((decomposition.totalRetenues / result.salaire_brut) * 100).toFixed(1)
                            : '0.0'}
                          %
                        </td>
                        <td className="montant neg">{fmt(-decomposition.totalRetenues)}</td>
                      </tr>
                    </tbody>
                    <tbody>
                      <tr className="net">
                        <td>NET À PAYER (avant PAS)</td>
                        <td className="regle">Brut − retenues</td>
                        <td className="montant">{fmt(result.salaire_net)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p className="annual-note">
                  Annuel (PFA incluse) : brut {fmt(result.salaire_brut_annuel)} · net{' '}
                  {fmt(result.salaire_net_annuel)}
                </p>
              </div>
            </div>

            <div className="actions">
              <div className="group">
                <button className="btn" onClick={reset}>
                  <span className="icon" style={{ fontSize: 16 }}>
                    restart_alt
                  </span>
                  Réinitialiser
                </button>
                <button className="btn" onClick={copy}>
                  <span className="icon" style={{ fontSize: 16 }}>
                    content_copy
                  </span>
                  Copier le détail
                </button>
              </div>
              <button className="btn blue" onClick={() => window.print()}>
                <span className="icon" style={{ fontSize: 16 }}>
                  print
                </span>
                Imprimer
              </button>
            </div>
          </>
        )}

        {!result && !error && <div className="card card-pad loading">Calcul en cours…</div>}
      </div>

      {toast && (
        <div className="toast show">
          <span className="icon">check_circle</span>
          {toast}
        </div>
      )}
    </div>
  )
}
