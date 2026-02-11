import type { CapabilityCard as Card } from "../../data/capabilityCards"

interface CapabilityCardProps {
  card: Card
  onClick: () => void
  disabled?: boolean
}

export function CapabilityCard({ card, onClick, disabled }: CapabilityCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="w-full text-left p-5 rounded-xl border border-neutral-200 bg-white hover:border-neutral-300 hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
    >
      <h3 className="font-semibold text-neutral-900 group-hover:text-neutral-700">
        {card.title}
      </h3>
      <p className="mt-1 text-sm text-neutral-600 line-clamp-2">
        {card.description}
      </p>
    </button>
  )
}
