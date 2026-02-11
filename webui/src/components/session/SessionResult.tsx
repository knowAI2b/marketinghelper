import type { IntentOutput, PlanStep } from "../../types/intent"

interface SessionResultProps {
  intentOutput: IntentOutput | null
  planSteps: PlanStep[]
  pastSteps: Array<[PlanStep, { agent: string; output: string }]>
  response: string | null
}

export function SessionResult({
  intentOutput,
  planSteps,
  pastSteps,
  response,
}: SessionResultProps) {
  return (
    <div className="space-y-6">
      {intentOutput && (
        <section className="rounded-xl border border-neutral-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-wide mb-2">
            需求理解
          </h3>
          <p className="text-neutral-900">{intentOutput.demand_summary}</p>
          {intentOutput.suggested_agents?.length > 0 && (
            <p className="mt-2 text-sm text-neutral-600">
              建议流程：{intentOutput.suggested_agents.join(" → ")}
            </p>
          )}
        </section>
      )}

      {planSteps.length > 0 && (
        <section className="rounded-xl border border-neutral-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-wide mb-3">
            执行计划
          </h3>
          <ol className="space-y-3">
            {planSteps.map((s, i) => (
              <li key={s.step_id} className="flex gap-3">
                <span className="shrink-0 w-6 h-6 rounded-full bg-neutral-200 flex items-center justify-center text-xs font-medium text-neutral-600">
                  {i + 1}
                </span>
                <div>
                  <p className="font-medium text-neutral-900">{s.agent}</p>
                  <p className="text-sm text-neutral-600">{s.input_summary}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      {pastSteps.length > 0 && (
        <section className="rounded-xl border border-neutral-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-wide mb-3">
            执行结果
          </h3>
          <div className="space-y-4">
            {pastSteps.map(([step, result], i) => (
              <div key={step.step_id ?? i} className="border-l-2 border-neutral-200 pl-4">
                <p className="font-medium text-neutral-900">{result.agent}</p>
                <p className="text-sm text-neutral-600 whitespace-pre-wrap mt-1">
                  {result.output}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {response && (
        <section className="rounded-xl border border-neutral-200 bg-neutral-50 p-4">
          <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-wide mb-2">
            完成
          </h3>
          <p className="text-neutral-900">{response}</p>
        </section>
      )}
    </div>
  )
}
