import { api } from './api'
import type { Course } from '../types'

/** Fetch the authenticated user's course list with progress summaries. */
export const getCourses = () => api<Course[]>('/courses')
