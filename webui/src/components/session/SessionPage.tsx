import { useState, useRef, useEffect } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import {
  postIntent,
  postFulfillability,
  postPlannerStream,
  type SSEStageEvent,
} from "../../api/client"
import type { PlannerResult, PlanStep, StepResult } from "../../types/intent"
import { getAccountContext } from "../../stores/accountContext"
import { useAuth } from "../../contexts/AuthContext"
import { XhsPreview } from "../xhs/XhsPreview"

// 对话消息类型
interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  // 图片列表
  images?: string[]
  // UI 状态
  isExpanded?: boolean
  isLoading?: boolean
  loadingStage?: LoadingStage  // 细化的加载阶段
  hasContent?: boolean  // 是否有实际生成内容
  showPreview?: boolean  // 是否显示小红书预览
  previewMode?: 'pc' | 'mobile'  // 预览模式
  isImageOnlyResponse?: boolean  // 是否只是配图响应（内容无实质文本）
  // 错误状态
  error?: string
  retryInput?: string  // 重试时使用的原始输入
  retryContext?: Record<string, string>  // 重试时的上下文
  // 澄清选项
  clarification?: {
    question: string
    options: Array<{
      label: string
      value: string
      category?: string
    }>
  }
  // 扩展信息
  details?: {
    planSteps?: PlanStep[]
    executionDetails?: Array<{
      agent: string
      inputSummary: string
      output: string
    }>
    isExpandable?: boolean
  }
}

// 加载阶段类型
type LoadingStage = {
  step: 'planning' | 'agent' | 'complete' | 'error'
  message: string
  agent?: string  // 当前执行的 agent 名称
}

// 生成唯一ID
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

// 账号阶段选项
const ACCOUNT_STAGE_OPTIONS = [
  { label: "起号", value: "起号" },
  { label: "冷启动", value: "冷启动" },
  { label: "放量", value: "放量" },
  { label: "变现", value: "变现" },
]

// 账号人设选项
const ACCOUNT_PERSONA_OPTIONS = [
  { label: "职场女性", value: "职场女性" },
  { label: "学生党", value: "学生党" },
  { label: "宝妈", value: "宝妈" },
  { label: "健身达人", value: "健身达人" },
  { label: "美食博主", value: "美食博主" },
  { label: "旅行达人", value: "旅行达人" },
  { label: "穿搭博主", value: "穿搭博主" },
  { label: "数码极客", value: "数码极客" },
]

// 内容形式选项
const CONTENT_FORM_OPTIONS = [
  { label: "图文", value: "图文" },
  { label: "视频", value: "视频" },
  { label: "图文+视频", value: "图文+视频" },
]

// 平台选项
const PLATFORM_OPTIONS = [
  { label: "小红书", value: "小红书" },
  { label: "抖音", value: "抖音" },
  { label: "微信", value: "微信" },
  { label: "朋友圈", value: "朋友圈" },
  { label: "微博", value: "微博" },
]

// 行业选项
const INDUSTRY_OPTIONS = [
  { label: "美妆", value: "美妆" },
  { label: "美食", value: "美食" },
  { label: "穿搭", value: "穿搭" },
  { label: "数码", value: "数码" },
  { label: "家居", value: "家居" },
  { label: "健身", value: "健身" },
  { label: "教育", value: "教育" },
  { label: "旅行", value: "旅行" },
  { label: "母婴", value: "母婴" },
  { label: "其他", value: "其他" },
]

// 目标选项
const GOAL_OPTIONS = [
  { label: "涨粉", value: "涨粉" },
  { label: "种草", value: "种草" },
  { label: "转化", value: "转化" },
  { label: "品牌曝光", value: "品牌曝光" },
]

// 主题选项（热门主题）
const TOPIC_OPTIONS = [
  { label: "咖啡", value: "咖啡" },
  { label: "护肤", value: "护肤" },
  { label: "穿搭分享", value: "穿搭分享" },
  { label: "美食探店", value: "美食探店" },
  { label: "旅行攻略", value: "旅行攻略" },
  { label: "健身打卡", value: "健身打卡" },
  { label: "好物推荐", value: "好物推荐" },
  { label: "日常Vlog", value: "日常Vlog" },
]

