import { api } from './api'
import type { RoadmapItem } from '../types'

export const getRoadmap = () => api<RoadmapItem[]>('/roadmap')
