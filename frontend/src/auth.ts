// Le jeton est conservé uniquement en mémoire (pas de persistance) :
// la connexion est donc exigée à chaque accès à l'administration.
let token: string | null = null

export function getToken(): string | null {
  return token
}

export function setToken(value: string | null) {
  token = value
}
