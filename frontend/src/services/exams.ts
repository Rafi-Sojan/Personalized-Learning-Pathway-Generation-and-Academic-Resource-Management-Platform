import { api } from './api'
import type { HistoricalQuestion, HistoricalRanking } from '../types'

/** Load historical question records for a course. */
export const getExamQuestions = (courseId: string) => api<HistoricalQuestion[]>(`/exams/questions?course_id=${encodeURIComponent(courseId)}`)
/** Load concept rankings derived from a course's historical question evidence. */
export const getExamRankings = (courseId: string) => api<HistoricalRanking[]>(`/exams/rankings?course_id=${encodeURIComponent(courseId)}`)
/** Import paper text and metadata for server-side question parsing. */
export const importExamQuestions = (payload: { course_id: string; source: string; exam_year: number; text: string }) => api<HistoricalQuestion[]>('/exams/import', { method: 'POST', body: JSON.stringify(payload) })
