import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom"
import { AuthProvider } from "./contexts/AuthContext"
import { Header, Footer } from "./components/layout"
import { HomePage } from "./components/home"
import { SessionPage } from "./components/session"
import { AccountPage } from "./components/account"
import { LoginPage, RegisterPage } from "./components/auth"

function AppContent() {
  const location = useLocation()
  // 在会话页面隐藏 Footer
  const showFooter = location.pathname !== "/session"

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/session" element={<SessionPage />} />
          <Route path="/account" element={<AccountPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </main>
      {showFooter && <Footer />}
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
