import { Link } from "react-router-dom"

export function Footer() {
  return (
    <footer className="border-t border-neutral-200 bg-neutral-50 mt-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
        <p className="text-center text-lg font-medium text-neutral-700 mb-8">
          少一点套路，多一点智能。
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 text-sm">
          <div>
            <h3 className="font-semibold text-neutral-900 mb-3">产品</h3>
            <ul className="space-y-2 text-neutral-600">
              <li><Link to="/" className="hover:text-neutral-900 hover:underline">首页</Link></li>
              <li><Link to="/account" className="hover:text-neutral-900 hover:underline">用户信息</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-neutral-900 mb-3">资源</h3>
            <ul className="space-y-2 text-neutral-600">
              <li><a href="#" className="hover:text-neutral-900 hover:underline">帮助</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-neutral-900 mb-3">公司</h3>
            <ul className="space-y-2 text-neutral-600">
              <li><a href="#" className="hover:text-neutral-900 hover:underline">关于</a></li>
              <li><a href="#" className="hover:text-neutral-900 hover:underline">隐私</a></li>
            </ul>
          </div>
        </div>
        <p className="mt-8 text-center text-neutral-500 text-sm">
          © {new Date().getFullYear()} 小红书助手
        </p>
      </div>
    </footer>
  )
}
