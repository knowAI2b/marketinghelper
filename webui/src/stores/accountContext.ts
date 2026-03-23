import type { AccountContext } from "../types/intent"

const STORAGE_KEY = "xhs_account_context"

export function getAccountContext(): AccountContext {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    return JSON.parse(raw) as AccountContext
  } catch {
    return {}
  }
}

export function setAccountContext(ctx: AccountContext): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(ctx))
}
