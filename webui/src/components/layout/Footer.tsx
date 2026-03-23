import { Link } from "react-router-dom"

export function Footer() {
  return (
    <footer className="border-t border-[var(--color-border)] bg-[var(--color-surface)] mt-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-14">
        <p className="text-center text-lg font-medium text-[var(--color-text-secondary)] mb-10">
          少一点套路，多一点智能。
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-10 text-sm">
          <div>
            <h3 className="font-semibold text-[var(--color-text)] mb-3">产品</h3>
            <ul className="space-y-2.5 text-[var(--color-text-secondary)]">
              <li><Link to="/" className="hover:text-[var(--color-text)] transition-colors">首页</Link></li>
              <li><Link to="/account" className="hover:text-[var(--color-text)] transition-colors">用户信息</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-[var(--color-text)] mb-3">资源</h3>
            <ul className="space-y-2.5 text-[var(--color-text-secondary)]">
              <li><a href="#" className="hover:text-[var(--color-text)] transition-colors">帮助</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-[var(--color-text)] mb-3">公司</h3>
            <ul className="space-y-2.5 text-[var(--color-text-secondary)]">
              <li><a href="#" className="hover:text-[var(--color-text)] transition-colors">关于</a></li>
              <li><a href="#" className="hover:text-[var(--color-text)] transition-colors">隐私</a></li>
            </ul>
          </div>
        </div>
        <p className="mt-10 text-center text-[var(--color-text-muted)] text-sm">
          © {new Date().getFullYear()} 小红书助手
        </p>
      </div>
    </footer>
  )
}
