import { api } from './api'
import type { RoadmapItem } from '../types'

/** Fetch the current roadmap preview for the authenticated learner. */
export const getRoadmap = () => api<RoadmapItem[]>('/roadmap')

/** Generate and persist a roadmap under the supplied deadline and daily capacity. */
export const generateRoadmap = (course_id: string, target_date: string, daily_minutes: number, revision_minutes = 30) =>
  api<{ id: string; course_id: string; target_date: string; daily_minutes: number; items: RoadmapItem[] }>('/roadmap/generate', { method: 'POST', body: JSON.stringify({ course_id, target_date, daily_minutes, revision_minutes }) })
