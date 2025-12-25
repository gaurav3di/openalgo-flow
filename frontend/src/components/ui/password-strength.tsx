/**
 * Password Strength Meter Component
 * Shows visual feedback on password strength with validation rules
 */
import { useMemo } from 'react'
import { Check, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PasswordRule {
  id: string
  label: string
  validator: (password: string) => boolean
}

const PASSWORD_RULES: PasswordRule[] = [
  {
    id: 'length',
    label: 'At least 8 characters',
    validator: (p) => p.length >= 8,
  },
  {
    id: 'uppercase',
    label: 'One uppercase letter',
    validator: (p) => /[A-Z]/.test(p),
  },
  {
    id: 'lowercase',
    label: 'One lowercase letter',
    validator: (p) => /[a-z]/.test(p),
  },
  {
    id: 'number',
    label: 'One number',
    validator: (p) => /[0-9]/.test(p),
  },
  {
    id: 'special',
    label: 'One special character (!@#$%^&*)',
    validator: (p) => /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(p),
  },
]

interface PasswordStrengthProps {
  password: string
  showRules?: boolean
}

export function PasswordStrength({ password, showRules = true }: PasswordStrengthProps) {
  const { score, passedRules } = useMemo(() => {
    const passed = PASSWORD_RULES.filter((rule) => rule.validator(password))
    return {
      score: passed.length,
      passedRules: passed.map((r) => r.id),
    }
  }, [password])

  const getStrengthLabel = () => {
    if (password.length === 0) return ''
    if (score <= 1) return 'Very Weak'
    if (score === 2) return 'Weak'
    if (score === 3) return 'Fair'
    if (score === 4) return 'Good'
    return 'Strong'
  }

  const getStrengthColor = () => {
    if (password.length === 0) return 'bg-muted'
    if (score <= 1) return 'bg-red-500'
    if (score === 2) return 'bg-orange-500'
    if (score === 3) return 'bg-yellow-500'
    if (score === 4) return 'bg-lime-500'
    return 'bg-green-500'
  }

  if (password.length === 0) {
    return null
  }

  return (
    <div className="space-y-3">
      {/* Strength bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between items-center">
          <span className="text-xs text-muted-foreground">Password strength</span>
          <span className={cn(
            'text-xs font-medium',
            score <= 1 && 'text-red-500',
            score === 2 && 'text-orange-500',
            score === 3 && 'text-yellow-500',
            score === 4 && 'text-lime-500',
            score === 5 && 'text-green-500'
          )}>
            {getStrengthLabel()}
          </span>
        </div>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((level) => (
            <div
              key={level}
              className={cn(
                'h-1.5 flex-1 rounded-full transition-colors duration-200',
                level <= score ? getStrengthColor() : 'bg-muted'
              )}
            />
          ))}
        </div>
      </div>

      {/* Rules checklist */}
      {showRules && (
        <div className="grid grid-cols-1 gap-1.5">
          {PASSWORD_RULES.map((rule) => {
            const passed = passedRules.includes(rule.id)
            return (
              <div
                key={rule.id}
                className={cn(
                  'flex items-center gap-2 text-xs transition-colors',
                  passed ? 'text-green-500' : 'text-muted-foreground'
                )}
              >
                {passed ? (
                  <Check className="h-3 w-3" />
                ) : (
                  <X className="h-3 w-3" />
                )}
                <span>{rule.label}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

/**
 * Validate password against all rules
 * Returns true if all rules pass
 */
export function validatePassword(password: string): { isValid: boolean; errors: string[] } {
  const errors: string[] = []

  for (const rule of PASSWORD_RULES) {
    if (!rule.validator(password)) {
      errors.push(rule.label)
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

/**
 * Get password strength score (0-5)
 */
export function getPasswordScore(password: string): number {
  return PASSWORD_RULES.filter((rule) => rule.validator(password)).length
}
