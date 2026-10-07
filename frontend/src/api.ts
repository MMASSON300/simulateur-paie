import { getToken } from './auth'
import type {
  Constant,
  Grade,
  Ifse,
  Options,
  Sft,
  SimulationRequest,
  SimulationResult,
  TempsPartiel,
  Transfert,
} from './types'

const BASE = '/api'

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken()
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...init,
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Erreur ${res.status}: ${body}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  login: (password: string) =>
    http<{ token: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ password }) }),
  verify: () => http<{ status: string }>('/auth/verify'),

  options: () => http<Options>('/options'),

  simuler: (payload: SimulationRequest) =>
    http<SimulationResult>('/simuler', { method: 'POST', body: JSON.stringify(payload) }),

  listGrades: () => http<Grade[]>('/reference/grades?limit=10000'),
  createGrade: (g: Omit<Grade, 'id'>) =>
    http<Grade>('/reference/grades', { method: 'POST', body: JSON.stringify(g) }),
  updateGrade: (id: number, g: Omit<Grade, 'id'>) =>
    http<Grade>(`/reference/grades/${id}`, { method: 'PUT', body: JSON.stringify(g) }),
  deleteGrade: (id: number) => http<void>(`/reference/grades/${id}`, { method: 'DELETE' }),

  listIfse: () => http<Ifse[]>('/reference/ifse?limit=10000'),
  createIfse: (i: Omit<Ifse, 'id'>) =>
    http<Ifse>('/reference/ifse', { method: 'POST', body: JSON.stringify(i) }),
  updateIfse: (id: number, i: Omit<Ifse, 'id'>) =>
    http<Ifse>(`/reference/ifse/${id}`, { method: 'PUT', body: JSON.stringify(i) }),
  deleteIfse: (id: number) => http<void>(`/reference/ifse/${id}`, { method: 'DELETE' }),

  listSft: () => http<Sft[]>('/reference/sft'),
  updateSft: (id: number, s: Omit<Sft, 'id'>) =>
    http<Sft>(`/reference/sft/${id}`, { method: 'PUT', body: JSON.stringify(s) }),

  listConstants: () => http<Constant[]>('/reference/constants'),
  updateConstant: (cle: string, valeur: number) =>
    http<Constant>(`/reference/constants/${cle}`, {
      method: 'PUT',
      body: JSON.stringify({ cle, valeur }),
    }),

  listTempsPartiel: () => http<TempsPartiel[]>('/reference/temps-partiel'),
  createTempsPartiel: (t: Omit<TempsPartiel, 'id'>) =>
    http<TempsPartiel>('/reference/temps-partiel', { method: 'POST', body: JSON.stringify(t) }),
  updateTempsPartiel: (id: number, t: Omit<TempsPartiel, 'id'>) =>
    http<TempsPartiel>(`/reference/temps-partiel/${id}`, { method: 'PUT', body: JSON.stringify(t) }),
  deleteTempsPartiel: (id: number) =>
    http<void>(`/reference/temps-partiel/${id}`, { method: 'DELETE' }),

  listTransfert: () => http<Transfert[]>('/reference/transfert'),
  createTransfert: (t: Omit<Transfert, 'id'>) =>
    http<Transfert>('/reference/transfert', { method: 'POST', body: JSON.stringify(t) }),
  updateTransfert: (id: number, t: Omit<Transfert, 'id'>) =>
    http<Transfert>(`/reference/transfert/${id}`, { method: 'PUT', body: JSON.stringify(t) }),
  deleteTransfert: (id: number) => http<void>(`/reference/transfert/${id}`, { method: 'DELETE' }),
}
