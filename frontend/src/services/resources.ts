import { api } from './api'
import type { Resource } from '../types'

export type ResourceMapping = { id: string; resource_id: string; concept_id: string; confidence: number | null; status: string; source: string; reviewed_by: string | null }
export const getResources = () => api<Resource[]>('/resources')
export const processResource = (resourceId: string) => api<Resource>(`/resources/${resourceId}/process`, { method: 'POST' })
export const getResourceMappings = (resourceId: string) => api<ResourceMapping[]>(`/resources/${resourceId}/mappings`)
export const updateResourceMapping = (resourceId: string, payload: { concept_id: string; confidence?: number; status: string; source: string }) => api<ResourceMapping>(`/resources/${resourceId}/mappings`, { method: 'POST', body: JSON.stringify(payload) })
export const uploadResource = (courseId: string, file: File, conceptId?: string) => { const body = new FormData(); body.append('file', file); return api<Resource>(`/resources/upload?course_id=${encodeURIComponent(courseId)}${conceptId ? `&concept_id=${encodeURIComponent(conceptId)}` : ''}`, { method: 'POST', body }) }
