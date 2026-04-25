import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './auth/useAuth'
import ProtectedRoute from './auth/ProtectedRoute'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Sources from './pages/Sources'
import Search from './pages/Search'
import Chat from './pages/Chat'
import Settings from './pages/Settings'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="/sources" element={<Sources />} />
            <Route path="/search" element={<Search />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </StrictMode>,
)
