import { api } from './api'
import type { Concept } from '../types'

export const getConcepts = () => api<Concept[]>('/concepts')
