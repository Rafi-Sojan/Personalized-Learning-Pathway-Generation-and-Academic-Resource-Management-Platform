import { api } from './api'
import type { Course } from '../types'

export type CourseCreate = {
  code: string
  title: string
  description: string
  program_code: string
  scheme_year: number
  semester: number
}

/** Fetch the authenticated user's course list with progress summaries. */
export const getCourses = () => api<Course[]>('/courses')

/** Create a learner-owned subject workspace inside a validated RVCE academic scope. */
export const createCourse = (payload: CourseCreate) => api<Course>('/courses', { method: 'POST', body: JSON.stringify(payload) })
