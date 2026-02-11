import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { postLogin } from "../../api/client"
import { useAuth } from "../../contexts/AuthContext"

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
      <h1 className="text-2xl font-semibold text-neutral-900 mb-6">登录</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-neutral-600 mb-1">
            用户名
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoComplete="username"
            className="w-full px-3 py-2 rounded-lg border border-neutral-200 text-neutral-900"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-neutral-600 mb-1">
            密码
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            className="w-full px-3 py-2 rounded-lg border border-neutral-200 text-neutral-900"
          />
        </div>
        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 rounded-xl bg-neutral-900 text-white font-medium hover:bg-neutral-800 disabled:opacity-50"
        >
          {loading ? "登录中…" : "登录"}
        </button>
      </form>
      <p className="mt-4 text-sm text-neutral-600 text-center">
        还没有账号？{" "}
        <Link to="/register" className="text-neutral-900 font-medium hover:underline">
          注册
        </Link>
      </p>
    </div>
  )
}
