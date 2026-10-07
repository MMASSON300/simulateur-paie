import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Constant, Grade, Ifse, Sft, TempsPartiel, Transfert } from '../types'

type Section = 'grades' | 'ifse' | 'sft' | 'constants' | 'temps' | 'transfert'

interface Column<T> {
  key: keyof T & string
  label: string
  type?: 'text' | 'number'
}

interface EditableTableProps<T extends { id: number }> {
  columns: Column<T>[]
  rows: T[]
  onCreate: (row: T) => Promise<void>
  onUpdate: (row: T) => Promise<void>
  onDelete: (id: number) => Promise<void>
  newRow: T
  searchable?: boolean
  filterable?: (keyof T & string)[]
}

function EditableTable<T extends { id: number }>({
  columns,
  rows,
  onCreate,
  onUpdate,
  onDelete,
  newRow,
  searchable,
  filterable,
}: EditableTableProps<T>) {
  const [drafts, setDrafts] = useState<Record<number, T>>({})
  const [newDraft, setNewDraft] = useState<T | null>(null)
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)

  const distinctValues = (key: keyof T & string): string[] =>
    Array.from(
      new Set(
        rows
          .map((r) => r[key])
          .filter((v) => v !== null && v !== undefined && String(v) !== '')
          .map((v) => String(v)),
      ),
    ).sort((a, b) => a.localeCompare(b, 'fr'))

  const visible = rows.filter((r) => {
    if (filterable) {
      for (const key of filterable) {
        const f = filters[key]
        if (f && String(r[key] ?? '') !== f) return false
      }
    }
    if (!searchable || !query) return true
    return columns.some((c) => String(r[c.key] ?? '').toLowerCase().includes(query.toLowerCase()))
  })

  const value = (row: T, key: keyof T & string) =>
    (drafts[row.id]?.[key] ?? row[key] ?? '') as string | number

  const setValue = (row: T, key: keyof T & string, val: string | number) => {
    setDrafts((prev) => ({ ...prev, [row.id]: { ...(prev[row.id] ?? row), [key]: val } as T }))
  }

  const save = async (row: T) => {
    setBusy(true)
    try {
      await onUpdate(drafts[row.id] ?? row)
      setDrafts((prev) => {
        const { [row.id]: _, ...rest } = prev
        return rest
      })
    } finally {
      setBusy(false)
    }
  }

  const add = async () => {
    if (!newDraft) return
    setBusy(true)
    try {
      await onCreate(newDraft)
      setNewDraft(null)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="admin-toolbar">
        {searchable && (
          <input
            className="search-input"
            placeholder="Rechercher…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        )}
        {filterable?.map((key) => {
          const col = columns.find((c) => c.key === key)
          return (
            <select
              key={key}
              className="filter-select"
              value={filters[key] ?? ''}
              onChange={(e) => setFilters((prev) => ({ ...prev, [key]: e.target.value }))}
            >
              <option value="">{col ? `Tous · ${col.label}` : 'Tous'}</option>
              {distinctValues(key).map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          )
        })}
        <button className="btn primary" onClick={() => setNewDraft(newRow)}>
          + Ajouter
        </button>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="admin-table">
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c.key}>{c.label}</th>
              ))}
              <th style={{ width: 150 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((row) => (
              <tr key={row.id}>
                {columns.map((c) => {
                  const isNum = c.type === 'number'
                  const v = value(row, c.key)
                  const val = v === '' || v === null || v === undefined ? '' : String(v)
                  return (
                    <td key={c.key} className={isNum ? 'num' : ''}>
                      <input
                        value={val}
                        type={isNum ? 'number' : 'text'}
                        step={isNum ? 'any' : undefined}
                        onChange={(e) =>
                          setValue(
                            row,
                            c.key,
                            isNum
                              ? e.target.value === ''
                                ? ''
                                : Number(e.target.value)
                              : e.target.value,
                          )
                        }
                      />
                    </td>
                  )
                })}
                <td>
                  <div className="group">
                    <button className="btn" onClick={() => save(row)} disabled={busy}>
                      Enregistrer
                    </button>
                    <button className="btn danger" onClick={() => onDelete(row.id)} disabled={busy}>
                      Supprimer
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {visible.length === 0 && (
              <tr>
                <td colSpan={columns.length + 1} style={{ color: 'var(--muted)', padding: 16 }}>
                  Aucun résultat.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {newDraft && (
        <div className="card" style={{ marginTop: 16 }}>
          <div className="card-pad">
            <div className="card-head">
              <h2>Nouvel élément</h2>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table className="admin-table">
                <tbody>
                  <tr>
                    {columns.map((c) => (
                      <td key={c.key}>
                        <input
                          value={newDraft[c.key] == null ? '' : String(newDraft[c.key])}
                          type={c.type === 'number' ? 'number' : 'text'}
                          step={c.type === 'number' ? 'any' : undefined}
                          onChange={(e) =>
                            setNewDraft({
                              ...newDraft,
                              [c.key]:
                                c.type === 'number'
                                  ? e.target.value === ''
                                    ? ('' as never)
                                    : (Number(e.target.value) as never)
                                  : (e.target.value as never),
                            })
                          }
                        />
                      </td>
                    ))}
                    <td style={{ whiteSpace: 'nowrap' }}>
                      <div className="group">
                        <button className="btn primary" onClick={add} disabled={busy}>
                          Créer
                        </button>
                        <button className="btn" onClick={() => setNewDraft(null)}>
                          Annuler
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const gradeCols: Column<Grade>[] = [
  { key: 'filiere', label: 'Filière' },
  { key: 'cadre', label: "Cadre d'emploi" },
  { key: 'grade', label: 'Grade' },
  { key: 'echelon', label: 'Échelon', type: 'number' },
  { key: 'im', label: 'IM', type: 'number' },
  { key: 'categorie', label: 'Catégorie' },
]

const ifseCols: Column<Ifse>[] = [
  { key: 'code_regime', label: 'Code' },
  { key: 'regime', label: 'Régime' },
  { key: 'grade_code', label: 'Code grade' },
  { key: 'grade', label: 'Grade' },
  { key: 'montant', label: 'Montant', type: 'number' },
]

const sftCols: Column<Sft>[] = [
  { key: 'enfants', label: 'Enfants', type: 'number' },
  { key: 'element_fixe', label: 'Élément fixe', type: 'number' },
  { key: 'element_proportionnel', label: 'Élément prop.', type: 'number' },
]

const tempsCols: Column<TempsPartiel>[] = [
  { key: 'quotite', label: 'Quotité', type: 'number' },
  { key: 'facteur', label: 'Facteur', type: 'number' },
]

const transfertCols: Column<Transfert>[] = [
  { key: 'categorie', label: 'Catégorie' },
  { key: 'montant_annuel', label: 'Montant annuel', type: 'number' },
]

export default function AdminPanel({ onLogout }: { onLogout: () => void }) {
  const [section, setSection] = useState<Section>('grades')
  const [grades, setGrades] = useState<Grade[]>([])
  const [ifse, setIfse] = useState<Ifse[]>([])
  const [sft, setSft] = useState<Sft[]>([])
  const [constants, setConstants] = useState<Constant[]>([])
  const [temps, setTemps] = useState<TempsPartiel[]>([])
  const [transfert, setTransfert] = useState<Transfert[]>([])

  const load = async () => {
    const [g, i, s, c, t, tr] = await Promise.all([
      api.listGrades(),
      api.listIfse(),
      api.listSft(),
      api.listConstants(),
      api.listTempsPartiel(),
      api.listTransfert(),
    ])
    setGrades(g)
    setIfse(i)
    setSft(s)
    setConstants(c)
    setTemps(t)
    setTransfert(tr)
  }

  useEffect(() => {
    load()
  }, [])

  const sections: { key: Section; label: string }[] = [
    { key: 'grades', label: `Grades (${grades.length})` },
    { key: 'ifse', label: `IFSE (${ifse.length})` },
    { key: 'sft', label: 'SFT' },
    { key: 'constants', label: 'Constantes' },
    { key: 'temps', label: 'Temps partiel' },
    { key: 'transfert', label: 'Transfert prime point' },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10, marginBottom: 20 }}>
        <div className="nav">
          {sections.map((s) => (
            <button
              key={s.key}
              className={section === s.key ? 'active' : ''}
              onClick={() => setSection(s.key)}
            >
              {s.label}
            </button>
          ))}
        </div>
        <button className="btn" onClick={onLogout}>
          <span className="icon" style={{ fontSize: 16 }}>
            logout
          </span>
          Déconnexion
        </button>
      </div>

      <div className="card card-pad">
        {section === 'grades' && (
          <EditableTable
            columns={gradeCols}
            rows={grades}
            searchable
            filterable={['filiere', 'cadre', 'categorie']}
            newRow={{ id: 0, filiere: '', cadre: '', grade: '', echelon: 1, im: 0, categorie: '' }}
            onCreate={async (r) => {
              await api.createGrade(r)
              load()
            }}
            onUpdate={async (r) => {
              await api.updateGrade(r.id, r)
              load()
            }}
            onDelete={async (id) => {
              await api.deleteGrade(id)
              load()
            }}
          />
        )}

        {section === 'ifse' && (
          <EditableTable
            columns={ifseCols}
            rows={ifse}
            searchable
            filterable={['regime']}
            newRow={{ id: 0, code_regime: '', regime: '', grade_code: '', grade: '', montant: 0 }}
            onCreate={async (r) => {
              await api.createIfse(r)
              load()
            }}
            onUpdate={async (r) => {
              await api.updateIfse(r.id, r)
              load()
            }}
            onDelete={async (id) => {
              await api.deleteIfse(id)
              load()
            }}
          />
        )}

        {section === 'sft' && (
          <EditableTable
            columns={sftCols}
            rows={sft}
            newRow={{ id: 0, enfants: 0, element_fixe: 0, element_proportionnel: null }}
            onCreate={async () => load()}
            onUpdate={async (r) => {
              await api.updateSft(r.id, r)
              load()
            }}
            onDelete={async () => load()}
          />
        )}

        {section === 'constants' && (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Constante</th>
                <th style={{ width: 200 }}>Valeur</th>
                <th style={{ width: 120 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {constants.map((c) => (
                <ConstantRow key={c.cle} constant={c} onSaved={load} />
              ))}
            </tbody>
          </table>
        )}

        {section === 'temps' && (
          <EditableTable
            columns={tempsCols}
            rows={temps}
            newRow={{ id: 0, quotite: 0.5, facteur: 0.5 }}
            onCreate={async (r) => {
              await api.createTempsPartiel(r)
              load()
            }}
            onUpdate={async (r) => {
              await api.updateTempsPartiel(r.id, r)
              load()
            }}
            onDelete={async (id) => {
              await api.deleteTempsPartiel(id)
              load()
            }}
          />
        )}

        {section === 'transfert' && (
          <EditableTable
            columns={transfertCols}
            rows={transfert}
            newRow={{ id: 0, categorie: '', montant_annuel: 0 }}
            onCreate={async (r) => {
              await api.createTransfert(r)
              load()
            }}
            onUpdate={async (r) => {
              await api.updateTransfert(r.id, r)
              load()
            }}
            onDelete={async (id) => {
              await api.deleteTransfert(id)
              load()
            }}
          />
        )}
      </div>
    </div>
  )
}

function ConstantRow({ constant, onSaved }: { constant: Constant; onSaved: () => Promise<void> }) {
  const [val, setVal] = useState(constant.valeur)
  const [busy, setBusy] = useState(false)

  const save = async () => {
    setBusy(true)
    try {
      await api.updateConstant(constant.cle, val)
      onSaved()
    } finally {
      setBusy(false)
    }
  }

  const labels: Record<string, string> = {
    valeur_point: 'Valeur du point d’indice',
    plafond_ss: 'Plafond Sécurité sociale',
    smic: 'SMIC mensuel',
    prime_pfa_mensuel: 'Prime de fin d’année (mensuel)',
    prime_segur_mensuel: 'CTI Ségur (mensuel)',
    prime_pga_mensuel: 'Prime grand âge (mensuel)',
  }

  return (
    <tr>
      <td>{labels[constant.cle] ?? constant.cle}</td>
      <td className="num">
        <input
          type="number"
          step="any"
          value={val}
          onChange={(e) => setVal(Number(e.target.value))}
        />
      </td>
      <td>
        <button className="btn" onClick={save} disabled={busy}>
          Enregistrer
        </button>
      </td>
    </tr>
  )
}
