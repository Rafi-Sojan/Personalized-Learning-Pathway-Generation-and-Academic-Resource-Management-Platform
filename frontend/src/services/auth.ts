import { api } from './api'
import type { User } from '../types'

type AuthResponse = { access_token: string; token_type: string; user: User }

export async function login(email: string, password: string): Promise<AuthResponse> {
  const result = await api<AuthResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
  localStorage.setItem('access_token', result.access_token)
  localStorage.setItem('user', JSON.stringify(result.user))
  return result
}

export function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
}
