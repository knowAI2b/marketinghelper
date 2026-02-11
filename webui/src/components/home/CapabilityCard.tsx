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
      className="w-full text-left p-5 rounded-xl border border-neutral-200 bg-white hover:border-neutral-300 hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
    >
      <div className="flex gap-4">
        {Icon && (
          <div className="shrink-0 w-12 h-12 flex items-center justify-center rounded-lg bg-neutral-50 text-neutral-400 group-hover:bg-neutral-100 group-hover:text-neutral-600 transition-colors">
            <Icon />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-neutral-900 group-hover:text-neutral-700">
            {card.title}
          </h3>
          <p className="mt-1 text-sm text-neutral-600 line-clamp-2">
            {card.description}
          </p>
        </div>
      </div>
    </button>
  )
}
