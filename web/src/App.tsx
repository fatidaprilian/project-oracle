import { useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { api, setApiAuthToken } from './api/client'
import { AuthSession, clearAuthSession, loadAuthSession, saveAuthSession } from './auth/session'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Requests from './pages/Requests'
import Login from './pages/Login'
import './App.css'

function App() {
  const [session, setSession] = useState<AuthSession | null>(() => loadAuthSession())
  const [authLoading, setAuthLoading] = useState(false)

  const role = session?.role ?? 'viewer'
  const username = session?.username ?? 'guest'
  const isAuthenticated = session !== null

  useEffect(() => {
    setApiAuthToken(session?.token || null)
  }, [session])

  const handleLogin = async (username: string, password: string) => {
    setAuthLoading(true)
    try {
      const { data } = await api.login(username, password)
      const nextSession: AuthSession = {
        token: data.access_token,
        username: data.username,
        role: data.role,
      }
      saveAuthSession(nextSession)
      setSession(nextSession)
    } catch (error) {
      const detail =
        typeof error === 'object' &&
        error !== null &&
        'response' in error &&
        typeof (error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail === 'string'
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : 'Invalid username or password'
      throw new Error(detail)
    } finally {
      setAuthLoading(false)
    }
  }

  const handleLogout = () => {
    clearAuthSession()
    setSession(null)
    setApiAuthToken(null)
  }

  return (
    <Router>
      <Layout
        username={username}
        role={role}
        isAuthenticated={isAuthenticated}
        onLogout={isAuthenticated ? handleLogout : undefined}
      >
        <Routes>
          <Route path="/" element={<Dashboard role={role} />} />
          <Route path="/requests" element={<Requests role={role} />} />
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to="/" replace />
              ) : (
                <Login onSubmit={handleLogin} loading={authLoading} />
              )
            }
          />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
