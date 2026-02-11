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
  const [images, setImages] = useState<{ file: File; url: string }[]>([])
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setValue("")
    // 提交后暂不自动清空已选图片，由后续交互决定
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleUploadClick = () => {
    if (disabled) return
    fileInputRef.current?.click()
  }

  const handleFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files
    if (!fileList || fileList.length === 0) {
      return
    }

    Array.from(fileList).forEach((file) => {
      const reader = new FileReader()
      reader.onload = (event) => {
        const result = event.target?.result
        if (typeof result === "string") {
          setImages((prev) => [...prev, { file, url: result }])
        }
      }
      reader.readAsDataURL(file)
    })

    // 允许再次选择同一批文件
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const handleRemoveImage = (index: number) => {
    setImages((prev) => {
      const next = [...prev]
      next.splice(index, 1)
      return next
    })
    if (fileInputRef.current && images.length === 1) {
      fileInputRef.current.value = ""
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-2">
      {images.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-1">
          {images.map((img, index) => (
            <div
              key={img.url}
              className="relative w-16 h-16 rounded-2xl overflow-hidden bg-[var(--color-surface)] border border-[var(--color-border)]"
            >
              <img
                src={img.url}
                alt={img.file.name}
                className="w-full h-full object-cover"
              />
              <button
                type="button"
                onClick={() => handleRemoveImage(index)}
                className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-black/70 text-white text-[10px] flex items-center justify-center"
                aria-label="移除图片"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="w-full min-h-[52px] px-4 py-3 pr-4 pb-7 rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-white text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus-ring-accent focus:border-[var(--color-accent)] resize-none disabled:opacity-50 transition-shadow duration-200"
          />
          <button
            type="button"
            onClick={handleUploadClick}
            disabled={disabled}
            className="absolute left-3 bottom-2 flex items-center justify-center w-7 h-7 rounded-full border border-[var(--color-border)] bg-[var(--color-surface-elevated)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface)] hover:border-[var(--color-border-hover)] text-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="上传图片"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden
            >
              <path
                d="M17.3977 3.9588C15.8361 2.39727 13.3037 2.39727 11.7422 3.9588L5.03365 10.6673C2.60612 13.0952 2.60612 17.0314 5.03365 19.4592C7.46144 21.887 11.3983 21.8875 13.8262 19.4599L20.5348 12.7514C20.8472 12.439 21.3534 12.439 21.6658 12.7514C21.9781 13.0638 21.9782 13.5701 21.6658 13.8825L14.9573 20.591C11.9046 23.6435 6.95518 23.6429 3.90255 20.5903C0.850191 17.5377 0.850191 12.5889 3.90255 9.53624L10.6111 2.82771C12.7975 0.641334 16.3424 0.641334 18.5288 2.82771C20.7149 5.01409 20.7151 8.55906 18.5288 10.7454L11.8699 17.4042C10.5369 18.7372 8.37542 18.7365 7.04241 17.4035C5.70963 16.0705 5.7095 13.9096 7.04241 12.5767L13.7012 5.91785C14.0136 5.60547 14.5199 5.60557 14.8323 5.91785C15.1447 6.23027 15.1447 6.73652 14.8323 7.04894L8.1735 13.7078C7.46543 14.4159 7.46556 15.5642 8.1735 16.2724C8.88167 16.9806 10.03 16.9806 10.7381 16.2724L17.397 9.61358C18.9584 8.05211 18.959 5.52035 17.3977 3.9588Z"
                fill="currentColor"
              />
            </svg>
          </button>
        </div>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="btn-accent px-5 sm:px-6 py-2.5 sm:py-3 rounded-[var(--radius-lg)] font-medium disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
        >
          提交
        </button>
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        multiple
        className="hidden"
        onChange={handleFilesChange}
      />
    </div>
  )
}
