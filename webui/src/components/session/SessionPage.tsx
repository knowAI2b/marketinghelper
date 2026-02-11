import { useEffect, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import {
  postIntent,
  postFulfillability,
  postPlannerRun,
} from "../../api/client"
import { getAccountContext } from "../../stores/accountContext"
import type { IntentOutput, PlanStep } from "../../types/intent"
import { SessionResult } from "./SessionResult"

export function SessionPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const userInput = (location.state as { userInput?: string } | null)?.userInput ?? ""

  const [step, setStep] = useState<
    "idle" | "intent" | "clarify" | "fulfillability" | "running" | "done" | "error"
  >("idle")
  const [intentOutput, setIntentOutput] = useState<IntentOutput | null>(null)
  const [clarificationAnswer, setClarificationAnswer] = useState("")
  const [fulfillabilityMessage, setFulfillabilityMessage] = useState<string | null>(null)
  const [planSteps, setPlanSteps] = useState<PlanStep[]>([])
  const [pastSteps, setPastSteps] = useState<Array<[PlanStep, { agent: string; output: string }]>>([])
  const [response, setResponse] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const accountContext = getAccountContext()

  useEffect(() => {
    if (!userInput.trim()) {
      setStep("idle")
      return
    }
    let cancelled = false
    setError(null)
    setFulfillabilityMessage(null)
    setPlanSteps([])
    setPastSteps([])
    setResponse(null)
    setStep("intent")

    async function run() {
      try {
        const intent = await postIntent(userInput, accountContext)
        if (cancelled) return
        setIntentOutput(intent)
        if (intent.needs_clarification) {
          setStep("clarify")
          return
        }
        setStep("fulfillability")
        const fulfillResult = await postFulfillability(intent, accountContext)
        if (cancelled) return
        if (!fulfillResult.can_fulfill) {
          setFulfillabilityMessage(fulfillResult.message_to_user ?? "当前无法执行该需求。")
          setStep("done")
          return
        }
        setStep("running")
        const plannerResult = await postPlannerRun(intent, accountContext)
        if (cancelled) return
        setPlanSteps(plannerResult.plan?.steps ?? [])
        setPastSteps((plannerResult.past_steps ?? []) as Array<[PlanStep, { agent: string; output: string }]>)
        setResponse(plannerResult.response ?? null)
        setStep("done")
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e))
          setStep("error")
        }
      }
    }
    run()
  }, [userInput])

  const handleClarificationSubmit = () => {
    const combined = `${userInput}\n${clarificationAnswer}`.trim()
    navigate("/session", { state: { userInput: combined }, replace: true })
    setClarificationAnswer("")
  }

  if (!userInput.trim()) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-[var(--color-text-secondary)] mb-4">未收到输入，请从首页提交需求。</p>
        <button
          type="button"
          onClick={() => navigate("/")}
          className="text-[var(--color-accent)] font-medium hover:underline underline-offset-4"
        >
          返回首页
        </button>
      </div>
    )
  }

  const isLoading = step === "intent" || step === "fulfillability" || step === "running"

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <div className="mb-6 flex items-center gap-4">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] text-sm font-medium transition-colors"
        >
          ← 返回首页
        </button>
      </div>

      <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 mb-6 card-shadow">
        <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)] mb-1.5">您的需求</p>
        <p className="text-[var(--color-text)] whitespace-pre-wrap">{userInput}</p>
      </div>

      {isLoading && (
        <div className="flex items-center gap-3 text-[var(--color-text-secondary)] mb-6">
          <span className="inline-block w-5 h-5 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" />
          <span className="text-sm">
            {step === "intent" && "理解意图…"}
            {step === "fulfillability" && "检查可执行性…"}
            {step === "running" && "规划与执行…"}
          </span>
        </div>
      )}

      {step === "clarify" && intentOutput?.clarification_question && (
        <div className="rounded-[var(--radius-lg)] border border-amber-200 bg-amber-50/80 p-5 mb-6">
          <p className="text-sm font-medium text-amber-800 mb-2">请补充信息</p>
          <p className="text-amber-900 mb-4">{intentOutput.clarification_question}</p>
          <textarea
            value={clarificationAnswer}
            onChange={(e) => setClarificationAnswer(e.target.value)}
            placeholder="在此补充…"
            className="w-full min-h-[88px] px-3 py-2.5 rounded-[var(--radius-md)] border border-amber-200 bg-white text-[var(--color-text)] focus-ring-accent focus:outline-none transition-shadow"
          />
          <button
            type="button"
            onClick={handleClarificationSubmit}
            className="btn-accent mt-3 px-4 py-2.5 rounded-[var(--radius-md)] font-medium"
          >
            提交
          </button>
        </div>
      )}

      {step === "done" && fulfillabilityMessage && (
        <div className="rounded-[var(--radius-lg)] border border-red-200 bg-red-50/80 p-5 mb-6">
          <p className="text-red-800 text-sm">{fulfillabilityMessage}</p>
        </div>
      )}

      {step === "done" && !fulfillabilityMessage && (
        <SessionResult
          intentOutput={intentOutput}
          planSteps={planSteps}
          pastSteps={pastSteps}
          response={response}
        />
      )}

      {step === "error" && error && (
        <div className="rounded-[var(--radius-lg)] border border-red-200 bg-red-50/80 p-5 text-red-800 text-sm">
          {error}
        </div>
      )}
    </div>
  )
}
