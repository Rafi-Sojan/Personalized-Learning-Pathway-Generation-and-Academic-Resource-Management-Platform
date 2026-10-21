import { api } from './api'
import type { Progress } from '../types'

export const getProgress = () => api<Progress>('/progress')

export const saveProgress = (concept_id: string, completed: boolean, score?: number) =>
  api('/progress', { method: 'POST', body: JSON.stringify({ concept_id, completed, score }) })
