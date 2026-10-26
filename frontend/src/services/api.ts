const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem('access_token')
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(init?.headers ?? {}) },
    ...init,
  })
  if (!response.ok) throw new Error((await response.text()) || `Request failed: ${response.status}`)
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}
