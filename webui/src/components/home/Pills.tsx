const PILLS = [
  { label: "账号战略", id: "account_strategy" },
  { label: "选题策划", id: "topic_planning" },
  { label: "内容生成", id: "content_generation" },
  { label: "投流", id: "ads_planning" },
  { label: "内容评估", id: "content_eval" },
]

interface PillsProps {
  active?: string | null
  onSelect?: (id: string) => void
}

export function Pills({ active = null, onSelect }: PillsProps) {
  return (
    <div className="flex flex-wrap justify-center gap-2.5">
      {PILLS.map(({ label, id }) => (
        <button
          key={id}
          type="button"
          onClick={() => onSelect?.(id)}
          className={`px-5 py-2.5 rounded-[var(--radius-full)] text-sm font-medium transition-all duration-200 ${
            active === id
              ? "bg-[var(--color-accent)] text-white shadow-[var(--shadow-sm)]"
              : "bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:bg-[var(--color-border)] hover:text-[var(--color-text)]"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
