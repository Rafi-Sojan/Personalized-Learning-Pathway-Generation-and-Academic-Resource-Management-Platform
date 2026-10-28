import { api } from './api'
import type { HistoricalQuestion, HistoricalRanking } from '../types'

export const getExamQuestions = (courseId: string) => api<HistoricalQuestion[]>(`/exams/questions?course_id=${encodeURIComponent(courseId)}`)
export const getExamRankings = (courseId: string) => api<HistoricalRanking[]>(`/exams/rankings?course_id=${encodeURIComponent(courseId)}`)
export const importExamQuestions = (payload: { course_id: string; source: string; exam_year: number; text: string }) => api<HistoricalQuestion[]>('/exams/import', { method: 'POST', body: JSON.stringify(payload) })
