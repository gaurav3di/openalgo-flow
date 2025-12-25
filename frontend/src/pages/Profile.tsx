/**
 * Profile Page
 * Displays user profile info and allows password change
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, User, Calendar, Lock, Check } from 'lucide-react'
import { authApi } from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PasswordStrength, validatePassword, getPasswordScore } from '@/components/ui/password-strength'
import { useToast } from '@/hooks/use-toast'

export function Profile() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const { username: storedUsername } = useAuthStore()

  // Password change form state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showChangePassword, setShowChangePassword] = useState(false)

  // Fetch profile data
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: authApi.getProfile,
  })

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: () => authApi.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      toast({
        title: 'Password changed',
        description: 'Your password has been updated successfully.',
        variant: 'success',
      })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setShowChangePassword(false)
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to change password',
        description: error.message,
        variant: 'destructive',
      })
    },
  })

  const handleChangePassword = (e: React.FormEvent) => {
    e.preventDefault()

    if (newPassword !== confirmPassword) {
      toast({
        title: 'Passwords do not match',
        description: 'Please make sure both passwords are the same.',
        variant: 'destructive',
      })
      return
    }

    const validation = validatePassword(newPassword)
    if (!validation.isValid) {
      toast({
        title: 'Password does not meet requirements',
        description: `Missing: ${validation.errors.slice(0, 2).join(', ')}${validation.errors.length > 2 ? '...' : ''}`,
        variant: 'destructive',
      })
      return
    }

    changePasswordMutation.mutate()
  }

  const isPasswordFormValid =
    currentPassword.length > 0 &&
    getPasswordScore(newPassword) >= 5 &&
    newPassword === confirmPassword

  const displayUsername = profile?.username || storedUsername || 'User'
  const createdAt = profile?.created_at
    ? new Date(profile.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : 'Unknown'

  if (profileLoading) {
    return (
      <div className="flex h-[calc(100vh-3.5rem)] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="container max-w-2xl py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Profile</h1>
        <p className="text-muted-foreground">
          Manage your account settings
        </p>
      </div>

      {/* Profile Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Account Information</CardTitle>
          <CardDescription>Your account details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-2xl font-bold text-primary">
              {displayUsername.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="text-xl font-semibold">{displayUsername}</h2>
              <p className="text-sm text-muted-foreground">Administrator</p>
            </div>
          </div>

          <div className="grid gap-4 pt-4 border-t">
            <div className="flex items-center gap-3">
              <User className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Username</p>
                <p className="text-sm text-muted-foreground">{displayUsername}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Account Created</p>
                <p className="text-sm text-muted-foreground">{createdAt}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Security Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Security</CardTitle>
          <CardDescription>Manage your password</CardDescription>
        </CardHeader>
        <CardContent>
          {!showChangePassword ? (
            <Button
              variant="outline"
              onClick={() => setShowChangePassword(true)}
              className="gap-2"
            >
              <Lock className="h-4 w-4" />
              Change Password
            </Button>
          ) : (
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="currentPassword">Current Password</Label>
                <Input
                  id="currentPassword"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter your current password"
                  required
                  autoComplete="current-password"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="newPassword">New Password</Label>
                <Input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter a new password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                />
                <PasswordStrength password={newPassword} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmNewPassword">Confirm New Password</Label>
                <Input
                  id="confirmNewPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your new password"
                  required
                  autoComplete="new-password"
                />
                {confirmPassword && newPassword !== confirmPassword && (
                  <p className="text-xs text-sell">Passwords do not match</p>
                )}
                {confirmPassword && newPassword === confirmPassword && confirmPassword.length > 0 && (
                  <p className="text-xs text-buy flex items-center gap-1">
                    <Check className="h-3 w-3" />
                    Passwords match
                  </p>
                )}
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  type="submit"
                  disabled={changePasswordMutation.isPending || !isPasswordFormValid}
                >
                  {changePasswordMutation.isPending && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Update Password
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setShowChangePassword(false)
                    setCurrentPassword('')
                    setNewPassword('')
                    setConfirmPassword('')
                  }}
                >
                  Cancel
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
