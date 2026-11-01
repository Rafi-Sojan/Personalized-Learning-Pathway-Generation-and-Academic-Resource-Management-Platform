import { api } from './api'
import type { ManagedUser } from '../types'

/** Fetch the administrator-managed user directory. */
export const getManagedUsers = () => api<ManagedUser[]>('/admin/users')
/** Create a managed account with the requested server-validated role. */
export const createManagedUser = (payload: { email: string; name: string; password: string; role: string }) => api<ManagedUser>('/admin/users', { method: 'POST', body: JSON.stringify(payload) })
