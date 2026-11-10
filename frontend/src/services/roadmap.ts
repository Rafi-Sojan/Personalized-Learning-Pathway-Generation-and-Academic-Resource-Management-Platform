import { api } from './api'
import type { RoadmapItem } from '../types'

export type RoadmapMode = 'full_term' | 'cie' | 'see' | 'revision'

export type RoadmapConstraints = {
  start_date: string
  target_date: string
  daily_minutes: number
  revision_minutes: number
  mode: RoadmapMode
  unavailable_weekdays: number[]
}

export type StudyPlan = {
  id: string
  scope_type: 'course' | 'semester'
  mode: RoadmapMode
  course_id: string | null
  program_code: string | null
  scheme_year: number | null
  semester: number | null
  start_date: string
  target_date: string
  daily_minutes: number
  revision_minutes: number
  unavailable_weekdays: number[]
  items: RoadmapItem[]
}

/** Fetch a short, non-persisted roadmap preview for one authenticated course. */
export const getRoadmap = (courseId: string, days = 14) => api<RoadmapItem[]>(`/roadmap?course_id=${encodeURIComponent(courseId)}&days=${days}`)

/** Load the newest active persisted plan, optionally constrained to one subject. */
export const getActiveRoadmap = (courseId?: string) => api<StudyPlan | null>(`/roadmap/active${courseId ? `?course_id=${encodeURIComponent(courseId)}` : ''}`)

/** Generate and persist one reviewed course roadmap. */
export const generateRoadmap = (courseId: string, constraints: RoadmapConstraints) =>
  api<StudyPlan>('/roadmap/generate', { method: 'POST', body: JSON.stringify({ course_id: courseId, ...constraints }) })

/** Generate and persist one balanced plan over explicitly selected same-scope subjects. */
export const generateSemesterRoadmap = (courseIds: string[], constraints: RoadmapConstraints) =>
  api<StudyPlan>('/roadmap/semester/generate', { method: 'POST', body: JSON.stringify({ course_ids: courseIds, ...constraints }) })

/** Mark an owned roadmap session and optionally feed a mastery score into regeneration. */
export const updateRoadmapItem = (itemId: string, status: 'planned' | 'completed' | 'skipped', masteryScore?: number) =>
  api<{ id: string; status: string; concept_id: string; mastery_score: number | null }>(`/roadmap/items/${encodeURIComponent(itemId)}`, {
    method: 'PATCH',
    body: JSON.stringify({ status, mastery_score: masteryScore }),
  })
