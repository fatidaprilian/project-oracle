import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { AppRole } from '../auth/session'

interface LayoutProps {
  children: React.ReactNode
  username: string
  role: AppRole
  isAuthenticated: boolean
  onLogout?: () => void
}

export default function Layout({
  children,
  username,
  role,
  isAuthenticated,
  onLogout,
}: LayoutProps) {
  const location = useLocation()
  const roleLabel = role.charAt(0).toUpperCase() + role.slice(1)
  
  const isActive = (path: string) => location.pathname === path
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">PO</span>
              </div>
              <h1 className="text-2xl font-bold text-white">Oracle</h1>
              <span className="text-xs px-2 py-1 rounded border border-slate-700 text-slate-300 bg-slate-800/80">
                role: {roleLabel}
              </span>
            </div>
            <nav className="flex items-center gap-1">
              <Link
                to="/"
                className={`px-4 py-2 rounded-lg transition-colors ${
                  isActive('/') 
                    ? 'bg-blue-600 text-white' 
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                Dashboard
              </Link>
              <Link
                to="/requests"
                className={`px-4 py-2 rounded-lg transition-colors ${
                  isActive('/requests') 
                    ? 'bg-blue-600 text-white' 
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                Requests
              </Link>
              {isAuthenticated ? (
                <>
                  <span className="ml-2 text-xs text-slate-400">{username}</span>
                  <button
                    type="button"
                    className="ml-2 px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-800"
                    onClick={onLogout}
                  >
                    Logout
                  </button>
                </>
              ) : (
                <Link
                  to="/login"
                  className={`ml-2 px-3 py-2 rounded-lg transition-colors ${
                    isActive('/login')
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  Login
                </Link>
              )}
            </nav>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-6 py-8">
        {children}
      </main>
    </div>
  )
}
