import { api } from './api'
import type { Resource } from '../types'

/** List stored syllabus PDF copies for one course. */
export const getSyllabusSources = (courseId: string) => api<Resource[]>(`/syllabus/sources?course_id=${encodeURIComponent(courseId)}`)

/** Upload a PDF syllabus copy into the selected course's private document storage. */
export const uploadSyllabusSource = (courseId: string, file: File) => {
  const body = new FormData()
  body.append('file', file)
  return api<Resource>(`/syllabus/sources/upload?course_id=${encodeURIComponent(courseId)}`, { method: 'POST', body })
}

/** Queue bounded text extraction for one stored syllabus PDF. */
export const processSyllabusSource = (resourceId: string) => api<Resource>(`/syllabus/sources/${encodeURIComponent(resourceId)}/process`, { method: 'POST' })

/** Create course concepts from the processed syllabus and record its source version. */
export const generateConceptMap = (resourceId: string) => api<{ topics_found: number; concepts_added: number; concepts_reused: number }>(`/syllabus/sources/${encodeURIComponent(resourceId)}/generate-map`, { method: 'POST' })

/** Load extracted syllabus facts with their version, page, confidence, and review state. */
export const getSyllabusRecords = (courseId: string) => api<SyllabusRecord[]>(`/syllabus/records?course_id=${encodeURIComponent(courseId)}`)

/** Save a review decision on a parsed syllabus record. */
export const reviewSyllabusRecord = (recordId: string, status: 'verified' | 'rejected') => api<{ id: string; review_status: string }>(`/syllabus/records/${encodeURIComponent(recordId)}/review?status=${status}`, { method: 'POST' })

export type SyllabusRecord = { id: string; syllabus_version_id: string; source_resource_id: string; record_type: string; source_page: number | null; source_text: string; normalized_text: string; unit_label: string | null; parent_label: string | null; hours: number | null; confidence: number; review_status: string; mapped_concept_id: string | null }
