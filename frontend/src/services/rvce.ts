import { api } from './api'

export type RvceProgram = { code: string; name: string; schemes: number[]; aliases?: string[] }
export type RvceCatalog = { program_schemes: RvceProgram[]; common_first_year_schemes: number[] }
export type RvceEnrollment = { program_code: string; scheme_year: number; semester: number }
export type RvceEnrollmentResult = { created: number; existing: number; course_ids: string[] }
export type RvceCourseReview = {
  id: string; program_code: string; scheme_year: number; semester: number; course_code: string; title: string
  credits: number; source_filename: string; source_page: number | null; source_checksum: string; verification_status: string
}

/** Fetch the normalized RVCE program list and supported first-year schemes. */
export const getRvceCatalog = () => api<RvceCatalog>('/catalog/rvce')
/** Enroll the current learner in verified course rows for one scheme semester. */
export const enrollRvceSemester = (selection: RvceEnrollment) => api<RvceEnrollmentResult>('/catalog/rvce/enroll', { method: 'POST', body: JSON.stringify(selection) })
/** Load pending source-backed records for the academic review interface. */
export const getRvceCourseReview = () => api<RvceCourseReview[]>('/catalog/rvce/courses/review')
/** Record an administrator decision and optional first-year branch mapping. */
export const verifyRvceCourse = (id: string, verification_status: 'academic_verified' | 'rejected', program_code?: string) => api<RvceCourseReview>(`/catalog/rvce/courses/${encodeURIComponent(id)}/verification`, { method: 'PATCH', body: JSON.stringify({ verification_status, ...(program_code ? { program_code } : {}) }) })
