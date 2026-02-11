import type {
  AccountContext,
  FulfillabilityResult,
  IntentOutput,
  PlannerResult,
} from "../types/intent"

const API_BASE = "/api"

async function post<T>(path: string, body: object): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${path}: ${res.status} ${text}`)
  }
  return res.json() as Promise<T>
}

export async function postIntent(
  userInput: string,
  accountContext: AccountContext = {}
): Promise<IntentOutput> {
  return post<IntentOutput>("/intent", {
    user_input: userInput,
    account_context: accountContext,
  })
}

export async function postFulfillability(
  intentOutput: IntentOutput,
  accountContext: AccountContext = {}
): Promise<FulfillabilityResult> {
  return post<FulfillabilityResult>("/fulfillability", {
    intent_output: intentOutput,
    account_context: accountContext,
  })
}

export async function postPlannerRun(
  intentOutput: IntentOutput,
  accountContext: AccountContext = {},
  pastSteps: unknown[] | null = null
): Promise<PlannerResult> {
  return post<PlannerResult>("/planner/run", {
    intent_output: intentOutput,
    account_context: accountContext,
    past_steps: pastSteps ?? undefined,
  })
}

export async function getHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error(`Health: ${res.status}`)
  return res.json() as Promise<{ status: string }>
}