// 格式化内容（支持 Markdown 基础语法）
function FormattedContent({ content }: { content: string }) {
  const lines = content.split("\n")
  return (
    <div className="whitespace-pre-wrap">
      {lines.map((line, i) => {
        if (line.startsWith("# ")) {
          return <h1 key={i} className="text-xl font-bold mt-4 mb-2">{line.slice(2)}</h1>
        }
        if (line.startsWith("## ")) {
          return <h2 key={i} className="text-lg font-semibold mt-3 mb-2">{line.slice(3)}</h2>
        }
        if (line.startsWith("### ")) {
          return <h3 key={i} className="text-base font-medium mt-2 mb-1">{line.slice(4)}</h3>
        }
        if (line.startsWith("- ") || line.startsWith("* ")) {
          return <li key={i} className="ml-4">{line.slice(2)}</li>
        }
        if (line.includes("**")) {
          const parts = line.split(/(\*\*[^*]+\*\*)/g)
          return (
            <p key={i}>
              {parts.map((part, j) => {
                if (part.startsWith("**") && part.endsWith("**")) {
                  return <strong key={j}>{part.slice(2, -2)}</strong>
                }
                return part
              })}
            </p>
          )
        }
        return <p key={i}>{line}</p>
      })}
    </div>
  )
}

