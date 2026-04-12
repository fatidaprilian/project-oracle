import { Component, ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  message: string
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    hasError: false,
    message: '',
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      message: error.message || 'Unexpected application error',
    }
  }

  componentDidCatch(error: Error): void {
    console.error('Unhandled UI error:', error)
  }

  private reloadPage(): void {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
          <div className="max-w-xl w-full bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h1 className="text-xl font-semibold text-red-300">Dashboard crashed</h1>
            <p className="text-slate-300">
              A runtime error happened in the UI. You can reload the page and continue.
            </p>
            <pre className="text-xs bg-slate-950 border border-slate-800 rounded p-3 text-slate-400 overflow-x-auto">
              {this.state.message}
            </pre>
            <button
              type="button"
              className="btn-primary"
              onClick={() => this.reloadPage()}
            >
              Reload Dashboard
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}