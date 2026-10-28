export type Course = {
  id: string
  code: string
  title: string
  description: string
  progress: number
  concept_count: number
}

export type Concept = {
  id: string
  name: string
  course_id: string
  difficulty: number
  status: 'completed' | 'in_progress' | 'not_started'
  prerequisites: string[]
}

export type RoadmapItem = {
  id: string
  concept_id: string
  concept_name: string
  scheduled_date: string
  minutes: number
  status: string
  reason: string
}

export type Resource = {
  id: string
  title: string
  kind: string
  url: string
  concept_id: string | null
  duration_minutes: number
  processing_status?: string
}

export type Progress = {
  completed_concepts: number
  total_concepts: number
  updates: Record<string, { completed: boolean; score?: number | null }>
}

export type User = { id: string; email: string; name: string; role: string }
export type HistoricalQuestion = { id: string; course_id: string; source: string; exam_year: number; prompt: string; concept_id: string | null; topic_label: string; difficulty: number }
export type HistoricalRanking = { concept_id: string; concept_name: string; question_count: number; average_difficulty: number; score: number }
export type ManagedUser = User & { created_at?: string }
