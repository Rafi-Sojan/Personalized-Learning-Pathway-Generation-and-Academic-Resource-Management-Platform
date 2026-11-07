import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ConceptMapView } from '../components/concept-map/ConceptMapView'
import { useAsync } from '../hooks/useAsync'
import { getConcepts, reviewPrerequisite } from '../services/concepts'
import { getCourses } from '../services/courses'
import type { Course } from '../types'

/** Display syllabus-derived concepts and their source locations for the selected course. */
export function ConceptMap() {
  const [courses, setCourses] = useState<Course[]>([])
  const [courseId, setCourseId] = useState('')
  const [courseError, setCourseError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  /** Load the learner's courses and initialize the map to the first available one. */
  useEffect(() => {
    getCourses().then((items) => {
      setCourses(items)
      if (items[0]) setCourseId(items[0].id)
    }).catch((reason) => setCourseError(reason instanceof Error ? reason.message : 'Unable to load courses'))
  }, [])

  /** Request only concepts belonging to the selected course. */
  const loadConcepts = useCallback(() => courseId ? getConcepts(courseId) : Promise.resolve([]), [courseId, refreshKey])
  const { data, loading, error } = useAsync(loadConcepts, [])
  const selectedCourse = courses.find((course) => course.id === courseId)

  /** Submit a reviewer decision and reload the graph after the API accepts it. */
  async function reviewEdge(conceptId: string, prerequisiteId: string, status: 'accepted' | 'rejected') {
    try { await reviewPrerequisite(conceptId, prerequisiteId, status); setRefreshKey((key) => key + 1) }
    catch (reason) { setCourseError(reason instanceof Error ? reason.message : 'Unable to review prerequisite') }
  }

  return <main>
    <div className="eyebrow">Built from your syllabus copy</div>
    <h1>Concept map</h1>
    <p className="lede">Review mapped topics by syllabus unit and verify each topic against its source page.</p>
    <section className="panel">
      <div className="panel-heading"><div><span className="section-kicker">Course concept graph</span><h2>{selectedCourse?.title ?? 'Select a course'}</h2></div>
        <label className="inline-select">Subject<select value={courseId} onChange={(event) => setCourseId(event.target.value)}>{courses.map((course) => <option key={course.id} value={course.id}>{course.code} · {course.title}</option>)}</select></label>
      </div>
      {(courseError || error) && <p className="form-error" role="alert">{courseError || error}</p>}
      {loading ? <p aria-live="polite">Loading concepts…</p> : data.length ? <ConceptMapView concepts={data} /> : <div className="empty-state"><p>No concepts are mapped for this course yet.</p><Link className="secondary" to="/syllabus">Add a syllabus copy and generate the map</Link></div>}
      {data.some((concept) => concept.suggested_prerequisites.length > 0) && <div className="exam-frequency-list"><h3>Suggested prerequisites · pending review</h3>{data.flatMap((concept) => concept.suggested_prerequisites.map((prerequisiteId) => {
        const prerequisite = data.find((item) => item.id === prerequisiteId)
        return <article className="roadmap-row" key={`${concept.id}-${prerequisiteId}`}><span className="roadmap-number">→</span><div><strong>{concept.name}</strong><p>Suggested prerequisite: {prerequisite?.name ?? 'Unknown topic'} · verify against syllabus before roadmap use</p><button className="secondary" type="button" onClick={() => void reviewEdge(concept.id, prerequisiteId, 'accepted')}>Accept</button> <button className="secondary" type="button" onClick={() => void reviewEdge(concept.id, prerequisiteId, 'rejected')}>Reject</button></div></article>
      }))}</div>}
    </section>
  </main>
}
