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
    <div className="flex flex-wrap justify-center gap-2">
      {PILLS.map(({ label, id }) => (
        <button
          key={id}
          type="button"
          onClick={() => onSelect?.(id)}
          className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
            active === id
              ? "bg-neutral-900 text-white"
              : "bg-neutral-100 text-neutral-700 hover:bg-neutral-200"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
