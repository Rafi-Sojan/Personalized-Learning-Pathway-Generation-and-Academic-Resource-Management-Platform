import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAsync } from '../hooks/useAsync'
import { enrollRvceSemester, getRvceCatalog, getRvceCourses, type RvceCourseReview } from '../services/rvce'

/** Let learners inspect and enroll only academically verified RVCE course records. */
export function RvceCatalog() {
  const { data, loading, error } = useAsync(useCallback(() => getRvceCatalog(), []), { program_schemes: [], common_first_year_schemes: [] })
  const [program, setProgram] = useState('AS')
  const [scheme, setScheme] = useState(2025)
  const [semester, setSemester] = useState(1)
  const [availableCourses, setAvailableCourses] = useState<RvceCourseReview[]>([])
  const [coursesLoading, setCoursesLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [busy, setBusy] = useState(false)
  const [enrolledCourseIds, setEnrolledCourseIds] = useState<string[]>([])
  const activeProgram = useMemo(() => data.program_schemes.find((item) => item.code === program), [data, program])
  const schemes = useMemo(() => semester <= 2 ? data.common_first_year_schemes : activeProgram?.schemes ?? [], [activeProgram, data, semester])

  /** Select the first manifest branch when a persisted/default code is unavailable. */
  useEffect(() => {
    if (data.program_schemes.length && !data.program_schemes.some((item) => item.code === program)) setProgram(data.program_schemes[0].code)
  }, [data, program])

  /** Keep the selected scheme inside the branch and semester options. */
  useEffect(() => {
    if (schemes.length && !schemes.includes(scheme)) setScheme(schemes[schemes.length - 1])
  }, [scheme, schemes])

  /** Load the exact approved records before enabling semester enrollment. */
  useEffect(() => {
    if (!program || !scheme || !schemes.includes(scheme)) {
      setAvailableCourses([])
      return
    }
    let active = true
    setCoursesLoading(true)
    setSubmitError('')
    getRvceCourses(program, scheme, semester).then((items) => {
      if (active) setAvailableCourses(items)
    }).catch((cause) => {
      if (active) setSubmitError(cause instanceof Error ? cause.message : 'Could not load approved courses.')
    }).finally(() => { if (active) setCoursesLoading(false) })
    return () => { active = false }
  }, [program, scheme, semester, schemes])

  /** Enroll all approved rows in the chosen scope and expose their new workspaces. */
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setMessage('')
    setSubmitError('')
    setEnrolledCourseIds([])
    try {
      const result = await enrollRvceSemester({ program_code: program, scheme_year: scheme, semester })
      setEnrolledCourseIds(result.course_ids)
      setMessage(`${result.created} subject workspace(s) added; ${result.existing} already in your library.`)
    } catch (cause) {
      setSubmitError(cause instanceof Error ? cause.message : 'Could not add this semester.')
    } finally {
      setBusy(false)
    }
  }

  return <main>
    <div className="eyebrow">Verified RVCE catalog</div>
    <h1>Build your semester</h1>
    <p className="lede">Inspect source-backed, academically approved course records before adding them to your private learning workspace.</p>
    {loading && <p aria-live="polite">Loading RVCE program catalog…</p>}
    {error && <p className="form-error" role="alert">Unable to load the RVCE catalog.</p>}
    <section className="panel roadmap-controls">
      <form onSubmit={submit}>
        <div className="form-grid">
          <label>RVCE branch<select value={program} onChange={(event) => setProgram(event.target.value)}>{data.program_schemes.map((entry) => <option key={entry.code} value={entry.code}>{entry.name} ({entry.code})</option>)}</select></label>
          <label>Semester<select value={semester} onChange={(event) => setSemester(Number(event.target.value))}>{[1, 2, 3, 4, 5, 6, 7, 8].map((value) => <option key={value} value={value}>Semester {value}</option>)}</select></label>
          <label>Scheme<select value={scheme} onChange={(event) => setScheme(Number(event.target.value))} disabled={!schemes.length}>{schemes.map((value) => <option key={value} value={value}>{value} scheme</option>)}</select></label>
        </div>
        <div className="catalog-summary">
          <span className="section-kicker">Approved records in this scope</span>
          {coursesLoading ? <p>Checking the reviewed catalog…</p> : availableCourses.length ? <div className="catalog-course-list">{availableCourses.map((course) => <article key={course.id}>
            <strong>{course.course_code} · {course.title}</strong>
            <span>{course.credits} credits · source page {course.source_page ?? 'not recorded'} · {course.source_filename}</span>
          </article>)}</div> : <p className="empty-state">No academically verified course rows are available for this exact branch, scheme, and semester. You can still <Link to="/courses">create a personal subject and attach its syllabus</Link>; that does not mark it as catalog-verified.</p>}
        </div>
        <button className="primary" type="submit" disabled={busy || coursesLoading || availableCourses.length === 0}>{busy ? 'Adding…' : `Add ${availableCourses.length} verified subject${availableCourses.length === 1 ? '' : 's'}`}</button>
        {message && <p aria-live="polite" className="mapping-status">{message} {enrolledCourseIds[0] && <Link to={`/syllabus?course_id=${encodeURIComponent(enrolledCourseIds[0])}`}>Add syllabus copies</Link>}</p>}
        {submitError && <p className="form-error" role="alert">{submitError}</p>}
        <p className="mapping-status">Pending PDF-derived entries stay hidden until an authorized academic reviewer confirms their branch mapping and provenance.</p>
      </form>
    </section>
  </main>
}
