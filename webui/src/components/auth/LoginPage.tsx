import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { postLogin } from "../../api/client"
import { useAuth } from "../../contexts/AuthContext"
import { AuthIllustration } from "../ui/Illustrations"

export function LoginPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuth()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      const res = await postLogin(username.trim(), password)
      setAuth(res.token, res.username)
      navigate("/", { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto px-4 py-12">
      <AuthIllustration />
      <h1 className="text-2xl font-semibold text-neutral-900 mb-6">登录</h1>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1.5">
            用户名
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoComplete="username"
            className="w-full px-3 py-2.5 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-white text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus-ring-accent focus:outline-none transition-shadow"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1.5">
            密码
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            className="w-full px-3 py-2.5 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-white text-[var(--color-text)] focus-ring-accent focus:outline-none transition-shadow"
          />
        </div>
        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="btn-accent w-full py-3 rounded-[var(--radius-lg)] font-medium disabled:opacity-50"
        >
          {loading ? "登录中…" : "登录"}
        </button>
      </form>
      <p className="mt-6 text-sm text-[var(--color-text-secondary)] text-center">
        还没有账号？{" "}
        <Link to="/register" className="text-[var(--color-accent)] font-medium hover:underline underline-offset-2">
          注册
        </Link>
      </p>
    </div>
  )
}
