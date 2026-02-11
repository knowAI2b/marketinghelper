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
      <div className="max-w-2xl mx-auto px-4 py-12 text-center">
        <p className="text-neutral-600 mb-4">未收到输入，请从首页提交需求。</p>
        <button
          type="button"
          onClick={() => navigate("/")}
          className="text-neutral-900 font-medium hover:underline"
        >
          返回首页
        </button>
      </div>
    )
  }

  const isLoading = step === "intent" || step === "fulfillability" || step === "running"

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="mb-6 flex items-center gap-4">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="text-neutral-600 hover:text-neutral-900 text-sm font-medium"
        >
          ← 返回首页
        </button>
      </div>

      <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-4 mb-6">
        <p className="text-sm text-neutral-500 mb-1">您的需求</p>
        <p className="text-neutral-900 whitespace-pre-wrap">{userInput}</p>
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 text-neutral-600 mb-6">
          <span className="inline-block w-5 h-5 border-2 border-neutral-300 border-t-neutral-600 rounded-full animate-spin" />
          <span>
            {step === "intent" && "理解意图…"}
            {step === "fulfillability" && "检查可执行性…"}
            {step === "running" && "规划与执行…"}
          </span>
        </div>
      )}

      {step === "clarify" && intentOutput?.clarification_question && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 mb-6">
          <p className="text-sm font-medium text-amber-800 mb-2">请补充信息</p>
          <p className="text-amber-900 mb-4">{intentOutput.clarification_question}</p>
          <textarea
            value={clarificationAnswer}
            onChange={(e) => setClarificationAnswer(e.target.value)}
            placeholder="在此补充…"
            className="w-full min-h-[80px] px-3 py-2 rounded-lg border border-amber-200 bg-white text-neutral-900"
          />
          <button
            type="button"
            onClick={handleClarificationSubmit}
            className="mt-2 px-4 py-2 rounded-lg bg-amber-600 text-white font-medium hover:bg-amber-700"
          >
            提交
          </button>
        </div>
      )}

      {step === "done" && fulfillabilityMessage && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 mb-6">
          <p className="text-red-800">{fulfillabilityMessage}</p>
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
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-800">
          {error}
        </div>
      )}
    </div>
  )
}
