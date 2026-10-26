import { FormEvent, useCallback, useState } from 'react'
import { useAsync } from '../hooks/useAsync'
import { getCourses } from '../services/courses'
import { generateRoadmap, getRoadmap } from '../services/roadmap'
import { RoadmapList } from '../components/roadmap/RoadmapList'

export function StudyRoadmap() {
  const courses = useAsync(useCallback(() => getCourses(), []), [])
  const initialDate = new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10)
  const [courseId, setCourseId] = useState('')
  const [targetDate, setTargetDate] = useState(initialDate)
  const [dailyMinutes, setDailyMinutes] = useState(60)
  const [items, setItems] = useState<Awaited<ReturnType<typeof getRoadmap>>>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(null)
    try {
      const selectedCourse = courseId || courses.data[0]?.id
      if (!selectedCourse) throw new Error('Create a course before generating a roadmap.')
      const result = await generateRoadmap(selectedCourse, targetDate, dailyMinutes)
      setItems(result.items)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to generate roadmap') } finally { setBusy(false) }
  }

  return <main><div className="eyebrow">Personalized schedule</div><h1>Study roadmap</h1><p className="lede">Set your target and capacity. The scheduler will preserve prerequisites and explain the order.</p><div className="roadmap-controls panel"><form onSubmit={submit}><label>Course<select value={courseId || courses.data[0]?.id || ''} onChange={(event) => setCourseId(event.target.value)}>{courses.data.map((course) => <option value={course.id} key={course.id}>{course.code} · {course.title}</option>)}</select></label><label>Target date<input type="date" value={targetDate} min={new Date().toISOString().slice(0, 10)} onChange={(event) => setTargetDate(event.target.value)} required /></label><label>Daily study minutes<input type="number" min="15" max="1440" value={dailyMinutes} onChange={(event) => setDailyMinutes(Number(event.target.value))} required /></label><button className="primary" disabled={busy}>{busy ? 'Generating…' : 'Generate plan'}</button></form>{error && <div className="form-error">{error}</div>}</div><div className="panel"><div className="panel-heading"><div><span className="section-kicker">Next plan</span><h2>{items.length ? `${items.length} concepts scheduled` : 'Your plan'}</h2></div><span className="section-kicker">{targetDate}</span></div>{items.length ? <RoadmapList items={items} /> : <p>Generate a plan to see your dated learning sessions.</p>}</div></main>
}
