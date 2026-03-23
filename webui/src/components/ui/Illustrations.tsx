/**
 * 内联 SVG 插画与图标，统一风格：简洁、中性色 + 珊瑚红点缀，适配 Manus 风格界面。
 */

const coral = "#e85d5d"
const coralLight = "#f5c6c6"
const neutral = "#737373"
const neutralLight = "#a3a3a3"

export function HeroIllustration() {
  return (
    <svg
      width="160"
      height="120"
      viewBox="0 0 160 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="mx-auto block"
      aria-hidden
    >
      {/* 主圆形背景 */}
      <circle cx="80" cy="58" r="44" fill="#fafafa" stroke="#e5e5e5" strokeWidth="1.5" />
      {/* 文档/笔记轮廓 */}
      <path
        d="M52 42h56v36H52V42z"
        fill="white"
        stroke={neutralLight}
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      <path d="M60 52h40M60 60h32M60 68h24" stroke={neutral} strokeWidth="1" strokeLinecap="round" />
      {/* 灯泡/想法 */}
      <circle cx="108" cy="38" r="14" fill={coralLight} stroke={coral} strokeWidth="1.2" />
      <path
        d="M108 30v4M108 46v2M102 38h4M114 38h4M105 33l2 2M111 33l-2 2M105 43l2-2M111 43l-2-2"
        stroke={coral}
        strokeWidth="1"
        strokeLinecap="round"
      />
      {/* 小装饰点 */}
      <circle cx="72" cy="78" r="3" fill={coralLight} />
      <circle cx="88" cy="82" r="2" fill={neutralLight} opacity="0.8" />
    </svg>
  )
}

export function IconStrategy() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <circle cx="24" cy="24" r="20" fill="#fafafa" stroke="#e5e5e5" strokeWidth="1.2" />
      <circle cx="24" cy="24" r="8" stroke={coral} strokeWidth="1.5" fill="none" />
      <path d="M24 16v16M16 24h16" stroke={neutral} strokeWidth="1" strokeLinecap="round" />
      <circle cx="24" cy="12" r="2" fill={coral} />
      <circle cx="24" cy="36" r="2" fill={neutralLight} />
      <circle cx="12" cy="24" r="2" fill={neutralLight} />
      <circle cx="36" cy="24" r="2" fill={neutralLight} />
    </svg>
  )
}

export function IconTopic() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <circle cx="24" cy="24" r="20" fill="#fafafa" stroke="#e5e5e5" strokeWidth="1.2" />
      <path
        d="M16 30L22 24L28 28L34 20"
        stroke={coral}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M18 26l4-4 6 4 4-6" stroke={neutral} strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" opacity="0.8" />
    </svg>
  )
}

export function IconContent() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <circle cx="24" cy="24" r="20" fill="#fafafa" stroke="#e5e5e5" strokeWidth="1.2" />
      <rect x="16" y="14" width="16" height="20" rx="1" fill="white" stroke={neutralLight} strokeWidth="1" />
      <path d="M20 20h8M20 24h8M20 28h5" stroke={neutral} strokeWidth="1" strokeLinecap="round" />
      <path d="M28 18v-2l2 2-2 2v-2z" fill={coral} opacity="0.9" />
    </svg>
  )
}

export function IconEval() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <circle cx="24" cy="24" r="20" fill="#fafafa" stroke="#e5e5e5" strokeWidth="1.2" />
      <path d="M18 28l4-6 4 4 6-8" stroke={coral} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="18" cy="28" r="1.5" fill={coral} />
      <circle cx="22" cy="22" r="1.5" fill={coral} />
      <circle cx="26" cy="26" r="1.5" fill={coral} />
      <circle cx="32" cy="20" r="1.5" fill={coral} />
    </svg>
  )
}

export function IconAds() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <circle cx="24" cy="24" r="20" fill="#fafafa" stroke="#e5e5e5" strokeWidth="1.2" />
      <rect x="14" y="18" width="20" height="12" rx="1" fill="white" stroke={neutralLight} strokeWidth="1" />
      <path d="M18 22h8M18 25h6" stroke={neutral} strokeWidth="0.8" strokeLinecap="round" />
      <path d="M30 22v6l4-3-4-3z" fill={coral} opacity="0.9" />
    </svg>
  )
}

export function IconFullChain() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <circle cx="24" cy="24" r="20" fill="#fafafa" stroke="#e5e5e5" strokeWidth="1.2" />
      <circle cx="16" cy="20" r="4" stroke={coral} strokeWidth="1.2" fill="none" />
      <circle cx="24" cy="28" r="4" stroke={neutral} strokeWidth="1" fill="none" />
      <circle cx="32" cy="20" r="4" stroke={neutral} strokeWidth="1" fill="none" />
      <path d="M20 20l4 6 8-6" stroke={coralLight} strokeWidth="1" strokeDasharray="2 2" strokeLinecap="round" />
    </svg>
  )
}

const CARD_ICONS: Record<string, React.FC> = {
  账号战略: IconStrategy,
  选题策划: IconTopic,
  内容生成: IconContent,
  内容评估与检验: IconEval,
  投流: IconAds,
}

export function getCardIcon(agent?: string): React.FC | null {
  if (!agent) return null
  return CARD_ICONS[agent] ?? IconFullChain
}

/** 登录/注册页顶部小插画 */
export function AuthIllustration() {
  return (
    <svg
      width="80"
      height="56"
      viewBox="0 0 80 56"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="mx-auto mb-4 block text-neutral-300"
      aria-hidden
    >
      <circle cx="40" cy="22" r="12" fill="#fafafa" stroke="currentColor" strokeWidth="1.2" />
      <path
        d="M28 52c0-6.6 5.4-12 12-12s12 5.4 12 12"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
      <rect x="52" y="18" width="20" height="14" rx="2" fill="#fafafa" stroke="currentColor" strokeWidth="1" />
      <path d="M58 24h8M58 28h5" stroke="currentColor" strokeWidth="0.8" strokeLinecap="round" opacity="0.7" />
    </svg>
  )
}
