const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

/** Extract FastAPI's structured detail while retaining a useful text/status fallback. */
async function responseErrorMessage(response: Response): Promise<string> {
  const fallback = `Request failed: ${response.status}`
  const body = await response.text()
  if (!body) return fallback
  try {
    const payload = JSON.parse(body) as { detail?: unknown }
    if (typeof payload.detail === 'string' && payload.detail.trim()) return payload.detail
    if (Array.isArray(payload.detail)) {
      const messages = payload.detail.flatMap((item) => {
        if (typeof item === 'string') return [item]
        if (item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string') return [item.msg]
        return []
      })
      if (messages.length) return messages.join('; ')
    }
  } catch {
    return body
  }
  return body
}

/** Send a typed API request with the active bearer token and parse its JSON response. */
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem('access_token')
  const isMultipart = typeof FormData !== 'undefined' && init?.body instanceof FormData
  const response = await fetch(`${API_URL}${path}`, {
    headers: { ...(isMultipart ? {} : { 'Content-Type': 'application/json' }), ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(init?.headers ?? {}) },
    ...init,
  })
  if (response.status === 401 && !path.startsWith('/auth/login') && !path.startsWith('/auth/register')) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    if (window.location.pathname !== '/login') window.location.replace('/login')
    throw new Error('Your session expired. Please sign in again.')
  }
  if (!response.ok) throw new Error(await responseErrorMessage(response))
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

/** Fetch an authenticated binary source document such as an imported paper PDF. */
export async function apiBlob(path: string): Promise<Blob> {
  const token = localStorage.getItem('access_token')
  const response = await fetch(`${API_URL}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (response.status === 401) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    if (window.location.pathname !== '/login') window.location.replace('/login')
    throw new Error('Your session expired. Please sign in again.')
  }
  if (!response.ok) throw new Error(await responseErrorMessage(response))
  return response.blob()
}
