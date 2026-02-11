import { useNavigate } from "react-router-dom"
import { Hero } from "./Hero"
import { Pills } from "./Pills"
import { CentralInput } from "./CentralInput"
import { CapabilityGrid } from "./CapabilityGrid"
import { useState } from "react"

const AGENT_PILL_MAP: Record<string, string> = {
  account_strategy: "账号战略",
  topic_planning: "选题策划",
  content_generation: "内容生成",
  ads_planning: "投流",
  content_eval: "内容评估与检验",
}

export function HomePage() {
  const navigate = useNavigate()
  const [filterAgent, setFilterAgent] = useState<string | null>(null)

  const handleSubmit = (userInput: string) => {
    navigate("/session", { state: { userInput } })
  }

  const handlePillSelect = (id: string) => {
    setFilterAgent((prev) => (prev === id ? null : id))
  }

  const filterAgentLabel = filterAgent ? AGENT_PILL_MAP[filterAgent] ?? null : null

  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col">
      <section className="pt-12 pb-8 px-4">
        <Hero />
      </section>
      <section className="pb-6 px-4">
        <Pills active={filterAgent} onSelect={handlePillSelect} />
      </section>
      <section className="pb-8 px-4">
        <CentralInput onSubmit={handleSubmit} placeholder="您想做什么？" />
      </section>
      <section className="flex-1 px-4 pb-12 max-w-5xl mx-auto w-full">
        <CapabilityGrid
          onCardClick={handleSubmit}
          filterAgent={filterAgentLabel}
        />
      </section>
    </div>
  )
}
