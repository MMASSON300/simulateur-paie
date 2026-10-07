import { useState } from 'react'
import { api } from '../api'
import { setToken } from '../auth'

interface Props {
  onSuccess: () => void
}

export default function AdminLogin({ onSuccess }: Props) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const { token } = await api.login(password)
      setToken(token)
      onSuccess()
    } catch {
      setError('Mot de passe incorrect.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card card-pad" style={{ maxWidth: 420 }}>
      <div className="card-head">
        <h2>
          <span className="icon" style={{ color: 'var(--gov-blue)' }}>
            lock
          </span>
          Accès administration
        </h2>
      </div>
      <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div className="field">
          <label htmlFor="admin-password">Mot de passe</label>
          <input
            id="admin-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
            autoComplete="current-password"
          />
        </div>
        {error && <div className="error-banner">{error}</div>}
        <button className="btn primary" type="submit" disabled={busy} style={{ alignSelf: 'flex-start' }}>
          <span className="icon" style={{ fontSize: 16 }}>
            login
          </span>
          Se connecter
        </button>
      </form>
    </div>
  )
}
