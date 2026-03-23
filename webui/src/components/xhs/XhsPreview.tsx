import React from "react"
import { Heart, MessageCircle, Star } from "lucide-react"
import { ImageCarousel } from "./ImageCarousel"

export interface XhsPreviewProps {
  images: string[]
  title?: string
  content: string
  author?: string
  avatar?: string
  likes?: number
  comments?: number
  collects?: number
  date?: string
  forceMobile?: boolean
}

// 净化内容，提取真正的正文
function parseContent(rawContent: string): { title: string | undefined; cleanContent: string } {
  let title: string | undefined
  let content = rawContent

  // 1. 移除开头废话（如"占位：..."、"必须分享..."等）
  content = content.replace(/^(占位：[^\n]*\n?|必须分享[^\n]*\n?|需要进一步处理的[^\n]*\n?)/g, '')

  // 2. 提取标题备选中的第一个作为标题
  const titleMatch = content.match(/##\s*①?\s*标题备选[\s\S]*?(\d+\.\s*\*\*([^*]+)\*\*)/)
  if (titleMatch) {
    title = titleMatch[2].trim()
    // 移除整个标题备选区块
    content = content.replace(/##\s*①?\s*标题备选[\s\S]*?(?=##|$)/, '')
  }

  // 3. 提取正文区块
  const bodyMatch = content.match(/##\s*②?\s*正文\s*([\s\S]*?)(?=##|$)/)
  if (bodyMatch) {
    content = bodyMatch[1].trim()
  }

  // 4. 移除段落标识符（如"## ①"、"## ②"等）
  content = content.replace(/##\s*[①②③④⑤]?\s*/g, '')

  // 5. 移除元信息标记（如"**开头钩子**"、"**正文**"等）
  content = content.replace(/\*\*(开头钩子|正文|结尾|互动引导|标签)\*\*/g, '')

  // 6. 移除"配图建议"等后续区块
  content = content.replace(/##\s*③?\s*配图建议[\s\S]*/g, '')

  // 7. 清理多余的空行
  content = content.replace(/\n{3,}/g, '\n\n').trim()

  return { title, cleanContent: content }
}

// 渲染Markdown格式
function RenderMarkdown({ content }: { content: string }) {
  const lines = content.split('\n')

  return (
    <div className="text-gray-700 text-sm leading-relaxed">
      {lines.map((line, i) => {
        // 标题
        if (line.startsWith('# ')) {
          return <h1 key={i} className="font-bold text-base mt-3 mb-2">{line.slice(2)}</h1>
        }
        if (line.startsWith('## ')) {
          return <h2 key={i} className="font-semibold text-sm mt-2 mb-1">{line.slice(3)}</h2>
        }

        // 列表项
        if (line.startsWith('- ') || line.startsWith('• ')) {
          return (
            <p key={i} className="pl-3 relative before:content-['•'] before:absolute before:left-0 before:text-gray-400">
              {renderInlineMarkdown(line.slice(2))}
            </p>
          )
        }
        if (/^\d+\.\s/.test(line)) {
          return (
            <p key={i} className="pl-4">
              {renderInlineMarkdown(line)}
            </p>
          )
        }

        // 空行
        if (!line.trim()) {
          return <br key={i} />
        }

        // 普通段落
        return <p key={i}>{renderInlineMarkdown(line)}</p>
      })}
    </div>
  )
}

// 渲染行内Markdown（加粗、emoji等）
function renderInlineMarkdown(text: string): React.ReactNode {
  // 处理 **加粗**
  const parts = text.split(/(\*\*[^*]+\*\*)/g)

  return parts.map((part, j) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={j} className="font-semibold">{part.slice(2, -2)}</strong>
    }
    return part
  })
}

function MobileLayout({
  images,
  title,
  content,
  author,
  avatar,
  likes,
  comments,
  collects,
  date,
}: {
  images: string[]
  title?: string
  content: string
  author: string
  avatar?: string
  likes: number
  comments: number
  collects: number
  date?: string
}) {
  const parsed = parseContent(content)
  const displayTitle = title || parsed.title
  const displayContent = parsed.cleanContent

  return (
    <div className="w-full">
      <ImageCarousel
        images={images}
        aspectRatio="3/4"
        showArrows={false}
        showDots={true}
      />
      <div className="p-4">
        <div className="flex items-center gap-3 mb-3">
          {avatar ? (
            <img src={avatar} alt={author} className="w-10 h-10 rounded-full object-cover" />
          ) : (
            <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
              <span className="text-gray-500 text-sm">{author.charAt(0)}</span>
            </div>
          )}
          <div>
            <p className="font-medium text-gray-900 text-sm">{author}</p>
            {date && <p className="text-gray-400 text-xs">{date}</p>}
          </div>
        </div>
        {displayTitle && (
          <h3 className="font-semibold text-gray-900 mb-2 text-base leading-snug">{displayTitle}</h3>
        )}
        <RenderMarkdown content={displayContent} />
        <div className="flex items-center gap-6 mt-4 pt-3 border-t border-gray-100">
          <div className="flex items-center gap-1.5 text-gray-500">
            <Heart size={16} />
            <span className="text-xs">{likes}</span>
          </div>
          <div className="flex items-center gap-1.5 text-gray-500">
            <MessageCircle size={16} />
            <span className="text-xs">{comments}</span>
          </div>
          <div className="flex items-center gap-1.5 text-gray-500">
            <Star size={16} />
            <span className="text-xs">{collects}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function PCLayout({
  images,
  title,
  content,
  author,
  avatar,
  likes,
  comments,
  collects,
  date,
}: {
  images: string[]
  title?: string
  content: string
  author: string
  avatar?: string
  likes: number
  comments: number
  collects: number
  date?: string
}) {
  const parsed = parseContent(content)
  const displayTitle = title || parsed.title
  const displayContent = parsed.cleanContent

  return (
    <div className="flex w-full">
      {/* 左侧图片区域 - 50% 宽度 */}
      <div className="w-1/2">
        <ImageCarousel
          images={images}
          aspectRatio="3/4"
          showArrows={true}
          showDots={true}
        />
      </div>

      {/* 右侧文字区域 - 50% 宽度 */}
      <div className="w-1/2 p-5 flex flex-col bg-white">
        {/* 作者信息 */}
        <div className="flex items-center gap-3 mb-4">
          {avatar ? (
            <img src={avatar} alt={author} className="w-10 h-10 rounded-full object-cover" />
          ) : (
            <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
              <span className="text-gray-500 text-sm">{author.charAt(0)}</span>
            </div>
          )}
          <div>
            <p className="font-medium text-gray-900 text-sm">{author}</p>
            {date && <p className="text-gray-400 text-xs">{date}</p>}
          </div>
        </div>

        {/* 标题 */}
        {displayTitle && (
          <h3 className="font-semibold text-gray-900 mb-3 text-base leading-snug">
            {displayTitle}
          </h3>
        )}

        {/* 正文内容 */}
        <div className="flex-1 overflow-auto">
          <RenderMarkdown content={displayContent} />
        </div>

        {/* 互动数据 */}
        <div className="flex items-center gap-6 mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-center gap-1.5 text-gray-500">
            <Heart size={16} />
            <span className="text-xs">{likes}</span>
          </div>
          <div className="flex items-center gap-1.5 text-gray-500">
            <MessageCircle size={16} />
            <span className="text-xs">{comments}</span>
          </div>
          <div className="flex items-center gap-1.5 text-gray-500">
            <Star size={16} />
            <span className="text-xs">{collects}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export function XhsPreview({
  images,
  title,
  content,
  author = "小红书博主",
  avatar,
  likes = 0,
  comments = 0,
  collects = 0,
  date,
  forceMobile = false,
}: XhsPreviewProps) {
  const isMobile = forceMobile || (typeof window !== "undefined" && window.innerWidth < 768)

  return (
    <div className="w-full max-w-2xl mx-auto bg-white rounded-xl overflow-hidden border border-gray-200 shadow-sm">
      {isMobile ? (
        <MobileLayout
          images={images}
          title={title}
          content={content}
          author={author}
          avatar={avatar}
          likes={likes}
          comments={comments}
          collects={collects}
          date={date}
        />
      ) : (
        <PCLayout
          images={images}
          title={title}
          content={content}
          author={author}
          avatar={avatar}
          likes={likes}
          comments={comments}
          collects={collects}
          date={date}
        />
      )}
    </div>
  )
}
