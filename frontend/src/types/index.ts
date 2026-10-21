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
}

export type Progress = {
  completed_concepts: number
  total_concepts: number
  updates: Record<string, { completed: boolean; score?: number | null }>
}
