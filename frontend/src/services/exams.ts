import { api } from './api'
import { apiBlob } from './api'
import type { HistoricalFrequency, HistoricalQuestion, HistoricalRanking } from '../types'

/** Load course questions with optional year and keyword filters. */
export const getExamQuestions = (courseId: string, yearFrom?: number, yearTo?: number, search?: string, assessmentType?: string, questionFormat?: string, topic?: string) => {
  const params = new URLSearchParams({ course_id: courseId })
  if (yearFrom) params.set('year_from', String(yearFrom))
  if (yearTo) params.set('year_to', String(yearTo))
  if (search) params.set('search', search)
  if (assessmentType) params.set('assessment_type', assessmentType)
  if (questionFormat) params.set('question_format', questionFormat)
  if (topic) params.set('topic', topic)
  return api<HistoricalQuestion[]>(`/exams/questions?${params.toString()}`)
}
/** Load concept rankings derived from a course's historical question evidence. */
export const getExamRankings = (courseId: string) => api<HistoricalRanking[]>(`/exams/rankings?course_id=${encodeURIComponent(courseId)}`)
/** Load topic counts, yearly recurrence, and repeated prompts for a subject. */
export const getExamFrequency = (courseId: string, yearFrom?: number, yearTo?: number, assessmentType?: string) => {
  const params = new URLSearchParams({ course_id: courseId })
  if (yearFrom) params.set('year_from', String(yearFrom))
  if (yearTo) params.set('year_to', String(yearTo))
  if (assessmentType) params.set('assessment_type', assessmentType)
  return api<HistoricalFrequency>(`/exams/frequency?${params.toString()}`)
}
/** Import paper text and metadata for server-side question parsing. */
export const importExamQuestions = (payload: { course_id: string; source: string; exam_year: number; text: string }) => api<HistoricalQuestion[]>('/exams/import', { method: 'POST', body: JSON.stringify(payload) })

/** Upload a PDF paper for server-side text extraction, parsing, and topic association. */
export const importExamPaperPdf = (courseId: string, source: string, examYear: number, file: File, assessmentType: string, questionFormat: string, partAIsQuiz: boolean) => {
  const body = new FormData()
  body.append('source', source)
  body.append('exam_year', String(examYear))
  body.append('file', file)
  body.append('assessment_type', assessmentType)
  body.append('question_format', questionFormat)
  body.append('part_a_is_quiz', String(partAIsQuiz))
  return api<HistoricalQuestion[]>(`/exams/import-pdf?course_id=${encodeURIComponent(courseId)}`, { method: 'POST', body })
}

/** Save a human review decision for a parsed question and its concept mapping. */
export const reviewExamQuestion = (questionId: string, status: 'verified' | 'rejected' | 'pending_review', difficulty?: number, assessmentType?: string, questionFormat?: string, conceptId?: string | null) => {
  const params = new URLSearchParams({ status })
  if (difficulty) params.set('difficulty', String(difficulty))
  if (assessmentType) params.set('assessment_type', assessmentType)
  if (questionFormat) params.set('question_format', questionFormat)
  if (conceptId) params.set('concept_id', conceptId)
  else if (conceptId === null) params.set('clear_concept', 'true')
  return api<{ id: string; review_status: string; difficulty: number | null; assessment_type: string; question_format: string; concept_id: string | null; topic_label: string }>(`/exams/questions/${encodeURIComponent(questionId)}/review?${params.toString()}`, { method: 'POST' })
}

/** Load an authenticated original paper PDF for source-page inspection. */
export const getExamPaperPdf = (resourceId: string) => apiBlob(`/exams/papers/${encodeURIComponent(resourceId)}`)
