import { api } from './api'
import type { Course } from '../types'

export const getCourses = () => api<Course[]>('/courses')
