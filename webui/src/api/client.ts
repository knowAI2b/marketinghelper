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
    let msg = text || `请求失败 ${res.status}`
    try {
      const j = JSON.parse(text) as { detail?: string }
      if (typeof j.detail === "string") msg = j.detail
    } catch {
      /* 非 JSON 时用 text */
    }
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

// SSE 事件类型
export interface SSEStageEvent {
  step: 'planning' | 'agent' | 'step_done' | 'complete' | 'error'
  message: string
  agent?: string
}

export interface SSEErrorEvent {
  error: string
}

// SSE 回调类型
export interface SSECallbacks {
  onStage?: (event: SSEStageEvent) => void
  onResult?: (result: PlannerResult) => void
  onError?: (error: string) => void
}

export async function postPlannerStream(
  intentOutput: IntentOutput,
  accountContext: AccountContext = {},
  callbacks: SSECallbacks,
  pastSteps: unknown[] | null = null
): Promise<void> {
  const res = await fetch(`${API_BASE}/planner/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      intent_output: intentOutput,
      account_context: accountContext,
      past_steps: pastSteps ?? undefined,
    }),
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `请求失败 ${res.status}`)
  }

  const reader = res.body?.getReader()
  if (!reader) {
    throw new Error("无法获取响应流")
  }

  const decoder = new TextDecoder()
  let buffer = ""

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // 解析 SSE 事件
      const lines = buffer.split("\n")
      buffer = lines.pop() || "" // 保留最后一个不完整的行

      let eventType = ""
      let eventData = ""

      for (const line of lines) {
        if (line.startsWith("event:")) {
          eventType = line.slice(6).trim()
        } else if (line.startsWith("data:")) {
          eventData = line.slice(5).trim()
        } else if (line === "" && eventType && eventData) {
          // 空行表示事件结束，处理事件
          try {
            const data = JSON.parse(eventData)

            if (eventType === "stage") {
              callbacks.onStage?.(data as SSEStageEvent)
            } else if (eventType === "result") {
              callbacks.onResult?.(data as PlannerResult)
            } else if (eventType === "error") {
              callbacks.onError?.((data as SSEErrorEvent).error)
            }
          } catch (e) {
            console.warn("Failed to parse SSE event:", eventData, e)
          }

          eventType = ""
          eventData = ""
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
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

// ---------- 认证 ----------

export interface RegisterRes {
  ok: boolean
  message?: string
}

export interface LoginRes {
  ok: boolean
  token: string
  username: string
}

export interface LogoutRes {
  ok: boolean
}

export interface MeRes {
  id: number
  username: string
  created_at: string
}

export async function postRegister(
  username: string,
  password: string
): Promise<RegisterRes> {
  return post<RegisterRes>("/auth/register", { username, password })
}

export async function postLogin(
  username: string,
  password: string
): Promise<LoginRes> {
  return post<LoginRes>("/auth/login", { username, password })
}

export async function postLogout(token: string): Promise<LogoutRes> {
  return post<LogoutRes>("/auth/logout", { token })
}

export async function getMe(token: string): Promise<MeRes> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error("未登录或 token 已过期")
  return res.json() as Promise<MeRes>
}
