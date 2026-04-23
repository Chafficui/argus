import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './auth/useAuth'
import ProtectedRoute from './auth/ProtectedRoute'
import Layout from './components/Layout'
import Sources from './pages/Sources'
import Search from './pages/Search'
import Chat from './pages/Chat'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <ProtectedRoute>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Sources />} />
              <Route path="/search" element={<Search />} />
              <Route path="/chat" element={<Chat />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ProtectedRoute>
    </AuthProvider>
  </StrictMode>,
)
