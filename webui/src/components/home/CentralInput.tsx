import { useState, useRef } from "react"

interface CentralInputProps {
  onSubmit: (value: string) => void
  disabled?: boolean
  placeholder?: string
}

export function CentralInput({
  onSubmit,
  disabled = false,
  placeholder = "您想做什么？",
}: CentralInputProps) {
  const [value, setValue] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setValue("")
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto flex flex-col sm:flex-row gap-3">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="flex-1 min-h-[52px] px-4 py-3 rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-white text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus-ring-accent focus:border-[var(--color-accent)] resize-none disabled:opacity-50 transition-shadow duration-200"
      />
      <button
        type="button"
        onClick={handleSubmit}
        disabled={disabled || !value.trim()}
        className="btn-accent px-6 py-3 rounded-[var(--radius-lg)] font-medium disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
      >
        提交
      </button>
    </div>
  )
}
