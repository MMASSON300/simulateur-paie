import { useEffect, useState } from 'react'
import { api } from './api'
import { setToken } from './auth'
import AdminLogin from './components/AdminLogin'
import AdminPanel from './components/AdminPanel'
import SimulationForm from './components/SimulationForm'
import type { Options } from './types'

type Tab = 'simulation' | 'admin'

export default function App() {
  const [tab, setTab] = useState<Tab>('simulation')
  const [options, setOptions] = useState<Options | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [adminAuthed, setAdminAuthed] = useState(false)

  useEffect(() => {
    api
      .options()
      .then(setOptions)
      .catch((e) => setError(`Impossible de joindre le backend : ${e.message}`))
  }, [])

  const logout = () => {
    setToken(null)
    setAdminAuthed(false)
  }

  const goTo = (next: Tab) => {
    if (next !== 'admin') {
      // La session d'administration est fermée dès que l'on quitte l'onglet.
      setToken(null)
      setAdminAuthed(false)
    }
    setTab(next)
  }

  return (
    <>
      <header className="app-header">
        <div className="app-header-inner">
          <div className="brand">
            <span className="brand-mark">SP</span>
            <span className="brand-name">Simulateur de salaire</span>
            <span className="brand-badge">
              <span className="dot" />
              Fonction publique territoriale
            </span>
          </div>

          <div className="header-right">
            <nav className="nav">
              <button
                className={tab === 'simulation' ? 'active' : ''}
                onClick={() => goTo('simulation')}
              >
                <span className="icon">calculate</span>
                Simulation
              </button>
              <button className={tab === 'admin' ? 'active' : ''} onClick={() => goTo('admin')}>
                <span className="icon">database</span>
                Administration
              </button>
            </nav>
            <span className="version-pill">V1.2026.10</span>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="container">
          {tab === 'simulation' && (
            <>
              <div className="page-title">
                <h1>Simulateur de rémunération — Fonction publique territoriale</h1>
                <p>
                  Calcul précis du traitement indiciaire brut, des primes (IFSE, SFT, NBI, Ségur,
                  prime de fin d'année) et des cotisations statutaires (CNRACL, RAFP, IRCANTEC,
                  CSG/CRDS) pour titulaires et contractuels.
                </p>
              </div>
              {error && <div className="error-banner">{error}</div>}
              <SimulationForm options={options} />
            </>
          )}

          {tab === 'admin' && (
            <>
              <div className="page-title">
                <h1>Administration des données de référence</h1>
                <p>
                  Grilles indiciaires, régimes IFSE, supplément familial, constantes et paramètres
                  de temps partiel. Les modifications sont appliquées immédiatement à la simulation.
                </p>
              </div>
              {adminAuthed ? (
                <AdminPanel onLogout={logout} />
              ) : (
                <AdminLogin onSuccess={() => setAdminAuthed(true)} />
              )}
            </>
          )}
        </div>
      </main>

      <footer className="app-footer">
        <div className="app-footer-inner">
          <div>
            <strong>Simulateur de salaire</strong> — conforme aux grilles statutaires territoriales
          </div>
          <div>Valeur du point d'indice : 4,92278 €</div>
        </div>
      </footer>
    </>
  )
}
