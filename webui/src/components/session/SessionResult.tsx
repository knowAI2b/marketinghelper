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
        <section className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-5 card-shadow">
          <h3 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-2">
            需求理解
          </h3>
          <p className="text-[var(--color-text)]">{intentOutput.demand_summary}</p>
          {intentOutput.suggested_agents?.length > 0 && (
            <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
              建议流程：{intentOutput.suggested_agents.join(" → ")}
            </p>
          )}
        </section>
      )}

      {planSteps.length > 0 && (
        <section className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-5 card-shadow">
          <h3 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-3">
            执行计划
          </h3>
          <ol className="space-y-3">
            {planSteps.map((s, i) => (
              <li key={s.step_id} className="flex gap-3">
                <span className="shrink-0 w-7 h-7 rounded-full bg-[var(--color-accent-muted)] text-[var(--color-accent)] flex items-center justify-center text-xs font-semibold">
                  {i + 1}
                </span>
                <div>
                  <p className="font-medium text-[var(--color-text)]">{s.agent}</p>
                  <p className="text-sm text-[var(--color-text-secondary)]">{s.input_summary}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      {pastSteps.length > 0 && (
        <section className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-5 card-shadow">
          <h3 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-3">
            执行结果
          </h3>
          <div className="space-y-4">
            {pastSteps.map(([step, result], i) => (
              <div key={step.step_id ?? i} className="border-l-2 border-[var(--color-border)] pl-4">
                <p className="font-medium text-[var(--color-text)]">{result.agent}</p>
                <p className="text-sm text-[var(--color-text-secondary)] whitespace-pre-wrap mt-1">
                  {result.output}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {response && (
        <section className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 card-shadow">
          <h3 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-2">
            完成
          </h3>
          <p className="text-[var(--color-text)]">{response}</p>
        </section>
      )}
    </div>
  )
}
