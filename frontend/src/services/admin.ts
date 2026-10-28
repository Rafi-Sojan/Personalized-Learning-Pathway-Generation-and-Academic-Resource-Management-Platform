import { api } from './api'
import type { ManagedUser } from '../types'

export const getManagedUsers = () => api<ManagedUser[]>('/admin/users')
export const createManagedUser = (payload: { email: string; name: string; password: string; role: string }) => api<ManagedUser>('/admin/users', { method: 'POST', body: JSON.stringify(payload) })
