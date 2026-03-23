import type { CapabilityCard as Card } from "../../data/capabilityCards"
import { getCardIcon } from "../ui/Illustrations"

interface CapabilityCardProps {
  card: Card
  onClick: () => void
  disabled?: boolean
}

export function CapabilityCard({ card, onClick, disabled }: CapabilityCardProps) {
  const Icon = getCardIcon(card.agent)
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="card-shadow card-shadow-hover w-full text-left p-5 rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface-elevated)] hover:border-[var(--color-border-hover)] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
    >
      <div className="flex gap-4">
        {Icon && (
          <div className="shrink-0 w-12 h-12 flex items-center justify-center rounded-[var(--radius-md)] bg-[var(--color-surface)] text-[var(--color-text-muted)] group-hover:bg-[var(--color-border)] group-hover:text-[var(--color-text-secondary)] transition-colors duration-200">
            <Icon />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-[var(--color-text)] group-hover:text-[var(--color-text)]">
            {card.title}
          </h3>
          <p className="mt-1.5 text-sm text-[var(--color-text-secondary)] line-clamp-2">
            {card.description}
          </p>
        </div>
      </div>
    </button>
  )
}
