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
        {title && <h3 className="font-semibold text-gray-900 mb-2 text-base leading-snug">{title}</h3>}
        <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
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
        {title && (
          <h3 className="font-semibold text-gray-900 mb-3 text-base leading-snug">
            {title}
          </h3>
        )}

        {/* 正文内容 */}
        <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap flex-1 overflow-auto">
          {content}
        </p>

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
