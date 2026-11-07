import { useCallback } from 'react'
import { useAsync } from '../hooks/useAsync'
import { getCourses } from '../services/courses'

/** Load and display the learner's selected subjects and mapped topic counts. */
export function Courses() {
  const { data, loading } = useAsync(useCallback(() => getCourses(), []), [])
  return <main><div className="eyebrow">RVCE learning library</div><h1>My subjects</h1><p className="lede">Choose a subject to add its syllabus copy, review mapped topics, and plan study.</p><div className="course-grid">{loading ? <p>Loading subjects…</p> : data.map((course) => <article className="course-card" key={course.id}><span className="course-code">{course.code}</span><h2>{course.title}</h2><p>{course.description}</p><small>{course.concept_count} mapped topics</small></article>)}</div></main>
}
