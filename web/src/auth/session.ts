export type AppRole = 'viewer' | 'operator' | 'admin'

export interface AuthSession {
  token: string
  username: string
  role: AppRole
}

const STORAGE_KEY = 'oracle.auth.session'

function normalizeRole(value: string): AppRole {
  const lowered = value.toLowerCase()
  if (lowered === 'viewer' || lowered === 'operator' || lowered === 'admin') {
    return lowered
  }
  return 'viewer'
}

export function loadAuthSession(): AuthSession | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return null
    }
    const parsed = JSON.parse(raw) as {
      token?: string
      username?: string
      role?: string
    }

    if (!parsed.token || !parsed.username || !parsed.role) {
      return null
    }

    return {
      token: parsed.token,
      username: parsed.username,
      role: normalizeRole(parsed.role),
    }
  } catch {
    return null
  }
}

export function saveAuthSession(session: AuthSession): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
}

export function clearAuthSession(): void {
  window.localStorage.removeItem(STORAGE_KEY)
}
