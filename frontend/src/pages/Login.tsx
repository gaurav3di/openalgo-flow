/**
 * Login Page
 * Handles both initial setup (password creation) and login
 * First-time users are routed to Settings, returning users to Dashboard
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Loader2, Lock, Shield, Eye, EyeOff, Workflow, Zap, LineChart, Bot, User } from 'lucide-react'
import { authApi } from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PasswordStrength, validatePassword, getPasswordScore } from '@/components/ui/password-strength'
import { useToast } from '@/hooks/use-toast'

const FEATURES = [
  {
    icon: Workflow,
    title: 'Visual Workflow Builder',
    description: 'Design trading strategies with drag-and-drop nodes',
  },
  {
    icon: Zap,
    title: 'Automated Execution',
    description: 'Execute trades automatically based on your rules',
  },
  {
    icon: LineChart,
    title: 'Options Strategies',
    description: 'Built-in support for complex options strategies',
  },
  {
    icon: Bot,
    title: 'Smart Orders',
    description: 'Position sizing and intelligent order management',
  },
]

export function Login() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const { setToken, setSetupComplete, setUsername, isAuthenticated } = useAuthStore()

  const [username, setUsernameInput] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  // Check if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/')
    }
  }, [isAuthenticated, navigate])

  // Check auth status
  const { data: authStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['authStatus'],
    queryFn: authApi.getStatus,
  })

  const isSetupMode = authStatus && !authStatus.is_setup_complete

  // Setup mutation (for first-time account creation)
  const setupMutation = useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      authApi.setup(username, password),
    onSuccess: (data) => {
      setToken(data.access_token)
      setSetupComplete(true)
      setUsername(username)
      toast({
        title: 'Welcome to OpenAlgo Flow!',
        description: 'Your account has been created. Let\'s configure your settings.',
        variant: 'success',
      })
      // First-time user goes to settings to configure OpenAlgo connection
      navigate('/settings')
    },
    onError: (error: Error) => {
      toast({
        title: 'Setup failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      authApi.login(username, password),
    onSuccess: (data) => {
      setToken(data.access_token)
      setUsername(username)
      toast({
        title: 'Welcome back!',
        description: 'Login successful.',
        variant: 'success',
      })
      // Returning user goes to dashboard
      navigate('/')
    },
    onError: (error: Error) => {
      toast({
        title: 'Login failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (isSetupMode) {
      if (username.length < 3) {
        toast({
          title: 'Username too short',
          description: 'Username must be at least 3 characters.',
          variant: 'destructive',
        })
        return
      }

      if (password !== confirmPassword) {
        toast({
          title: 'Passwords do not match',
          description: 'Please make sure both passwords are the same.',
          variant: 'destructive',
        })
        return
      }

      // Validate password against all rules
      const validation = validatePassword(password)
      if (!validation.isValid) {
        toast({
          title: 'Password does not meet requirements',
          description: `Missing: ${validation.errors.slice(0, 2).join(', ')}${validation.errors.length > 2 ? '...' : ''}`,
          variant: 'destructive',
        })
        return
      }

      setupMutation.mutate({ username, password })
    } else {
      if (!username || !password) {
        toast({
          title: 'Missing credentials',
          description: 'Please enter both username and password.',
          variant: 'destructive',
        })
        return
      }
      loginMutation.mutate({ username, password })
    }
  }

  // Check if form is valid for submit button
  const isFormValid = isSetupMode
    ? username.length >= 3 && getPasswordScore(password) >= 5 && password === confirmPassword
    : username.length > 0 && password.length > 0

  const isSubmitting = setupMutation.isPending || loginMutation.isPending

  if (statusLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-background">
      {/* Left side - Branding and features */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between bg-card p-12 relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 mesh-gradient opacity-30" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
              <Workflow className="h-7 w-7 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">OpenAlgo Flow</h1>
              <p className="text-muted-foreground text-sm">Visual Trading Automation</p>
            </div>
          </div>
        </div>

        <div className="relative z-10 space-y-8">
          <div>
            <h2 className="text-3xl font-bold mb-4">
              Build Trading Strategies <br />
              <span className="text-primary">Without Code</span>
            </h2>
            <p className="text-muted-foreground text-lg">
              Create, test, and deploy automated trading workflows with a visual drag-and-drop interface.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {FEATURES.map((feature) => {
              const Icon = feature.icon
              return (
                <div
                  key={feature.title}
                  className="rounded-xl border border-border bg-background/50 p-4"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 mb-3">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="font-semibold mb-1">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </div>
              )
            })}
          </div>
        </div>

        <div className="relative z-10 text-sm text-muted-foreground">
          Powered by OpenAlgo API
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <Card className="w-full max-w-md border-0 shadow-none lg:border lg:shadow-sm">
          <CardHeader className="text-center pb-2">
            {/* Mobile logo */}
            <div className="lg:hidden flex items-center justify-center gap-2 mb-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                <Workflow className="h-6 w-6 text-primary" />
              </div>
              <span className="text-xl font-bold">OpenAlgo Flow</span>
            </div>

            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
              {isSetupMode ? (
                <Shield className="h-7 w-7 text-primary" />
              ) : (
                <Lock className="h-7 w-7 text-primary" />
              )}
            </div>
            <CardTitle className="text-2xl">
              {isSetupMode ? 'Create Your Account' : 'Welcome Back'}
            </CardTitle>
            <CardDescription className="text-base">
              {isSetupMode
                ? 'Set up your admin password to get started'
                : 'Enter your password to access your workflows'}
            </CardDescription>
          </CardHeader>

          <CardContent className="pt-4">
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-sm font-medium">
                  {isSetupMode ? 'Create Username' : 'Username'}
                </Label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsernameInput(e.target.value)}
                  placeholder={isSetupMode ? 'Choose a username' : 'Enter your username'}
                  required
                  minLength={isSetupMode ? 3 : 1}
                  maxLength={50}
                  autoComplete="username"
                  className="h-11"
                />
                {isSetupMode && username.length > 0 && username.length < 3 && (
                  <p className="text-xs text-sell">Username must be at least 3 characters</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-medium">
                  {isSetupMode ? 'Create Password' : 'Password'}
                </Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={isSetupMode ? 'Create a strong password' : 'Enter your password'}
                    required
                    minLength={isSetupMode ? 8 : 1}
                    autoComplete={isSetupMode ? 'new-password' : 'current-password'}
                    className="pr-10 h-11"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
                {/* Password strength meter - only in setup mode */}
                {isSetupMode && <PasswordStrength password={password} />}
              </div>

              {isSetupMode && (
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-sm font-medium">
                    Confirm Password
                  </Label>
                  <Input
                    id="confirmPassword"
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm your password"
                    required
                    autoComplete="new-password"
                    className="h-11"
                  />
                  {confirmPassword && password !== confirmPassword && (
                    <p className="text-xs text-sell">Passwords do not match</p>
                  )}
                  {confirmPassword && password === confirmPassword && confirmPassword.length > 0 && (
                    <p className="text-xs text-buy">Passwords match</p>
                  )}
                </div>
              )}

              <Button
                type="submit"
                className="w-full h-11 btn-glow text-base"
                disabled={isSubmitting || !isFormValid}
              >
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isSetupMode ? 'Create Account' : 'Login'}
              </Button>
            </form>

            {isSetupMode && (
              <div className="mt-6 rounded-xl bg-muted/50 p-4 text-sm">
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 shrink-0">
                    <Shield className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground mb-1">Single-User Mode</p>
                    <p className="text-muted-foreground text-xs leading-relaxed">
                      This password protects your trading workflows and API keys.
                      Make sure to remember it as there's no password recovery.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
