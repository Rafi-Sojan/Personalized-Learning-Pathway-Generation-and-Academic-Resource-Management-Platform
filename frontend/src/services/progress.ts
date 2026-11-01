import { api } from './api'
import type { Progress } from '../types'

/** Fetch the authenticated learner's progress summary and concept updates. */
export const getProgress = () => api<Progress>('/progress')

/** Save a completion decision and optional score for one concept. */
export const saveProgress = (concept_id: string, completed: boolean, score?: number) =>
  api('/progress', { method: 'POST', body: JSON.stringify({ concept_id, completed, score }) })
