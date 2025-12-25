/**
 * Authentication Store
 * Manages authentication state and token storage
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  username: string | null
  isAuthenticated: boolean
  isSetupComplete: boolean | null

  // Actions
  setToken: (token: string) => void
  setUsername: (username: string) => void
  setSetupComplete: (complete: boolean) => void
  logout: () => void
  checkAuth: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      username: null,
      isAuthenticated: false,
      isSetupComplete: null,

      setToken: (token: string) => {
        set({ token, isAuthenticated: true })
      },

      setUsername: (username: string) => {
        set({ username })
      },

      setSetupComplete: (complete: boolean) => {
        set({ isSetupComplete: complete })
      },

      logout: () => {
        set({ token: null, username: null, isAuthenticated: false })
      },

      checkAuth: () => {
        const state = get()
        return state.isAuthenticated && !!state.token
      },
    }),
    {
      name: 'openalgo-flow-auth',
      partialize: (state) => ({
        token: state.token,
        username: state.username,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

/**
 * Get the current auth token for API requests
 */
export const getAuthToken = (): string | null => {
  return useAuthStore.getState().token
}
