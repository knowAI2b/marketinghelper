import { useState } from "react"
import { CapabilityCard } from "./CapabilityCard"
import { CAPABILITY_CARDS } from "../../data/capabilityCards"

const INITIAL_COUNT = 6

interface CapabilityGridProps {
  onCardClick: (userInput: string) => void
  filterAgent?: string | null
  disabled?: boolean
}

export function CapabilityGrid({
  onCardClick,
  filterAgent = null,
  disabled = false,
}: CapabilityGridProps) {
  const [showCount, setShowCount] = useState(INITIAL_COUNT)
  const filtered =
    filterAgent == null
      ? CAPABILITY_CARDS
      : CAPABILITY_CARDS.filter((c) => c.agent === filterAgent)
  const visible = filtered.slice(0, showCount)
  const hasMore = showCount < filtered.length

  return (
    <div className="w-full">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {visible.map((card) => (
          <CapabilityCard
            key={card.id}
            card={card}
            onClick={() => onCardClick(card.userInput)}
            disabled={disabled}
          />
        ))}
      </div>
      {hasMore && (
        <div className="mt-10 text-center">
          <button
            type="button"
            onClick={() => setShowCount((n) => Math.min(n + 6, filtered.length))}
            className="px-6 py-2.5 rounded-[var(--radius-full)] border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface)] hover:border-[var(--color-border-hover)] text-sm font-medium transition-colors duration-200"
          >
            加载更多
          </button>
        </div>
      )}
    </div>
  )
}
