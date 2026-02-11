import { Link, useNavigate } from "react-router-dom"
import { useState } from "react"
import { useAuth } from "../../contexts/AuthContext"
import { postLogout } from "../../api/client"

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false)
  const { isLoggedIn, username, token, clearAuth } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    if (token) {
      try {
        await postLogout(token)
      } catch {
        // 忽略网络错误，本地仍清除
      }
      clearAuth()
      setMenuOpen(false)
      navigate("/")
    }
  }

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-neutral-100">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
        <Link to="/" className="font-semibold text-lg text-neutral-900">
          小红书助手
        </Link>

        {/* Desktop nav */}
        <nav className="hidden sm:flex items-center gap-6 text-sm">
          <Link
            to="/"
            className="text-neutral-600 hover:text-neutral-900 hover:underline underline-offset-4"
          >
            首页
          </Link>
          <Link
            to="/account"
            className="text-neutral-600 hover:text-neutral-900 hover:underline underline-offset-4"
          >
            用户信息
          </Link>
          {isLoggedIn ? (
            <>
              <span className="text-neutral-700">{username}</span>
              <button
                type="button"
                onClick={handleLogout}
                className="text-neutral-600 hover:text-neutral-900 hover:underline underline-offset-4"
              >
                登出
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-neutral-600 hover:text-neutral-900 hover:underline underline-offset-4"
              >
                登录
              </Link>
              <Link
                to="/register"
                className="text-neutral-600 hover:text-neutral-900 hover:underline underline-offset-4"
              >
                注册
              </Link>
            </>
          )}
        </nav>

        {/* Mobile menu button */}
        <button
          type="button"
          className="sm:hidden p-2 rounded-md text-neutral-600 hover:bg-neutral-100"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="菜单"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {menuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile nav dropdown */}
      {menuOpen && (
        <div className="sm:hidden border-t border-neutral-100 bg-white px-4 py-3 flex flex-col gap-2">
          <Link
            to="/"
            onClick={() => setMenuOpen(false)}
            className="text-neutral-600 hover:text-neutral-900 hover:underline underline-offset-4"
          >
            首页
          </Link>
          <Link
            to="/account"
            onClick={() => setMenuOpen(false)}
            className="text-neutral-600 hover:text-neutral-900 hover:underline underline-offset-4"
          >
            用户信息
          </Link>
          {isLoggedIn ? (
            <>
              <span className="text-neutral-700">{username}</span>
              <button
                type="button"
                onClick={handleLogout}
                className="text-left text-neutral-600 hover:text-neutral-900 hover:underline underline-offset-4"
              >
                登出
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                onClick={() => setMenuOpen(false)}
                className="text-neutral-600 hover:text-neutral-900 hover:underline underline-offset-4"
              >
                登录
              </Link>
              <Link
                to="/register"
                onClick={() => setMenuOpen(false)}
                className="text-neutral-600 hover:text-neutral-900 hover:underline underline-offset-4"
              >
                注册
              </Link>
            </>
          )}
        </div>
      )}
    </header>
  )
}
