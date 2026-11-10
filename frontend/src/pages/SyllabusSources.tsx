import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getCourses } from '../services/courses'
import { generateConceptMap, getSyllabusRecords, getSyllabusRoadmapProfile, getSyllabusSources, processSyllabusSource, reviewSyllabusRecord, reviewSyllabusRoadmapProfile, uploadSyllabusSource, type SyllabusRecord } from '../services/syllabus'
import type { Course, Resource, RoadmapProfile, SyllabusRoadmapProfile } from '../types'

/** Store course syllabus copies, extract their topics, and create roadmap concepts. */
export function SyllabusSources() {
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedCourseId = searchParams.get('course_id') ?? ''
  const [courses, setCourses] = useState<Course[]>([])
  const [courseId, setCourseId] = useState('')
  const [sources, setSources] = useState<Resource[]>([])
  const [records, setRecords] = useState<SyllabusRecord[]>([])
  const [roadmapProfile, setRoadmapProfile] = useState<SyllabusRoadmapProfile | null>(null)
  const [profileType, setProfileType] = useState('theory')
  const [profileHours, setProfileHours] = useState({ lecture: 0, tutorial: 0, practical: 0, experiential: 0 })
  const [profileUnitHours, setProfileUnitHours] = useState<Record<string, number>>({})
  const [profileScopes, setProfileScopes] = useState<Record<string, 'both' | 'cie_only' | 'see_only'>>({})
  const [profileNotes, setProfileNotes] = useState('')
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
      setRoadmapProfile(null)
      return
    }
    try {
      setError('')
      const [sourceItems, recordItems, profile] = await Promise.all([getSyllabusSources(courseId), getSyllabusRecords(courseId), getSyllabusRoadmapProfile(courseId)])
      setSources(sourceItems)
      setRecords(recordItems)
      setRoadmapProfile(profile)
      if (profile.available) {
        const data = profile.profile as RoadmapProfile
        setProfileType(data.course_type)
        setProfileHours(data.modality_hours)
        setProfileUnitHours(Object.fromEntries(data.units.map((unit) => [unit.label, unit.hours ?? 0])))
        setProfileScopes(Object.fromEntries(data.units.map((unit) => [unit.label, unit.assessment_scope])))
        setProfileNotes(profile.review_notes)
      }
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
      await refreshSources()
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

  /** Verify, reject, or correct the extracted workload profile that controls roadmap activities. */
  async function reviewProfile(status: 'verified' | 'rejected') {
    if (!roadmapProfile?.syllabus_version_id) return
    setBusyId('profile')
    setError('')
    try {
      const updated = await reviewSyllabusRoadmapProfile(roadmapProfile.syllabus_version_id, {
        status,
        course_type: profileType,
        lecture_hours: profileHours.lecture,
        tutorial_hours: profileHours.tutorial,
        practical_hours: profileHours.practical,
        experiential_hours: profileHours.experiential,
        unit_hours: profileUnitHours,
        unit_assessment_scopes: profileScopes,
        review_notes: profileNotes,
      })
      setRoadmapProfile(updated)
      setMessage(status === 'verified' ? 'Course roadmap profile verified. Its reviewed workload and activity type can now control persisted plans.' : 'Course roadmap profile rejected. Correct and verify it before generating a persisted plan.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to review roadmap profile')
    } finally {
      setBusyId('')
    }
  }

  const profileData = roadmapProfile?.available ? roadmapProfile.profile as RoadmapProfile : null

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
    {profileData && <section className="panel roadmap-profile-panel">
      <div className="panel-heading"><div><span className="section-kicker">Reviewed planning contract</span><h2>Course roadmap profile</h2></div><span className={`scope-badge ${roadmapProfile?.status === 'verified' ? 'verified' : ''}`}>{roadmapProfile?.status.replace(/_/g, ' ')}</span></div>
      <p className="mapping-status">Confirm the extracted activity type, workload, unit order, and assessment scope. Source warnings remain visible even after a reviewer records a decision.</p>
      <div className="profile-facts"><span>Codes: {profileData.course_codes.join(' / ') || 'not detected'}</span><span>Category: {profileData.category ?? 'not detected'}</span><span>L:T:P credits: {profileData.credit_allocation.lecture}:{profileData.credit_allocation.tutorial}:{profileData.credit_allocation.practical}</span><span>Assessment: {profileData.assessment_format.replace(/_/g, ' ')}</span><span>CIE / SEE marks: {profileData.cie_marks ?? '—'} / {profileData.see_marks ?? '—'}</span><span>Components: {profileData.assessment_components.join(', ').replace(/_/g, ' ') || 'not detected'}</span></div>
      {profileData.course_outcomes.length > 0 && <details className="profile-outcomes"><summary>{profileData.course_outcomes.length} extracted course outcome{profileData.course_outcomes.length === 1 ? '' : 's'}</summary><ul>{profileData.course_outcomes.map((outcome) => <li key={outcome}>{outcome}</li>)}</ul></details>}
      {profileData.issues.length > 0 && <div className="profile-warning" role="status"><strong>Source checks requiring review</strong><ul>{profileData.issues.map((issue) => <li key={issue}>{issue}</li>)}</ul></div>}
      <div className="form-grid">
        <label>Activity model<select value={profileType} onChange={(event) => setProfileType(event.target.value)}>
          {['theory', 'numerical_theory', 'theory_lab', 'programming', 'project', 'cad', 'language', 'objective_hss', 'health_practice', 'generic'].map((value) => <option key={value} value={value}>{value.replace(/_/g, ' ')}</option>)}
        </select></label>
        {(['lecture', 'tutorial', 'practical', 'experiential'] as const).map((modality) => <label key={modality}>{modality[0].toUpperCase() + modality.slice(1)} hours<input type="number" min="0" max="1000" step="0.5" value={profileHours[modality]} onChange={(event) => setProfileHours((current) => ({ ...current, [modality]: Number(event.target.value) }))} /></label>)}
        <label className="full-field">Review notes<textarea rows={3} maxLength={2000} value={profileNotes} onChange={(event) => setProfileNotes(event.target.value)} placeholder="Record corrections or the source used to resolve discrepancies." /></label>
      </div>
      <div className="profile-unit-list">{profileData.units.map((unit) => <div key={`${unit.sequence}-${unit.label}`}><span>Unit {unit.label} · {unit.title || 'Untitled'}{unit.source_page ? ` · p.${unit.source_page}` : ''}</span><label>Hours<input aria-label={`Hours for unit ${unit.label}`} type="number" min="0" max="1000" step="0.5" value={profileUnitHours[unit.label] ?? unit.hours ?? 0} onChange={(event) => setProfileUnitHours((current) => ({ ...current, [unit.label]: Number(event.target.value) }))} /></label><label>Assessment<select aria-label={`Assessment scope for unit ${unit.label}`} value={profileScopes[unit.label] ?? unit.assessment_scope} onChange={(event) => setProfileScopes((current) => ({ ...current, [unit.label]: event.target.value as 'both' | 'cie_only' | 'see_only' }))}><option value="both">CIE and SEE</option><option value="cie_only">CIE only</option><option value="see_only">SEE only</option></select></label></div>)}</div>
      <div className="action-row"><button className="primary" type="button" disabled={Boolean(busyId)} onClick={() => void reviewProfile('verified')}>Verify profile</button><button className="secondary" type="button" disabled={Boolean(busyId)} onClick={() => void reviewProfile('rejected')}>Reject profile</button></div>
    </section>}
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
