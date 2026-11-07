import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { createCourse, getCourses } from '../services/courses'
import { getRvceCatalog, type RvceCatalog } from '../services/rvce'
import { uploadSyllabusSource } from '../services/syllabus'
import type { Course } from '../types'

/** Convert an internal processing state into a short learner-facing label. */
function syllabusLabel(course: Course) {
  if (!course.syllabus_source_count) return 'No syllabus copy'
  return `${course.syllabus_source_count} syllabus cop${course.syllabus_source_count === 1 ? 'y' : 'ies'} · ${course.syllabus_status.replace(/_/g, ' ')}`
}

/** Format the optional academic scope without implying that a personal subject is verified. */
function scopeLabel(course: Course) {
  if (!course.program_code || !course.scheme_year || !course.semester) return 'Legacy subject · academic scope not set'
  return `${course.program_code} · ${course.scheme_year} scheme · Semester ${course.semester}`
}

/** Create learner-owned RVCE subject workspaces and optionally attach their first syllabus copy. */
export function Courses() {
  const [courses, setCourses] = useState<Course[]>([])
  const [catalog, setCatalog] = useState<RvceCatalog | null>(null)
  const [programCode, setProgramCode] = useState('')
  const [semester, setSemester] = useState(1)
  const [schemeYear, setSchemeYear] = useState(0)
  const [code, setCode] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [syllabusFile, setSyllabusFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [createdCourseId, setCreatedCourseId] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)

  /** Load both the user's workspaces and the controlled RVCE branch/scheme manifest. */
  useEffect(() => {
    let active = true
    Promise.all([getCourses(), getRvceCatalog()]).then(([items, manifest]) => {
      if (!active) return
      setCourses(items)
      setCatalog(manifest)
      setProgramCode((current) => current || manifest.program_schemes[0]?.code || '')
    }).catch((reason) => {
      if (active) setError(reason instanceof Error ? reason.message : 'Unable to load subject setup')
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const activeProgram = useMemo(() => catalog?.program_schemes.find((item) => item.code === programCode), [catalog, programCode])
  const availableSchemes = useMemo(() => semester <= 2 ? catalog?.common_first_year_schemes ?? [] : activeProgram?.schemes ?? [], [activeProgram, catalog, semester])

  /** Keep scheme selection valid when the branch or semester changes. */
  useEffect(() => {
    if (availableSchemes.length && !availableSchemes.includes(schemeYear)) setSchemeYear(availableSchemes[availableSchemes.length - 1])
  }, [availableSchemes, schemeYear])

  /** Persist the subject first, then attach the optional private syllabus PDF. */
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!programCode || !schemeYear) return
    setBusy(true)
    setError('')
    setMessage('')
    setCreatedCourseId('')
    try {
      const created = await createCourse({ code, title, description, program_code: programCode, scheme_year: schemeYear, semester })
      setCreatedCourseId(created.id)
      if (syllabusFile) {
        try {
          await uploadSyllabusSource(created.id, syllabusFile)
        } catch (reason) {
          setError(`Subject created, but the syllabus copy was not attached: ${reason instanceof Error ? reason.message : 'upload failed'}`)
          setCourses(await getCourses())
          return
        }
      }
      setCourses(await getCourses())
      setMessage(syllabusFile ? 'Subject and syllabus copy added. Continue to extraction and topic review.' : 'Subject added. You can attach its syllabus copy now or later.')
      setCode('')
      setTitle('')
      setDescription('')
      setSyllabusFile(null)
      if (fileInput.current) fileInput.current.value = ''
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to add subject')
    } finally {
      setBusy(false)
    }
  }

  return <main>
    <div className="eyebrow">RVCE learner workspace</div>
    <h1>My subjects</h1>
    <p className="lede">Create a subject under its RVCE branch, scheme, and semester, then attach the syllabus copy that will drive its concept map and roadmap.</p>
    <section className="panel course-onboarding">
      <div className="panel-heading"><div><span className="section-kicker">Personal subject setup</span><h2>Add a subject and syllabus</h2></div><Link to="/rvce">Use verified catalog</Link></div>
      <p className="mapping-status">A personal subject is a private learning workspace. Its branch selection does not publish or academically verify an RVCE catalog record.</p>
      <form onSubmit={submit}>
        <div className="form-grid">
          <label>RVCE branch<select required value={programCode} onChange={(event) => setProgramCode(event.target.value)} disabled={!catalog}>{catalog?.program_schemes.map((program) => <option key={program.code} value={program.code}>{program.name} ({program.code})</option>)}</select></label>
          <label>Semester<select required value={semester} onChange={(event) => setSemester(Number(event.target.value))}>{[1, 2, 3, 4, 5, 6, 7, 8].map((value) => <option key={value} value={value}>Semester {value}</option>)}</select></label>
          <label>Scheme<select required value={schemeYear || ''} onChange={(event) => setSchemeYear(Number(event.target.value))} disabled={!availableSchemes.length}><option value="" disabled>Select scheme</option>{availableSchemes.map((value) => <option key={value} value={value}>{value} scheme</option>)}</select></label>
          <label>Subject code<input required minLength={2} maxLength={20} value={code} onChange={(event) => setCode(event.target.value.toUpperCase())} placeholder="e.g. AI253IA" /></label>
          <label className="full-field">Subject title<input required minLength={2} maxLength={200} value={title} onChange={(event) => setTitle(event.target.value)} placeholder="e.g. Deep Learning" /></label>
          <label className="full-field">Description <span className="optional-label">optional</span><textarea rows={3} maxLength={2000} value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Personal notes about this subject" /></label>
          <label className="full-field">Syllabus PDF <span className="optional-label">optional now</span><input ref={fileInput} type="file" accept="application/pdf,.pdf" onChange={(event) => setSyllabusFile(event.target.files?.[0] ?? null)} /></label>
        </div>
        <div className="action-row"><button className="primary" type="submit" disabled={busy || !catalog || !availableSchemes.length}>{busy ? 'Adding subject…' : syllabusFile ? 'Add subject and syllabus' : 'Add subject'}</button></div>
      </form>
      {message && <p role="status" className="mapping-status">{message} {createdCourseId && <Link to={`/syllabus?course_id=${encodeURIComponent(createdCourseId)}`}>Open syllabus workflow</Link>}</p>}
      {error && <p className="form-error" role="alert">{error} {createdCourseId && <Link to={`/syllabus?course_id=${encodeURIComponent(createdCourseId)}`}>Open the created subject</Link>}</p>}
    </section>
    <section aria-labelledby="subject-list-heading">
      <div className="panel-heading subject-list-heading"><div><span className="section-kicker">Your learning scopes</span><h2 id="subject-list-heading">{courses.length} subject{courses.length === 1 ? '' : 's'}</h2></div></div>
      <div className="course-grid">{loading ? <p>Loading subjects…</p> : courses.map((course) => <article className="course-card" key={course.id}>
        <div className="course-card-heading"><span className="course-code">{course.code}</span><span className={`scope-badge ${course.origin === 'rvce_catalog' ? 'verified' : ''}`}>{course.origin === 'rvce_catalog' ? 'Verified catalog' : 'Personal'}</span></div>
        <h2>{course.title}</h2>
        <p>{course.description || 'No personal description added.'}</p>
        <div className="course-meta"><span>{scopeLabel(course)}</span><span>{course.concept_count} mapped topics</span><span>{syllabusLabel(course)}</span></div>
        <div className="course-actions"><Link to={`/syllabus?course_id=${encodeURIComponent(course.id)}`}>{course.syllabus_source_count ? 'Manage syllabus' : 'Add syllabus'}</Link><Link to="/concepts">Concept map</Link><Link to="/exams">Question papers</Link></div>
      </article>)}</div>
      {!loading && !courses.length && <p className="empty-state">No subjects yet. Use the form above to create a private subject workspace, or add approved records from the verified RVCE catalog.</p>}
    </section>
  </main>
}
