import { BrowserRouter, Routes, Route } from "react-router-dom"
import { Header, Footer } from "./components/layout"
import { HomePage } from "./components/home"
import { SessionPage } from "./components/session"
import { AccountPage } from "./components/account"

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-white">
        <Header />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/session" element={<SessionPage />} />
            <Route path="/account" element={<AccountPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  )
}

export default App
