import { api } from './api'

export type AccountExport = {
  user: { id: string; email: string; name: string; role: string }
  courses: unknown[]
  concepts: unknown[]
  progress: unknown[]
  quiz_attempts: unknown[]
  study_plans: unknown[]
  resources: unknown[]
  resource_mappings: unknown[]
}

/** Request the current user's portable learning-data export. */
export function exportAccount() {
  return api<AccountExport>('/auth/export')
}

/** Request permanent account deletion using the required email confirmation. */
export function deleteAccount(confirm_email: string) {
  return api<void>('/auth/delete', { method: 'POST', body: JSON.stringify({ confirm_email }) })
}
