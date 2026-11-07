import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getCourses } from '../services/courses'
import { generateConceptMap, getSyllabusRecords, getSyllabusSources, processSyllabusSource, reviewSyllabusRecord, uploadSyllabusSource, type SyllabusRecord } from '../services/syllabus'
import type { Course, Resource } from '../types'

/** Store course syllabus copies, extract their topics, and create roadmap concepts. */
export function SyllabusSources() {
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedCourseId = searchParams.get('course_id') ?? ''
  const [courses, setCourses] = useState<Course[]>([])
  const [courseId, setCourseId] = useState('')
  const [sources, setSources] = useState<Resource[]>([])
  const [records, setRecords] = useState<SyllabusRecord[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [busyId, setBusyId] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  /** Load learner courses and honor a subject deep link when it belongs to the caller. */
  useEffect(() => {
    getCourses().then((items) => {
      setCourses(items)
      const nextCourseId = items.some((item) => item.id === requestedCourseId) ? requestedCourseId : items[0]?.id ?? ''
      setCourseId(nextCourseId)
      if (nextCourseId && nextCourseId !== requestedCourseId) setSearchParams({ course_id: nextCourseId }, { replace: true })
    }).catch((reason) => setError(reason instanceof Error ? reason.message : 'Unable to load courses'))
  }, [requestedCourseId, setSearchParams])

  /** Change the active course and preserve it in the URL for direct navigation. */
  function selectCourse(nextCourseId: string) {
    setCourseId(nextCourseId)
    setSearchParams(nextCourseId ? { course_id: nextCourseId } : {}, { replace: true })
  }

  /** Refresh stored syllabus copies when the learner changes the course. */
  const refreshSources = useCallback(async () => {
    if (!courseId) {
      setSources([])
      return
    }
    try {
      setError('')
      setSources(await getSyllabusSources(courseId))
      setRecords(await getSyllabusRecords(courseId))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load syllabus copies')
    }
  }, [courseId])

  /** Keep the document list aligned with the selected course. */
  useEffect(() => { void refreshSources() }, [refreshSources])

  /** Upload the selected PDF as an owned syllabus source for the active course. */
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file || !courseId) return
    setBusyId('upload')
    setError('')
    setMessage('')
    try {
      await uploadSyllabusSource(courseId, file)
      setFile(null)
      setMessage('Syllabus copy stored. Start extraction to read its topics.')
      await refreshSources()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to upload syllabus copy')
    } finally {
      setBusyId('')
    }
  }

  /** Start PDF text extraction and refresh the row after processing returns. */
  async function processSource(source: Resource) {
    setBusyId(source.id)
    setError('')
    setMessage('')
    try {
      await processSyllabusSource(source.id)
      setMessage('Text extraction finished or was queued. Refresh the status if it is still processing.')
      await refreshSources()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to process syllabus PDF')
    } finally {
      setBusyId('')
    }
  }

  /** Generate concepts from extracted topics and report the number added or reused. */
  async function createMap(source: Resource) {
    setBusyId(source.id)
    setError('')
    setMessage('')
    try {
      const result = await generateConceptMap(source.id)
      setMessage(`Found ${result.topics_found} syllabus topics; added ${result.concepts_added} concepts and reused ${result.concepts_reused}. Verify the extracted topic records below before they influence frequency or roadmaps.`)
      setRecords(await getSyllabusRecords(courseId))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to generate concepts')
    } finally {
      setBusyId('')
    }
  }

  /** Record a human decision for a parsed syllabus topic and refresh its status. */
  async function reviewRecord(record: SyllabusRecord, status: 'verified' | 'rejected') {
    try {
      await reviewSyllabusRecord(record.id, status)
      setRecords(await getSyllabusRecords(courseId))
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to review syllabus record') }
  }

  /** Reload extraction lifecycle states for the selected course. */
  async function refreshStatus() {
    await refreshSources()
  }

  return <main>
    <div className="eyebrow">Syllabus-driven learning</div>
    <h1>Syllabus copies</h1>
      <p className="lede">Store the matching course PDF, extract its unit hierarchy, and verify topics before they influence the concept map, question frequency, or study roadmap.</p>
    <section className="panel">
      <div className="panel-heading"><div><span className="section-kicker">Source document</span><h2>Add a syllabus PDF</h2></div></div>
      <form className="form-grid" onSubmit={upload}>
        <label>Subject<select required value={courseId} onChange={(event) => selectCourse(event.target.value)}>
          {courses.map((course) => <option key={course.id} value={course.id}>{course.code} · {course.title}{course.program_code && course.scheme_year && course.semester ? ` · ${course.program_code}/${course.scheme_year}/S${course.semester}` : ''}</option>)}
        </select></label>
        <label>PDF copy<input required type="file" accept="application/pdf,.pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
        <button className="primary" type="submit" disabled={!courseId || !file || Boolean(busyId)}>{busyId === 'upload' ? 'Uploading…' : 'Store syllabus copy'}</button>
      </form>
      {!courses.length && <p className="empty-state">Create a subject before uploading its syllabus. <Link to="/courses">Add a subject</Link></p>}
    </section>
    {records.length > 0 && <section className="panel">
      <div className="panel-heading"><div><span className="section-kicker">Source-backed extraction</span><h2>{records.length} syllabus records</h2></div><span className="section-kicker">Versioned · page-linked</span></div>
      <div className="exam-frequency-list">{records.map((record) => <article className="roadmap-row" key={record.id}>
        <span className="roadmap-number">{record.source_page ? `p.${record.source_page}` : '—'}</span>
        <div><strong>{record.source_text}</strong><p>{record.record_type} · {record.unit_label ?? 'Unit not identified'}{record.parent_label ? ` · under ${record.parent_label}` : ''}{record.hours !== null ? ` · ${record.hours} hours` : ''} · confidence {Math.round(record.confidence * 100)}% · {record.review_status} · version {record.syllabus_version_id.slice(0, 8)}</p>
          {record.review_status === 'pending_review' && <><button className="secondary" type="button" onClick={() => void reviewRecord(record, 'verified')}>Verify record</button> <button className="secondary" type="button" onClick={() => void reviewRecord(record, 'rejected')}>Reject</button></>}</div>
      </article>)}</div>
    </section>}
    <section className="panel">
      <div className="panel-heading"><div><span className="section-kicker">Stored source copies</span><h2>{sources.length} syllabus PDF{sources.length === 1 ? '' : 's'}</h2></div><button className="secondary" type="button" onClick={() => void refreshStatus()} disabled={!courseId}>Refresh status</button></div>
      {sources.length ? <div className="resource-grid">{sources.map((source) => <article className="resource-card" key={source.id}>
        <span>SYLLABUS · {source.processing_status ?? 'uploaded'}</span>
        <h3>{source.title}</h3>
        {source.processing_error && <p className="form-error">{source.processing_error}</p>}
        <div className="form-grid">
          <button className="secondary" type="button" disabled={Boolean(busyId) || ['queued', 'processing'].includes(source.processing_status ?? '')} onClick={() => void processSource(source)}>{busyId === source.id ? 'Working…' : source.processing_status === 'processed' ? 'Re-extract text' : 'Extract syllabus topics'}</button>
          <button className="primary" type="button" disabled={Boolean(busyId) || source.processing_status !== 'processed'} onClick={() => void createMap(source)}>Generate concept map</button>
        </div>
      </article>)}</div> : <p className="empty-state">Upload a syllabus PDF to start building the course concept map.</p>}
    </section>
    {message && <p role="status">{message}</p>}
    {error && <p className="form-error" role="alert">{error}</p>}
  </main>
}