// 澄清选项组件
function ClarificationPanel({
  clarification,
  onSelect,
  disabled,
}: {
  clarification: ChatMessage["clarification"]
  onSelect: (value: string) => void
  disabled: boolean
}) {
  if (!clarification) return null

  // 按类别分组选项
  const groupedOptions: Record<string, typeof clarification.options> = {}
  clarification.options.forEach(opt => {
    const category = opt.category || "其他"
    if (!groupedOptions[category]) groupedOptions[category] = []
    groupedOptions[category].push(opt)
  })

  return (
    <div className="mt-3">
      <p className="text-sm text-[var(--color-text-secondary)] mb-3">{clarification.question}</p>
      {Object.entries(groupedOptions).map(([category, options]) => (
        <div key={category} className="mb-3">
          {Object.keys(groupedOptions).length > 1 && (
            <p className="text-xs text-[var(--color-text-muted)] mb-2">{category}：</p>
          )}
          <div className="flex flex-wrap gap-2">
            {options.map(opt => (
              <button
                key={opt.value}
                type="button"
                onClick={() => onSelect(opt.value)}
                disabled={disabled}
                className="px-3 py-1.5 text-sm rounded-full border border-[var(--color-accent)] text-[var(--color-accent)] hover:bg-[var(--color-accent)] hover:text-white transition-colors disabled:opacity-50"
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// 消息气泡组件
function MessageBubble({
  message,
  allMessages,
  onToggleExpand,
  onTogglePreview,
  onSwitchPreviewMode,
  onClarificationSelect,
  onRetry,
}: {
  message: ChatMessage
  allMessages: ChatMessage[]
  onToggleExpand: (id: string) => void
  onTogglePreview: (id: string) => void
  onSwitchPreviewMode: (id: string, mode: 'pc' | 'mobile') => void
  onClarificationSelect: (id: string, value: string) => void
  onRetry: (id: string) => void
}) {
  const isUser = message.role === "user"
  const hasImages = message.images && message.images.length > 0
  const hasError = message.error && message.retryInput

  // 从内容中提取标题（通常是第一个 # 标题或第一行加粗文字）
  const extractTitle = (content: string): { title: string | undefined; body: string } => {
    const lines = content.split('\n')
    let title: string | undefined
    let bodyStartIndex = 0

    // 查找第一个 # 标题
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()
      if (line.startsWith('# ')) {
        title = line.slice(2).trim()
        bodyStartIndex = i + 1
        break
      }
    }

    // 如果没有标题，使用第一行作为标题（如果不太长）
    if (!title && lines.length > 0) {
      const firstLine = lines[0].trim()
      if (firstLine.length > 0 && firstLine.length <= 30) {
        title = firstLine
        bodyStartIndex = 1
      }
    }

    const body = lines.slice(bodyStartIndex).join('\n').trim()
    return { title, body }
  }

  // 获取预览内容：如果是配图响应，合并之前的文本内容
  const getPreviewContent = (): { title: string | undefined; body: string } => {
    // 如果不是纯配图响应，直接使用当前内容
    if (!message.isImageOnlyResponse) {
      return extractTitle(message.content)
    }

    // 找到当前消息在列表中的位置
    const currentIndex = allMessages.findIndex(m => m.id === message.id)

    // 向前查找最近的有实质内容的 assistant 消息
    for (let i = currentIndex - 1; i >= 0; i--) {
      const prevMsg = allMessages[i]
      if (
        prevMsg.role === "assistant" &&
        !prevMsg.isLoading &&
        prevMsg.hasContent &&
        prevMsg.content &&
        !prevMsg.isImageOnlyResponse
      ) {
        return extractTitle(prevMsg.content)
      }
    }

    // 没找到就使用当前内容
    return extractTitle(message.content)
  }

  const previewContent = getPreviewContent()

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div className={`max-w-[85%] ${isUser ? "order-2" : "order-1"}`}>
        {/* 用户消息 */}
        {isUser && (
          <div className="rounded-2xl rounded-tr-sm bg-[var(--color-accent)] text-white px-4 py-2.5">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        )}

        {/* AI 消息 */}
        {!isUser && (
          <div className="rounded-2xl rounded-tl-sm bg-[var(--color-surface-elevated)] border border-[var(--color-border)] px-4 py-3">
            {message.isLoading ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-[var(--color-text-secondary)]">
                  <span className="w-4 h-4 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" />
                  <span className="text-sm font-medium">
                    {message.loadingStage?.message || "思考中..."}
                  </span>
                </div>
                {/* 进度指示器 - 3个阶段：规划 -> 执行 -> 完成 */}
                <div className="flex gap-1.5 pl-6">
                  <div className={`w-2 h-2 rounded-full transition-colors ${
                    ['planning', 'agent', 'complete'].indexOf(message.loadingStage?.step || 'intent') >= 0
                      ? 'bg-[var(--color-accent)]' : 'bg-[var(--color-border)]'
                  }`} title="任务规划" />
                  <div className={`w-2 h-2 rounded-full transition-colors ${
                    ['agent', 'complete'].indexOf(message.loadingStage?.step || 'intent') >= 0
                      ? 'bg-[var(--color-accent)]' : 'bg-[var(--color-border)]'
                  }`} title="生成内容" />
                  <div className={`w-2 h-2 rounded-full transition-colors ${
                    message.loadingStage?.step === 'complete'
                      ? 'bg-[var(--color-accent)]' : 'bg-[var(--color-border)]'
                  }`} title="完成" />
                </div>
              </div>
            ) : (
              <>
                {/* 错误状态 - 显示错误信息和重试按钮 */}
                {hasError ? (
                  <div className="space-y-3">
                    <p className="text-[var(--color-text)]">{message.content}</p>
                    <button
                      type="button"
                      onClick={() => onRetry(message.id)}
                      className="px-4 py-2 text-sm rounded-lg bg-[var(--color-accent)] text-white hover:opacity-90 transition-opacity"
                    >
                      🔄 重试
                    </button>
                  </div>
                ) : (
                  <>
                    {/* 有图片时显示小红书预览卡片 */}
                    {hasImages && message.showPreview !== false ? (
                  <div className="space-y-3">
                    {/* 预览控制栏 */}
                    <div className="flex items-center justify-between gap-2 pb-2 border-b border-[var(--color-border)]">
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => onSwitchPreviewMode(message.id, 'pc')}
                          className={`px-2 py-1 text-xs rounded transition-colors ${
                            message.previewMode !== 'mobile'
                              ? 'bg-[var(--color-accent)] text-white'
                              : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface)]'
                          }`}
                        >
                          💻 PC端
                        </button>
                        <button
                          type="button"
                          onClick={() => onSwitchPreviewMode(message.id, 'mobile')}
                          className={`px-2 py-1 text-xs rounded transition-colors ${
                            message.previewMode === 'mobile'
                              ? 'bg-[var(--color-accent)] text-white'
                              : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface)]'
                          }`}
                        >
                          📱 移动端
                        </button>
                      </div>
                      <button
                        type="button"
                        onClick={() => onTogglePreview(message.id)}
                        className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]"
                      >
                        ✕ 关闭预览
                      </button>
                    </div>

                    {/* 预览卡片 */}
                    <XhsPreview
                      images={message.images!}
                      title={previewContent.title}
                      content={previewContent.body || message.content}
                      author="小红书博主"
                      likes={128}
                      comments={32}
                      collects={56}
                      forceMobile={message.previewMode === 'mobile'}
                    />

                    {/* 图片链接（可折叠） */}
                    <details className="text-xs">
                      <summary className="cursor-pointer text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]">
                        查看图片链接
                      </summary>
                      <div className="mt-2 space-y-1 pl-2">
                        {message.images!.map((url, i) => (
                          <div key={i} className="flex items-center gap-1">
                            <span className="text-[var(--color-text-muted)]">{i + 1}.</span>
                            <a
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[var(--color-accent)] hover:underline truncate"
                            >
                              {url}
                            </a>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                ) : hasImages ? (
                  /* 有图片但预览关闭时，显示开启按钮 */
                  <div className="space-y-3">
                    <div className="text-[var(--color-text)]">
                      <FormattedContent content={message.content} />
                    </div>
                    <button
                      type="button"
                      onClick={() => onTogglePreview(message.id)}
                      className="text-xs text-[var(--color-accent)] hover:underline"
                    >
                      📱 查看小红书预览效果
                    </button>
                  </div>
                ) : (
                  /* 无图片时只显示文本 */
                  <div className="text-[var(--color-text)]">
                    <FormattedContent content={message.content} />
                  </div>
                )}

                {/* 澄清选项 */}
                {message.clarification && !hasError && (
                  <ClarificationPanel
                    clarification={message.clarification}
                    onSelect={(value) => onClarificationSelect(message.id, value)}
                    disabled={false}
                  />
                )}

                {/* 执行详情（可折叠） */}
                {message.details?.isExpandable && message.details.executionDetails && !hasError && (
                  <div className="mt-3 pt-3 border-t border-[var(--color-border)]">
                    <button
                      type="button"
                      onClick={() => onToggleExpand(message.id)}
                      className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] flex items-center gap-1"
                    >
                      <span className={`transition-transform ${message.isExpanded ? "rotate-90" : ""}`}>▶</span>
                      {message.isExpanded ? "收起执行详情" : "查看执行详情"}
                    </button>

                    {message.isExpanded && (
                      <div className="mt-2 space-y-2 text-sm">
                        {message.details.executionDetails.map((detail, i) => (
                          <div key={i} className="pl-3 border-l-2 border-[var(--color-border)]">
                            <p className="font-medium text-[var(--color-text)]">{detail.agent}</p>
                            <p className="text-[var(--color-text-secondary)] text-xs">{detail.inputSummary}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                  </>
                )}
              </>
            )}
          </div>
        )}

        {/* 时间戳 */}
        <p className={`text-xs text-[var(--color-text-muted)] mt-1 ${isUser ? "text-right" : "text-left"}`}>
          {message.timestamp.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>
    </div>
  )
}

// 检查是否有实际生成内容
function hasGeneratedContent(messages: ChatMessage[]): boolean {
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i]
    if (msg.role === "assistant" && !msg.isLoading && msg.hasContent) {
      return true
    }
  }
  return false
}

// 检查是否需要澄清
function needsClarification(messages: ChatMessage[]): boolean {
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i]
    if (msg.role === "assistant" && !msg.isLoading && msg.clarification) {
      return true
    }
  }
  return false
}

export function SessionPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const initialInput = (location.state as { userInput?: string } | null)?.userInput ?? ""
  const auth = useAuth()

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pendingContext, setPendingContext] = useState<Record<string, string>>({})

  // session_id 由用户ID和会话ID组成
  // 用户ID：登录用户使用用户名，未登录使用匿名标识
  // 会话ID：每次进入会话页面时生成新的
  const [sessionId] = useState(() => {
    const userId = auth?.username || "anonymous"
    const timestamp = Date.now()
    const random = Math.random().toString(36).substr(2, 9)
    return `${userId}-${timestamp}-${random}`
  })
  const [isFirstRequest, setIsFirstRequest] = useState(true)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const accountContext = getAccountContext()

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 处理初始输入
  useEffect(() => {
    if (!initialInput.trim()) return

    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      content: initialInput,
      timestamp: new Date(),
    }

    const loadingMessage: ChatMessage = {
      id: generateId(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    }

    setMessages([userMessage, loadingMessage])
    processRequest(initialInput, loadingMessage.id)
    window.history.replaceState({}, "")
  }, [initialInput])

  // 构建澄清选项
  const buildClarificationOptions = (
    missingSlots: string[],
    clarificationQuestion: string
  ): ChatMessage["clarification"] => {
    const options: Array<{ label: string; value: string; category?: string }> = []

    missingSlots.forEach(slot => {
      if (slot === "platform") {
        PLATFORM_OPTIONS.forEach(opt => {
          options.push({ ...opt, category: "平台" })
        })
      } else if (slot === "industry") {
        INDUSTRY_OPTIONS.forEach(opt => {
          options.push({ ...opt, category: "行业" })
        })
      } else if (slot === "goal") {
        GOAL_OPTIONS.forEach(opt => {
          options.push({ ...opt, category: "目标" })
        })
      } else if (slot === "topic") {
        TOPIC_OPTIONS.forEach(opt => {
          options.push({ ...opt, category: "主题" })
        })
      } else if (slot === "account_stage") {
        ACCOUNT_STAGE_OPTIONS.forEach(opt => {
          options.push({ ...opt, category: "账号阶段" })
        })
      } else if (slot === "account_persona") {
        ACCOUNT_PERSONA_OPTIONS.forEach(opt => {
          options.push({ ...opt, category: "账号人设" })
        })
      } else if (slot === "content_form") {
        CONTENT_FORM_OPTIONS.forEach(opt => {
          options.push({ ...opt, category: "内容形式" })
        })
      } else {
        // 对于未知的槽位，从问题中提取选项
        // 例如："账号阶段（起号、冷启动、放量、变现）"
        const match = clarificationQuestion.match(/[（(]([^)）]+)[)）]/)
        if (match) {
          const values = match[1].split(/[、,，]/).map(v => v.trim())
          values.forEach(value => {
            options.push({ label: value, value, category: slot })
          })
        }
      }
    })

    // 如果没有匹配的槽位，返回空（使用文本输入）
    if (options.length === 0) {
      return undefined
    }

    return {
      question: clarificationQuestion,
      options,
    }
  }

  // 处理请求
  const processRequest = async (userInput: string, messageId: string, context: Record<string, string> = {}) => {
    setIsProcessing(true)
    setError(null)

    // 辅助函数：更新加载阶段
    const updateLoadingStage = (stage: LoadingStage) => {
      setMessages(prev => prev.map(msg =>
        msg.id === messageId
          ? { ...msg, loadingStage: stage }
          : msg
      ))
    }

    try {
      // 合并上下文，包含 session_id 和 is_new_session
      const mergedContext = {
        ...accountContext,
        ...context,
        session_id: sessionId,
        is_new_session: isFirstRequest,
        // 传递已收集的槽位信息，避免重复询问
        slots: {
          platform: context.platform || pendingContext.platform,
          industry: context.industry || pendingContext.industry,
          goal: context.goal || pendingContext.goal,
          topic: context.topic || pendingContext.topic,
          account_stage: context.account_stage || pendingContext.account_stage,
          account_persona: context.account_persona || pendingContext.account_persona,
          content_form: context.content_form || pendingContext.content_form || "图文",
        },
        original_demand: messages.find(m => m.role === "user")?.content || userInput,
      }

      // 标记已经不是首次请求了
      if (isFirstRequest) {
        setIsFirstRequest(false)
      }

      // 1. 意图识别（静默执行，直接进入规划阶段显示）
      const intent = await postIntent(userInput, mergedContext)

      // 显示规划中状态
      updateLoadingStage({ step: 'planning', message: '正在规划任务...' })

      // 处理非营销意图
      const nonMarketingResponses: Record<string, string> = {
        greeting: "你好！我是小红书营销助手，可以帮你：\n\n📝 生成小红书笔记内容\n📊 做选题策划\n🎯 制定账号策略\n📈 规划投流方案\n\n有什么可以帮到你的吗？",
        help: "我可以帮你完成以下营销任务：\n\n1️⃣ **内容生成** - 写小红书笔记、朋友圈文案等\n2️⃣ **选题策划** - 根据行业热点推荐选题\n3️⃣ **账号战略** - 制定账号定位和发展规划\n4️⃣ **投流规划** - 制定付费推广策略\n5️⃣ **内容评估** - 评估内容质量和优化建议\n\n试试说：\"帮我写一篇咖啡种草笔记\"",
        feedback: "感谢你的反馈！如果你有任何问题或建议，欢迎告诉我，我会尽力改进。\n\n如果是功能问题，请描述具体遇到的困难，我会帮你解决。",
        out_of_scope: "抱歉，这个问题超出了我的服务范围 😅\n\n我专注于**营销内容创作**，比如：\n- 小红书笔记\n- 选题策划\n- 账号运营\n\n如果你有营销相关的需求，我很乐意帮忙！",
      }

      if (nonMarketingResponses[intent.intent_type]) {
        setMessages(prev => prev.map(msg =>
          msg.id === messageId
            ? {
                ...msg,
                isLoading: false,
                content: nonMarketingResponses[intent.intent_type],
                hasContent: false,
              }
            : msg
        ))
        setIsProcessing(false)
        return
      }

      // 如果需要澄清
      if (intent.needs_clarification && intent.clarification_question) {
        const clarification = buildClarificationOptions(
          intent.missing_slots || [],
          intent.clarification_question
        )

        setMessages(prev => prev.map(msg =>
          msg.id === messageId
            ? {
                ...msg,
                isLoading: false,
                content: clarification ? "" : `需要补充信息：\n\n${intent.clarification_question}`,
                clarification,
              }
            : msg
        ))
        setIsProcessing(false)
        return
      }

      // 2. 可执行性检查（静默执行，不显示进度）
      const fulfillResult = await postFulfillability(intent, mergedContext)
      if (!fulfillResult.can_fulfill) {
        setMessages(prev => prev.map(msg =>
          msg.id === messageId
            ? {
                ...msg,
                isLoading: false,
                content: `暂时无法执行：${fulfillResult.message_to_user || "请稍后再试"}`,
              }
            : msg
        ))
        setIsProcessing(false)
        return
      }

      // 3. 执行 Planner（流式）
      let plannerResult: PlannerResult | undefined

      await postPlannerStream(intent, mergedContext, {
        onStage: (event: SSEStageEvent) => {
          // 实时更新进度状态
          // agent 阶段统一显示"正在生成内容..."
          const message = event.step === 'agent' || event.step === 'step_done'
            ? '正在生成内容...'
            : event.message
          updateLoadingStage({
            step: event.step === 'step_done' ? 'agent' : event.step,
            message,
            agent: event.agent,
          })
        },
        onResult: (result: PlannerResult) => {
          plannerResult = result
        },
        onError: (error: string) => {
          throw new Error(error)
        },
      })

      if (!plannerResult) {
        throw new Error("未收到执行结果")
      }

      // 使用断言确保 TypeScript 知道 plannerResult 不为 null
      const result = plannerResult as PlannerResult

      // 提取主要内容
      const mainContent = (result.past_steps ?? [])
        .map(([, stepResult]: [PlanStep, StepResult]) => stepResult.output || stepResult.response || "")
        .filter(Boolean)
        .join("\n\n")

      // 提取图片（合并所有步骤的图片）
      const allImages: string[] = []
      ;(result.past_steps ?? []).forEach(([, stepResult]: [PlanStep, StepResult]) => {
        if (stepResult.images && stepResult.images.length > 0) {
          allImages.push(...stepResult.images)
        }
      })
      // 也检查顶层 images 字段
      if (result.images && result.images.length > 0) {
        allImages.push(...result.images)
      }

      // 提取执行详情
      const executionDetails = (result.past_steps ?? []).map(([step, stepResult]: [PlanStep, StepResult]) => ({
        agent: step.agent || stepResult.agent || "未知",
        inputSummary: step.input_summary || "",
        output: stepResult.output || stepResult.response || "",
      }))

      // 判断返回的内容是否只是配图确认信息（而非新内容）
      const isImageOnlyResponse = allImages.length > 0 && (
        mainContent.length < 50 ||
        mainContent.includes("封面图地址") ||
        mainContent.includes("配图") ||
        mainContent.includes("封面图") ||
        mainContent.includes("图片地址") ||
        mainContent.includes("已为您生成")
      )

      // 更新消息
      setMessages(prev => prev.map(msg =>
        msg.id === messageId
          ? {
              ...msg,
              isLoading: false,
              content: mainContent || result.response || "执行完成",
              images: allImages.length > 0 ? allImages : undefined,
              hasContent: !!mainContent,
              // 标记这条消息是否只是配图响应
              isImageOnlyResponse: isImageOnlyResponse || undefined,
              details: {
                planSteps: result.plan?.steps ?? [],
                executionDetails,
                isExpandable: executionDetails.length > 0,
              },
              isExpanded: false,
              showPreview: allImages.length > 0 ? true : undefined,
            }
          : msg
      ))

    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : String(e)
      setError(errorMessage)
      setMessages(prev => prev.map(msg =>
        msg.id === messageId
          ? {
              ...msg,
              isLoading: false,
              content: `生成失败：${errorMessage}`,
              error: errorMessage,
              retryInput: userInput,
              retryContext: context,
            }
          : msg
      ))
    } finally {
      setIsProcessing(false)
    }
  }

  // 重试失败的请求
  const handleRetry = (messageId: string) => {
    const failedMsg = messages.find(m => m.id === messageId)
    if (!failedMsg?.retryInput) return

    // 重新设置加载状态
    setMessages(prev => prev.map(msg =>
      msg.id === messageId
        ? { ...msg, isLoading: true, content: "", error: undefined }
        : msg
    ))

    // 重新处理请求
    processRequest(failedMsg.retryInput, messageId, failedMsg.retryContext || {})
  }

  // 发送消息
  const handleSend = () => {
    if (!inputValue.trim() || isProcessing) return

    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    }

    const loadingMessage: ChatMessage = {
      id: generateId(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    }

    setMessages(prev => [...prev, userMessage, loadingMessage])
    setInputValue("")

    // 构建包含上下文的请求
    const contextContent = messages
      .filter(m => m.role === "assistant" && !m.isLoading && m.hasContent)
      .map(m => m.content)
      .join("\n\n")

    const enhancedInput = contextContent
      ? `之前的对话内容：\n${contextContent}\n\n用户新的需求：${userMessage.content}`
      : userMessage.content

    processRequest(enhancedInput, loadingMessage.id, pendingContext)
    setPendingContext({})
  }

  // 处理澄清选项点击
  const handleClarificationSelect = (messageId: string, value: string) => {
    // 添加用户选择的消息
    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      content: value,
      timestamp: new Date(),
    }

    // 更新待处理的上下文
    const newContext = { ...pendingContext }

    // 根据值判断类型并更新
    if (PLATFORM_OPTIONS.some(opt => opt.value === value)) {
      newContext.platform = value
    } else if (INDUSTRY_OPTIONS.some(opt => opt.value === value)) {
      newContext.industry = value
    } else if (GOAL_OPTIONS.some(opt => opt.value === value)) {
      newContext.goal = value
    } else if (TOPIC_OPTIONS.some(opt => opt.value === value)) {
      newContext.topic = value
    } else if (ACCOUNT_STAGE_OPTIONS.some(opt => opt.value === value)) {
      newContext.account_stage = value
    } else if (ACCOUNT_PERSONA_OPTIONS.some(opt => opt.value === value)) {
      newContext.account_persona = value
    } else if (CONTENT_FORM_OPTIONS.some(opt => opt.value === value)) {
      newContext.content_form = value
    } else {
      // 不在预定义选项中，根据当前澄清问题的类型推断
      const currentMessage = messages.find(m => m.id === messageId)
      const currentCategory = currentMessage?.clarification?.options?.[0]?.category
      if (currentCategory === "平台") {
        newContext.platform = value
      } else if (currentCategory === "行业") {
        newContext.industry = value
      } else if (currentCategory === "目标") {
        newContext.goal = value
      } else if (currentCategory === "主题") {
        newContext.topic = value
      } else if (currentCategory === "账号阶段") {
        newContext.account_stage = value
      } else if (currentCategory === "账号人设") {
        newContext.account_persona = value
      } else if (currentCategory === "内容形式") {
        newContext.content_form = value
      } else {
        // 未知类别，直接存储
        newContext[currentCategory || "custom"] = value
      }
    }

    setPendingContext(newContext)

    // 清除澄清消息，添加加载消息
    const loadingMessage: ChatMessage = {
      id: generateId(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    }

    setMessages(prev => [
      ...prev.filter(m => m.id !== messageId),
      userMessage,
      loadingMessage,
    ])

    // 检查是否还需要更多澄清
    const currentMessage = messages.find(m => m.id === messageId)
    const remainingCategories = new Set(
      currentMessage?.clarification?.options
        .filter(opt => opt.value !== value)
        .map(opt => opt.category)
        .filter(Boolean)
    )

    // 如果还有其他类别的选项需要选择，继续显示澄清
    if (remainingCategories.size > 0) {
      // 找出还缺少哪些槽位
      const missingSlots: string[] = []
      if (!newContext.platform && remainingCategories.has("平台")) missingSlots.push("platform")
      if (!newContext.industry && remainingCategories.has("行业")) missingSlots.push("industry")
      if (!newContext.goal && remainingCategories.has("目标")) missingSlots.push("goal")
      if (!newContext.topic && remainingCategories.has("主题")) missingSlots.push("topic")
      if (!newContext.account_stage && remainingCategories.has("账号阶段")) missingSlots.push("account_stage")
      if (!newContext.account_persona && remainingCategories.has("账号人设")) missingSlots.push("account_persona")
      if (!newContext.content_form && remainingCategories.has("内容形式")) missingSlots.push("content_form")

      if (missingSlots.length > 0) {
        const clarification = buildClarificationOptions(
          missingSlots,
          "请继续选择："
        )

        setMessages(prev => prev.map(msg =>
          msg.id === loadingMessage.id
            ? {
                ...msg,
                isLoading: false,
                clarification,
              }
            : msg
        ))
        setIsProcessing(false)
        return
      }
    }

    // 继续处理请求 - 使用完整的对话历史
    const conversationHistory = messages
      .filter(m => m.role === "user")
      .map(m => m.content)
      .join(" -> ")
    const fullInput = conversationHistory ? `${conversationHistory} -> ${value}` : value
    processRequest(fullInput, loadingMessage.id, newContext)
  }

  // 切换详情展开
  const handleToggleExpand = (id: string) => {
    setMessages(prev => prev.map(msg =>
      msg.id === id ? { ...msg, isExpanded: !msg.isExpanded } : msg
    ))
  }

  // 切换预览显示
  const handleTogglePreview = (id: string) => {
    setMessages(prev => prev.map(msg =>
      msg.id === id ? { ...msg, showPreview: msg.showPreview === false ? true : false } : msg
    ))
  }

  // 切换预览模式（PC/移动端）
  const handleSwitchPreviewMode = (id: string, mode: 'pc' | 'mobile') => {
    setMessages(prev => prev.map(msg =>
      msg.id === id ? { ...msg, previewMode: mode } : msg
    ))
  }

  // 快捷操作
  const handleQuickAction = (action: string) => {
    const actions: Record<string, string> = {
      images: "请为这篇内容推荐或生成合适的配图",
      shorten: "请帮我缩短内容，更加简洁有力",
      expand: "请帮我扩展内容，增加更多细节和案例",
      tone: "请帮我调整语气，更加活泼有趣",
      format: "请帮我优化排版和格式，使其更易阅读",
    }
    setInputValue(actions[action] || "")
  }

  // 是否显示快捷操作
  const showQuickActions = hasGeneratedContent(messages) && !needsClarification(messages)

  if (messages.length === 0 && !initialInput) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-[var(--color-text-secondary)] mb-4">未收到输入，请从首页提交需求。</p>
        <button
          type="button"
          onClick={() => navigate("/")}
          className="text-[var(--color-accent)] font-medium hover:underline underline-offset-4"
        >
          返回首页
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto">
      {/* 返回按钮 */}
      <div className="px-4 py-3 border-b border-[var(--color-border)]">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] text-sm font-medium transition-colors"
        >
          ← 返回首页
        </button>
      </div>

      {/* 消息列表区域 */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.map(message => (
          <MessageBubble
            key={message.id}
            message={message}
            allMessages={messages}
            onToggleExpand={handleToggleExpand}
            onTogglePreview={handleTogglePreview}
            onSwitchPreviewMode={handleSwitchPreviewMode}
            onClarificationSelect={handleClarificationSelect}
            onRetry={handleRetry}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 快捷操作栏 - 只在有生成内容时显示 */}
      {showQuickActions && (
        <div className="px-4 py-2 border-t border-[var(--color-border)] bg-[var(--color-surface)]">
          <div className="flex gap-2 overflow-x-auto pb-2">
            <button
              type="button"
              onClick={() => handleQuickAction("images")}
              disabled={isProcessing}
              className="shrink-0 px-3 py-1.5 text-sm rounded-full border border-[var(--color-border)] hover:bg-[var(--color-surface-elevated)] transition-colors disabled:opacity-50"
            >
              🖼️ 配图
            </button>
            <button
              type="button"
              onClick={() => handleQuickAction("shorten")}
              disabled={isProcessing}
              className="shrink-0 px-3 py-1.5 text-sm rounded-full border border-[var(--color-border)] hover:bg-[var(--color-surface-elevated)] transition-colors disabled:opacity-50"
            >
              ✂️ 缩短
            </button>
            <button
              type="button"
              onClick={() => handleQuickAction("expand")}
              disabled={isProcessing}
              className="shrink-0 px-3 py-1.5 text-sm rounded-full border border-[var(--color-border)] hover:bg-[var(--color-surface-elevated)] transition-colors disabled:opacity-50"
            >
              📝 扩展
            </button>
            <button
              type="button"
              onClick={() => handleQuickAction("tone")}
              disabled={isProcessing}
              className="shrink-0 px-3 py-1.5 text-sm rounded-full border border-[var(--color-border)] hover:bg-[var(--color-surface-elevated)] transition-colors disabled:opacity-50"
            >
              🎭 调整语气
            </button>
            <button
              type="button"
              onClick={() => handleQuickAction("format")}
              disabled={isProcessing}
              className="shrink-0 px-3 py-1.5 text-sm rounded-full border border-[var(--color-border)] hover:bg-[var(--color-surface-elevated)] transition-colors disabled:opacity-50"
            >
              📋 优化格式
            </button>
          </div>
        </div>
      )}

      {/* 输入区域 */}
      <div className="px-4 py-3 border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="flex gap-2 items-end">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            placeholder="输入修改意见或继续对话... (Shift+Enter 换行)"
            disabled={isProcessing}
            rows={1}
            className="flex-1 px-4 py-2.5 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-elevated)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] disabled:opacity-50 resize-none max-h-32 overflow-y-auto"
            style={{
              height: 'auto',
              minHeight: '42px',
            }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement
              target.style.height = 'auto'
              target.style.height = Math.min(target.scrollHeight, 128) + 'px'
            }}
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={isProcessing || !inputValue.trim()}
            className="shrink-0 w-10 h-10 rounded-full bg-[var(--color-accent)] text-white flex items-center justify-center disabled:opacity-50 hover:opacity-90 transition-opacity"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg bg-red-100 border border-red-200 text-red-800 text-sm">
          {error}
          <button
            type="button"
            onClick={() => setError(null)}
            className="ml-2 text-red-600 hover:text-red-800"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  )
}