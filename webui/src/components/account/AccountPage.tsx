import { useState, useEffect } from "react"
import { getAccountContext, setAccountContext } from "../../stores/accountContext"
import type { AccountContext } from "../../types/intent"

const STAGE_OPTIONS = [
  { value: "", label: "请选择" },
  { value: "起号", label: "起号" },
  { value: "冷启动", label: "冷启动" },
  { value: "放量", label: "放量" },
  { value: "变现", label: "变现" },
]

const GOAL_OPTIONS = [
  { value: "", label: "请选择" },
  { value: "涨粉", label: "涨粉" },
  { value: "种草", label: "种草" },
  { value: "变现", label: "变现" },
]

export function AccountPage() {
  const [persona, setPersona] = useState("")
  const [accountStage, setAccountStage] = useState("")
  const [industry, setIndustry] = useState("")
  const [goal, setGoal] = useState("")
  const [contentSummary, setContentSummary] = useState("")
  const [recentTags, setRecentTags] = useState("")
  const [adsQualified, setAdsQualified] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const ctx = getAccountContext()
    setPersona((ctx.persona as string) ?? "")
    setAccountStage((ctx.account_stage as string) ?? "")
    setIndustry((ctx.industry as string) ?? "")
    setGoal((ctx.goal as string) ?? "")
    setContentSummary((ctx.content_summary as string) ?? "")
    setRecentTags(
      Array.isArray(ctx.recent_tags)
        ? (ctx.recent_tags as string[]).join("、")
        : (ctx.recent_tags as string) ?? ""
    )
    setAdsQualified((ctx.ads_qualified as boolean) ?? false)
  }, [])

  const handleSave = () => {
    const tags = recentTags
      .split(/[、,，\s]+/)
      .map((s) => s.trim())
      .filter(Boolean)
    const ctx: AccountContext = {
      persona: persona || undefined,
      account_stage: accountStage || undefined,
      industry: industry || undefined,
      goal: goal || undefined,
      content_summary: contentSummary || undefined,
      recent_tags: tags.length ? tags : undefined,
      ads_qualified: adsQualified,
    }
    setAccountContext(ctx)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold text-neutral-900 mb-6">用户信息管理</h1>

      <div className="space-y-8">
        <section className="rounded-xl border border-neutral-200 bg-white p-6">
          <h2 className="text-lg font-medium text-neutral-900 mb-4">基础信息</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-neutral-600 mb-1">行业</label>
              <input
                type="text"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="如：美妆、母婴、装修"
                className="w-full px-3 py-2 rounded-lg border border-neutral-200 text-neutral-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-600 mb-1">账号目标</label>
              <select
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-neutral-200 text-neutral-900"
              >
                {GOAL_OPTIONS.map((o) => (
                  <option key={o.value || "empty"} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-neutral-200 bg-white p-6">
          <h2 className="text-lg font-medium text-neutral-900 mb-4">人设与阶段</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-neutral-600 mb-1">人设（3 句话内）</label>
              <textarea
                value={persona}
                onChange={(e) => setPersona(e.target.value)}
                placeholder="用 3 句话描述账号人设与表达风格"
                rows={3}
                className="w-full px-3 py-2 rounded-lg border border-neutral-200 text-neutral-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-600 mb-1">账号阶段</label>
              <select
                value={accountStage}
                onChange={(e) => setAccountStage(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-neutral-200 text-neutral-900"
              >
                {STAGE_OPTIONS.map((o) => (
                  <option key={o.value || "empty"} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-neutral-200 bg-white p-6">
          <h2 className="text-lg font-medium text-neutral-900 mb-4">内容与标签</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-neutral-600 mb-1">近期内容摘要</label>
              <textarea
                value={contentSummary}
                onChange={(e) => setContentSummary(e.target.value)}
                placeholder="最近笔记主题或摘要"
                rows={2}
                className="w-full px-3 py-2 rounded-lg border border-neutral-200 text-neutral-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-600 mb-1">常用标签</label>
              <input
                type="text"
                value={recentTags}
                onChange={(e) => setRecentTags(e.target.value)}
                placeholder="用顿号或逗号分隔，如：好物分享、测评"
                className="w-full px-3 py-2 rounded-lg border border-neutral-200 text-neutral-900"
              />
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-neutral-200 bg-white p-6">
          <h2 className="text-lg font-medium text-neutral-900 mb-4">投流与资质</h2>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="ads_qualified"
              checked={adsQualified}
              onChange={(e) => setAdsQualified(e.target.checked)}
              className="w-4 h-4 rounded border-neutral-300"
            />
            <label htmlFor="ads_qualified" className="text-sm text-neutral-700">
              已具备小红书官方投流资质（报白/开户）
            </label>
          </div>
        </section>

        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={handleSave}
            className="px-6 py-2.5 rounded-xl bg-neutral-900 text-white font-medium hover:bg-neutral-800"
          >
            保存
          </button>
          {saved && (
            <span className="text-sm text-green-600">已保存到本地</span>
          )}
        </div>
      </div>
    </div>
  )
}
