export type Course = {
  id: string
  code: string
  title: string
  description: string
  progress: number
  concept_count: number
  program_code: string | null
  scheme_year: number | null
  semester: number | null
  origin: 'personal' | 'rvce_catalog'
  catalog_course_id: string | null
  syllabus_source_count: number
  syllabus_status: string
}

export type Concept = {
  id: string
  name: string
  course_id: string
  difficulty: number
  status: 'completed' | 'in_progress' | 'not_started'
  prerequisites: string[]
  suggested_prerequisites: string[]
  unit_label: string | null
  unit_sequence: number | null
  source_page: number | null
  syllabus_version_id: string | null
  parent_concept_id: string | null
  estimated_minutes: number | null
  review_status: 'verified' | 'pending_review' | 'rejected' | null
}

export type RoadmapItem = {
  id: string
  course_id: string
  course_code: string
  course_title: string
  concept_id: string
  concept_name: string
  scheduled_date: string
  minutes: number
  status: 'planned' | 'completed' | 'skipped'
  reason: string
  activity_type: string
  modality: string
  unit_label: string | null
  source_page: number | null
  assessment_scope: 'both' | 'cie_only' | 'see_only'
  syllabus_version_id: string | null
  evidence_question_ids?: string[]
}

export type RoadmapProfileUnit = {
  sequence: number
  label: string
  title: string
  hours: number | null
  source_page: number | null
  assessment_scope: 'both' | 'cie_only' | 'see_only'
}

export type RoadmapProfile = {
  course_codes: string[]
  course_type: string
  category: string | null
  credit_allocation: Record<'lecture' | 'tutorial' | 'practical', number>
  modality_hours: Record<'lecture' | 'tutorial' | 'practical' | 'experiential', number>
  units: RoadmapProfileUnit[]
  course_outcomes: string[]
  assessment_components: string[]
  assessment_format: string
  cie_marks: string | null
  see_marks: string | null
  issues: string[]
}

export type SyllabusRoadmapProfile = {
  available: boolean
  syllabus_version_id: string | null
  status: 'not_available' | 'pending_review' | 'verified' | 'rejected'
  profile: RoadmapProfile | Record<string, never>
  review_notes: string
}

export type Resource = {
  id: string
  title: string
  kind: string
  url: string
  concept_id: string | null
  duration_minutes: number
  processing_status?: string
  processing_error?: string | null
  processed_at?: string | null
}

export type User = { id: string; email: string; name: string; role: string }
export type MappingCandidate = { concept_id: string; name?: string; score?: number; matched_terms?: string[]; evidence?: string[] }
export type MappingMetadata = { status?: string; model_version?: string; margin?: number | null; explanation?: string; candidates?: MappingCandidate[] }
export type HistoricalQuestion = { id: string; course_id: string; source: string; source_document: string; source_resource_id: string | null; exam_year: number; prompt: string; concept_id: string | null; topic_label: string; difficulty: number | null; paper_part: string | null; question_kind: 'quiz' | 'main'; question_number: string | null; subpart: string | null; marks: number | null; source_page: number | null; assessment_type: string; question_format: string; mapping_confidence: number | null; mapping_metadata: MappingMetadata; review_status: string }
export type HistoricalRanking = { concept_id: string; concept_name: string; question_count: number; average_difficulty: number | null; score: number }
export type HistoricalFrequency = { course_id: string; question_count: number; main_question_count: number; mapped_main_question_count: number; unmapped_main_question_count: number; quiz_count: number; year_from: number | null; year_to: number | null; topics: { topic_key: string; topic_name: string; question_count: number; repeat_count: number; last_seen: number; total_marks: number; supporting_questions: { id: string; year: number; source: string; source_document: string; source_page: number | null; marks: number | null }[]; year_counts: { year: number; count: number }[] }[] }
export type ManagedUser = User & { created_at?: string }
