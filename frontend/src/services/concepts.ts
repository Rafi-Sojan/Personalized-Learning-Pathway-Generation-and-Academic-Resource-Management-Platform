import { api } from './api'
import type { Concept } from '../types'

/** Fetch concepts with their syllabus provenance, optionally scoped to a course. */
export const getConcepts = (courseId?: string) => {
  const params = new URLSearchParams({ syllabus_only: 'true' })
  if (courseId) params.set('course_id', courseId)
  return api<Concept[]>(`/concepts?${params.toString()}`)
}

/** Accept or reject an explicitly sourced prerequisite suggestion. */
export const reviewPrerequisite = (conceptId: string, prerequisiteId: string, status: 'accepted' | 'rejected') =>
  api(`/concepts/${encodeURIComponent(conceptId)}/prerequisites/${encodeURIComponent(prerequisiteId)}/review?status=${status}`, { method: 'POST' })
