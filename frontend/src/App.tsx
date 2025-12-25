import { useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ReactFlowProvider } from '@xyflow/react'
import { settingsApi, authApi } from '@/lib/api'
import { useSettingsStore } from '@/stores/settingsStore'
import { useAuthStore } from '@/stores/authStore'
import { Layout } from '@/components/layout/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { Settings } from '@/pages/Settings'
import { Editor } from '@/pages/Editor'
import { Login } from '@/pages/Login'
import { Profile } from '@/pages/Profile'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Loader2 } from 'lucide-react'

function EditorWrapper() {
  return (
    <ReactFlowProvider>
      <Editor />
    </ReactFlowProvider>
  )
}

/**
 * Protected Route wrapper - redirects to login if not authenticated
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, token } = useAuthStore()
  const location = useLocation()

  // Verify token is still valid
  const { isLoading, isError } = useQuery({
    queryKey: ['verifyToken'],
    queryFn: authApi.verify,
    enabled: !!token,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // If token verification fails, redirect to login
  if (isError) {
    useAuthStore.getState().logout()
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Show loading while verifying
  if (isLoading && token) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}

export default function App() {
  const setSettings = useSettingsStore((state) => state.setSettings)
  const setLoading = useSettingsStore((state) => state.setLoading)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  // Only fetch settings if authenticated
  const { data, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.get,
    enabled: isAuthenticated,
  })

  useEffect(() => {
    if (data) {
      setSettings(data)
    }
    setLoading(isLoading)
  }, [data, isLoading, setSettings, setLoading])

  return (
    <TooltipProvider>
      <Routes>
        {/* Public route - Login */}
        <Route path="/login" element={<Login />} />

        {/* Protected routes */}
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/editor/:id" element={<EditorWrapper />} />
        </Route>

        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </TooltipProvider>
  )
}
