import type { IntentOutput, PlanStep } from "../../types/intent"
import { XhsPreview } from "../xhs"

// 将URL转换为可点击链接的组件
function ContentWithImages({ content }: { content: string }) {
  // 匹配图片URL
  const imageRegex = /(https?:\/\/[^\s]+\.(?:jpg|jpeg|png|gif|webp))/gi
  const parts = content.split(imageRegex)

  if (parts.length === 1) {
    // 没有图片，直接显示文本
    return <>{content}</>
  }

  return (
    <div className="space-y-2">
      {parts.map((part, index) => {
        if (imageRegex.test(part)) {
          // 重置正则lastIndex
          imageRegex.lastIndex = 0
          return (
            <a
              key={index}
              href={part}
              target="_blank"
              rel="noopener noreferrer"
              className="block"
            >
              <img
                src={part}
                alt="内容图片"
                className="max-w-full h-auto rounded-lg border border-gray-200"
              />
              <p className="text-xs text-gray-400 mt-1">{part}</p>
            </a>
          )
        }
        return part ? <span key={index}>{part}</span> : null
      })}
    </div>
  )
}

// 模拟图片数据
const DEMO_IMAGES = [
  "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&h=800&fit=crop",
  "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&h=800&fit=crop",
  "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=800&h=800&fit=crop",
  "https://images.unsplash.com/photo-1560343090-f0409e92791a?w=800&h=800&fit=crop",
]

const DEMO_CONTENT = `分享一款超好用的无线耳机！

🎧 音质超棒，低音浑厚，高音清晰
🔋 续航持久，充一次电可以用一周
🎨 外观时尚，佩戴舒适

强烈推荐给喜欢听音乐的朋友！#好物推荐 #耳机 #音乐爱好者`

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
  // 获取实际内容
  const actualContent = pastSteps.map(([, result]) => result.output || (result as any).response || '').join("\n")
  const hasActualContent = actualContent.trim().length > 0

  // 提取图片
  const imageRegex = /(https?:\/\/[^\s]+\.(?:jpg|jpeg|png|gif|webp))/gi
  const imageMatches = actualContent.match(imageRegex) || []
  const uniqueImages = [...new Set(imageMatches)]

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

      {pastSteps.length > 0 && hasActualContent && (
        <section className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-5 card-shadow">
          <h3 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-3">
            执行结果
          </h3>

          {/* 如果有图片，显示预览 */}
          {uniqueImages.length > 0 && (
            <div className="mb-4">
              <XhsPreview
                images={uniqueImages}
                title="生成的图文内容"
                content={actualContent.replace(imageRegex, "").slice(0, 500)}
                author="AI 生成"
                likes={Math.floor(Math.random() * 1000)}
                comments={Math.floor(Math.random() * 100)}
                collects={Math.floor(Math.random() * 500)}
              />
            </div>
          )}

          {/* 显示实际内容 */}
          <div className="space-y-4">
            {pastSteps.map(([step, result], i) => {
              const content = result.output || (result as any).response || ''
              if (!content.trim()) return null
              return (
                <div key={step.step_id ?? i} className="border-l-2 border-[var(--color-border)] pl-4">
                  <p className="font-medium text-[var(--color-text)]">{result.agent}</p>
                  <div className="text-sm text-[var(--color-text-secondary)] whitespace-pre-wrap mt-1">
                    <ContentWithImages content={content} />
                  </div>
                </div>
              )
            })}
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

      {/* 如果没有实际内容，显示演示 */}
      {pastSteps.length === 0 && (
        <section className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-gradient-to-r from-pink-50 to-orange-50 p-5 card-shadow">
          <h3 className="text-xs font-semibold text-pink-700 mb-3">
            小红书图文预览 - 演示模式
          </h3>
          <div className="flex justify-center">
            <XhsPreview
              images={DEMO_IMAGES}
              title="超好用的无线耳机推荐🎧"
              content={DEMO_CONTENT}
              author="数码达人小王"
              likes={1234}
              comments={89}
              collects={567}
              date="2024年1月15日"
            />
          </div>
        </section>
      )}
    </div>
  )
}