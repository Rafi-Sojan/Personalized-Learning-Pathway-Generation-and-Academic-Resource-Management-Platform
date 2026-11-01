import { api } from './api'
import type { Concept } from '../types'

/** Fetch the authenticated user's concepts and prerequisite links. */
export const getConcepts = () => api<Concept[]>('/concepts')
