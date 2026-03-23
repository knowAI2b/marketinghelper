const TOKEN_KEY = "xhs_auth_token"
const USERNAME_KEY = "xhs_auth_username"

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function getStoredUsername(): string | null {
  return localStorage.getItem(USERNAME_KEY)
}

export function setStoredAuth(token: string, username: string): void {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USERNAME_KEY, username)
}

export function clearStoredAuth(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USERNAME_KEY)
}
