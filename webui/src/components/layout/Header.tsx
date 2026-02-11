import { Link, useNavigate } from "react-router-dom"
import { useState } from "react"
import { useAuth } from "../../contexts/AuthContext"
import { postLogout } from "../../api/client"
import { LogoMark } from "../ui/LogoMark"

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
    <header className="sticky top-0 z-50 bg-white/98 backdrop-blur-sm border-b border-[var(--color-border)]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
        <Link
          to="/"
          className="flex items-center gap-2.5 font-semibold text-lg text-[var(--color-text)] transition-opacity hover:opacity-90"
        >
          <LogoMark />
          小红书助手
        </Link>

        {/* Desktop nav */}
        <nav className="hidden sm:flex items-center gap-8 text-sm">
          <Link
            to="/"
            className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors duration-200 underline-offset-4 hover:underline"
          >
            首页
          </Link>
          <Link
            to="/account"
            className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors duration-200 underline-offset-4 hover:underline"
          >
            用户信息
          </Link>
          {isLoggedIn ? (
            <>
              <span className="text-[var(--color-text-secondary)] font-medium">{username}</span>
              <button
                type="button"
                onClick={handleLogout}
                className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors duration-200 underline-offset-4 hover:underline"
              >
                登出
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors duration-200 underline-offset-4 hover:underline"
              >
                登录
              </Link>
              <Link
                to="/register"
                className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors duration-200 underline-offset-4 hover:underline"
              >
                注册
              </Link>
            </>
          )}
        </nav>

        {/* Mobile menu button */}
        <button
          type="button"
          className="sm:hidden p-2 rounded-[var(--radius-md)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface)] transition-colors"
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
        <div className="sm:hidden border-t border-[var(--color-border)] bg-white px-4 py-3 flex flex-col gap-1">
          <Link
            to="/"
            onClick={() => setMenuOpen(false)}
            className="py-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors"
          >
            首页
          </Link>
          <Link
            to="/account"
            onClick={() => setMenuOpen(false)}
            className="py-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors"
          >
            用户信息
          </Link>
          {isLoggedIn ? (
            <>
              <span className="py-2 text-[var(--color-text-secondary)] font-medium">{username}</span>
              <button
                type="button"
                onClick={handleLogout}
                className="text-left py-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors"
              >
                登出
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                onClick={() => setMenuOpen(false)}
                className="py-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors"
              >
                登录
              </Link>
              <Link
                to="/register"
                onClick={() => setMenuOpen(false)}
                className="py-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors"
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
