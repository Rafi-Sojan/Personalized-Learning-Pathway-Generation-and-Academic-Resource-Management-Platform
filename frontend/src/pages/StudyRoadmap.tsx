import { type FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAsync } from '../hooks/useAsync'
import { getCourses } from '../services/courses'
import { generateRoadmap, generateSemesterRoadmap, getActiveRoadmap, updateRoadmapItem, type RoadmapConstraints, type RoadmapMode } from '../services/roadmap'
import { RoadmapList } from '../components/roadmap/RoadmapList'
import type { Course, RoadmapItem } from '../types'

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

/** Build a stable branch/scheme/semester key only for fully scoped subjects. */
function courseScopeKey(course: Course) {
  if (!course.program_code || !course.scheme_year || !course.semester) return ''
  return `${course.program_code}|${course.scheme_year}|${course.semester}`
}

/** Render an academic scope without suggesting that personal subjects are catalog-verified. */
function courseScopeLabel(course: Course) {
  return `${course.program_code} · ${course.scheme_year} scheme · Semester ${course.semester}`
}

/** Generate reviewed course or semester roadmaps and capture session-level mastery feedback. */
export function StudyRoadmap() {
  const courses = useAsync(useCallback(() => getCourses(), []), [])
  const today = new Date().toISOString().slice(0, 10)
  const initialDate = new Date(Date.now() + 45 * 86400000).toISOString().slice(0, 10)
  const [scopeType, setScopeType] = useState<'course' | 'semester'>('course')
  const [courseId, setCourseId] = useState('')
  const [academicScope, setAcademicScope] = useState('')
  const [selectedCourseIds, setSelectedCourseIds] = useState<string[]>([])
  const [mode, setMode] = useState<RoadmapMode>('full_term')
  const [startDate, setStartDate] = useState(today)
  const [targetDate, setTargetDate] = useState(initialDate)
  const [dailyMinutes, setDailyMinutes] = useState(180)
  const [revisionMinutes, setRevisionMinutes] = useState(60)
  const [unavailableWeekdays, setUnavailableWeekdays] = useState<number[]>([])
  const [items, setItems] = useState<RoadmapItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  const scopeGroups = useMemo(() => {
    const groups = new Map<string, Course[]>()
    for (const course of courses.data) {
      const key = courseScopeKey(course)
      if (key) groups.set(key, [...(groups.get(key) ?? []), course])
    }
    return [...groups.entries()]
  }, [courses.data])

  const scopedCourses = useMemo(() => scopeGroups.find(([key]) => key === academicScope)?.[1] ?? [], [academicScope, scopeGroups])

  /** Initialize selections after the authenticated course list becomes available. */
  useEffect(() => {
    if (!courseId && courses.data[0]) setCourseId(courses.data[0].id)
    if (!academicScope && scopeGroups[0]) {
      setAcademicScope(scopeGroups[0][0])
      setSelectedCourseIds([])
    }
  }, [academicScope, courseId, courses.data, scopeGroups])

  /** Restore the newest persisted plan so navigation does not discard session state. */
  useEffect(() => {
    let active = true
    getActiveRoadmap().then((plan) => {
      if (!active || !plan) return
      setScopeType(plan.scope_type)
      setMode(plan.mode)
      setStartDate(plan.start_date)
      setTargetDate(plan.target_date)
      setDailyMinutes(plan.daily_minutes)
      setRevisionMinutes(plan.revision_minutes)
      setUnavailableWeekdays(plan.unavailable_weekdays)
      setItems(plan.items)
      if (plan.course_id) setCourseId(plan.course_id)
      if (plan.scope_type === 'semester') {
        setAcademicScope(`${plan.program_code}|${plan.scheme_year}|${plan.semester}`)
        setSelectedCourseIds([...new Set(plan.items.map((item) => item.course_id))])
      }
      setMessage('Loaded your latest active roadmap and saved session progress.')
    }).catch((reason) => {
      if (active) setError(reason instanceof Error ? reason.message : 'Unable to load the active roadmap')
    })
    return () => { active = false }
  }, [])

  /** Replace semester selections when the learner changes academic scope. */
  function selectAcademicScope(value: string) {
    setAcademicScope(value)
    setSelectedCourseIds([])
  }

  /** Toggle one explicit semester subject without inferring placeholder options. */
  function toggleCourse(value: string) {
    setSelectedCourseIds((current) => current.includes(value) ? current.filter((id) => id !== value) : [...current, value])
  }

  /** Toggle one weekday exclusion used by inclusive capacity calculations. */
  function toggleWeekday(value: number) {
    setUnavailableWeekdays((current) => current.includes(value) ? current.filter((day) => day !== value) : [...current, value].sort())
  }

  /** Validate selection and persist an activity-aware course or semester plan. */
  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setMessage('')
    const constraints: RoadmapConstraints = {
      start_date: startDate,
      target_date: targetDate,
      daily_minutes: dailyMinutes,
      revision_minutes: revisionMinutes,
      mode,
      unavailable_weekdays: unavailableWeekdays,
    }
    try {
      if (scopeType === 'course') {
        const selectedCourse = courseId || courses.data[0]?.id
        if (!selectedCourse) throw new Error('Create a subject before generating a roadmap.')
        const result = await generateRoadmap(selectedCourse, constraints)
        setItems(result.items)
      } else {
        if (!selectedCourseIds.length) throw new Error('Select at least one subject in this semester.')
        const result = await generateSemesterRoadmap(selectedCourseIds, constraints)
        setItems(result.items)
      }
      setMessage('Plan generated from verified syllabus topics and reviewed course profiles.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to generate roadmap')
    } finally {
      setBusy(false)
    }
  }

  /** Update one stored session and retain valid completion mastery in the displayed plan. */
  async function updateItem(item: RoadmapItem, status: 'planned' | 'completed' | 'skipped', masteryScore?: number) {
    setError(null)
    try {
      await updateRoadmapItem(item.id, status, masteryScore)
      setItems((current) => current.map((candidate) => candidate.id === item.id ? { ...candidate, status } : candidate))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to update roadmap session')
    }
  }

  const selectedCourse = courses.data.find((course) => course.id === courseId)
  const totalMinutes = items.reduce((total, item) => total + item.minutes, 0)

  return <main>
    <div className="eyebrow">Personalized schedule</div>
    <h1>Study roadmap</h1>
    <p className="lede">Generate one source-ordered subject plan or balance explicitly selected subjects across a semester. Reviewed Part B evidence prioritizes deep practice; Part A evidence supplies retrieval work.</p>
    <section className="roadmap-controls panel">
      <form onSubmit={submit}>
        <label>Plan scope<select value={scopeType} onChange={(event) => setScopeType(event.target.value as 'course' | 'semester')}><option value="course">One subject</option><option value="semester">Semester subjects</option></select></label>
        {scopeType === 'course' ? <label>Subject<select value={courseId || courses.data[0]?.id || ''} onChange={(event) => setCourseId(event.target.value)}>{courses.data.map((course) => <option value={course.id} key={course.id}>{course.code} · {course.title}</option>)}</select></label> : <label>Academic scope<select value={academicScope} onChange={(event) => selectAcademicScope(event.target.value)}>{scopeGroups.map(([key, values]) => <option value={key} key={key}>{courseScopeLabel(values[0])}</option>)}</select></label>}
        <label>Plan mode<select value={mode} onChange={(event) => setMode(event.target.value as RoadmapMode)}><option value="full_term">Full term</option><option value="cie">CIE preparation</option><option value="see">SEE preparation</option><option value="revision">Revision</option></select></label>
        <label>Start date<input type="date" value={startDate} min={today} max={targetDate} onChange={(event) => setStartDate(event.target.value)} required /></label>
        <label>Target date<input type="date" value={targetDate} min={startDate} onChange={(event) => setTargetDate(event.target.value)} required /></label>
        <label>Daily study minutes<input type="number" min="15" max="1440" value={dailyMinutes} onChange={(event) => setDailyMinutes(Number(event.target.value))} required /></label>
        <label>Reserved revision minutes<input type="number" min="0" max="1440" value={revisionMinutes} onChange={(event) => setRevisionMinutes(Number(event.target.value))} required /></label>
        <button className="primary" disabled={busy}>{busy ? 'Generating…' : 'Generate plan'}</button>
      </form>
      {scopeType === 'semester' && <fieldset className="course-selector"><legend>Included subjects</legend>{scopedCourses.map((course) => <label key={course.id}><input type="checkbox" checked={selectedCourseIds.includes(course.id)} onChange={() => toggleCourse(course.id)} />{course.code} · {course.title}</label>)}</fieldset>}
      <fieldset className="weekday-selector"><legend>Unavailable days</legend>{WEEKDAYS.map((weekday, index) => <label key={weekday}><input type="checkbox" checked={unavailableWeekdays.includes(index)} onChange={() => toggleWeekday(index)} />{weekday.slice(0, 3)}</label>)}</fieldset>
      {selectedCourse && scopeType === 'course' && <p className="mapping-status">{courseScopeKey(selectedCourse) ? courseScopeLabel(selectedCourse) : 'Legacy subject without an academic scope'} · {selectedCourse.concept_count} mapped topics</p>}
      {message && <p role="status" className="mapping-status">{message}</p>}
      {error && <div className="form-error" role="alert">{error} {error.toLowerCase().includes('profile') && scopeType === 'course' && courseId && <Link to={`/syllabus?course_id=${encodeURIComponent(courseId)}`}>Review syllabus profile</Link>}</div>}
    </section>
    <section className="panel">
      <div className="panel-heading"><div><span className="section-kicker">Next plan</span><h2>{items.length ? `${items.length} scheduled sessions` : 'Your plan'}</h2></div><span className="section-kicker">{items.length ? `${Math.round(totalMinutes / 60 * 10) / 10} hours` : targetDate}</span></div>
      {items.length ? <RoadmapList items={items} onUpdate={updateItem} /> : <p>Generate a plan to see source-linked learning, practice, project, laboratory, and revision sessions.</p>}
    </section>
  </main>
}
