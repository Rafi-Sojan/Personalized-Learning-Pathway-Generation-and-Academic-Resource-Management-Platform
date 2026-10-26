import { api } from './api'
import type { RoadmapItem } from '../types'

export const getRoadmap = () => api<RoadmapItem[]>('/roadmap')

export const generateRoadmap = (course_id: string, target_date: string, daily_minutes: number, revision_minutes = 30) =>
  api<{ id: string; course_id: string; target_date: string; daily_minutes: number; items: RoadmapItem[] }>('/roadmap/generate', { method: 'POST', body: JSON.stringify({ course_id, target_date, daily_minutes, revision_minutes }) })
