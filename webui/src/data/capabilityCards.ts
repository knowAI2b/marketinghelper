export interface CapabilityCard {
  id: string
  title: string
  description: string
  /** Preset user_input sent when card is clicked */
  userInput: string
  agent?: string
}

export const CAPABILITY_CARDS: CapabilityCard[] = [
  {
    id: "account-strategy",
    title: "起号与定位",
    description: "基于行业与目标确定账号人设与阶段策略。",
    userInput: "帮我起个账号，确定人设和账号阶段策略",
    agent: "账号战略",
  },
  {
    id: "topic-planning",
    title: "热门选题",
    description: "捕捉行业热点并产出选题与执行建议。",
    userInput: "根据当前行业流行的小红书内容，帮我做选题策划",
    agent: "选题策划",
  },
  {
    id: "content-generation",
    title: "生成图文笔记",
    description: "按人设与结构生成正文与配图规划。",
    userInput: "帮我生成一篇小红书图文笔记，要符合账号人设",
    agent: "内容生成",
  },
  {
    id: "burst-title",
    title: "爆款标题",
    description: "为笔记生成多组标题用于 A/B 测试。",
    userInput: "给上一篇笔记生成 3 个爆款标题，我要 A/B 测试",
    agent: "选题策划",
  },
  {
    id: "content-eval",
    title: "内容质量评估",
    description: "质量、人设一致性、合规与发布前建议。",
    userInput: "帮我评估一下这篇内容的质量和合规性",
    agent: "内容评估与检验",
  },
  {
    id: "ads-candidate",
    title: "投流候选筛选",
    description: "筛选笔记并评估投流性价比。",
    userInput: "从已发布笔记里选几条适合投流的，并评估投流价值",
    agent: "投流",
  },
  {
    id: "full-chain",
    title: "选题到发布全链路",
    description: "从流行选题到特色图文再到评估，一站式完成。",
    userInput: "根据行业流行的小红书文章生成选题，再生成带我们品牌特色的图文内容，评估后我要发布到小红书",
    agent: "选题策划",
  },
  {
    id: "mixed-intent",
    title: "起号 + 种草 + 节奏",
    description: "起美妆/母婴等账号，先做种草，设定更新节奏。",
    userInput: "帮我起个美妆账号，先做种草，一周 3 更",
    agent: "账号战略",
  },
]
