import { useCallback } from 'react'
import { BookOpen, BrainCircuit, Route, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import { StatCard } from '../components/common/StatCard'
import { RoadmapList } from '../components/roadmap/RoadmapList'
import { useAsync } from '../hooks/useAsync'
import { getConcepts } from '../services/concepts'
import { getCourses } from '../services/courses'
import { getRoadmap } from '../services/roadmap'

/** Summarize the learner's syllabus mapping and upcoming roadmap without progress tracking. */
export function Dashboard() {
  const courses = useAsync(useCallback(() => getCourses(), []), [])
  const concepts = useAsync(useCallback(() => getConcepts(), []), [])
  const roadmap = useAsync(useCallback(() => courses.data[0] ? getRoadmap(courses.data[0].id) : Promise.resolve([]), [courses.data]), [])
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  const storedUser = localStorage.getItem('user')
  const firstName = storedUser ? (JSON.parse(storedUser) as { name?: string }).name?.trim().split(/\s+/)[0] || 'learner' : 'learner'
  const today = new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date())
  return <main>
    <div className="eyebrow">{today}</div>
    <div className="hero-row"><div><h1>{greeting}, {firstName}.</h1><p className="lede">Map your RVCE syllabus, then build a focused study plan.</p></div><Link className="primary" to="/syllabus"><Sparkles size={16} /> Open syllabus copies</Link></div>
    <section className="stats-grid"><StatCard label="Subjects" value={`${courses.data.length}`} detail="In your learning space" tone="warm" /><StatCard label="Mapped topics" value={`${concepts.data.length}`} detail="Linked to syllabus copies" tone="cool" /><StatCard label="Upcoming topics" value={`${roadmap.data.length}`} detail="In your study roadmap" /></section>
    {(courses.error || concepts.error || roadmap.error) && <p className="form-error" role="alert">{courses.error || concepts.error || roadmap.error}</p>}
    <section className="dashboard-grid"><div className="panel large"><div className="panel-heading"><div><span className="section-kicker">Your focus</span><h2>Upcoming roadmap</h2></div><Link to="/roadmap">View full plan →</Link></div>{roadmap.loading ? <p aria-live="polite">Loading your plan…</p> : roadmap.data.length ? <RoadmapList items={roadmap.data.slice(0, 3)} /> : <p className="empty-state">No roadmap yet. <Link to="/roadmap">Create a study plan</Link> after mapping a syllabus copy.</p>}</div><div className="panel"><div className="panel-heading"><div><span className="section-kicker">Your subjects</span><h2>My courses</h2></div><BookOpen size={20} /></div>{courses.loading ? <p aria-live="polite">Loading subjects…</p> : courses.data.length ? courses.data.map((course) => <div className="course-mini" key={course.id}><div className="course-icon">{course.code.slice(0, 2)}</div><div className="course-copy"><strong>{course.title}</strong><small>{course.code} · {course.concept_count} mapped topics</small></div></div>) : <p className="empty-state">No subjects yet. <Link to="/courses">Add a subject</Link> or choose one from the RVCE catalog.</p>}</div></section>
    <section className="quote-card"><BrainCircuit size={24} /><div><strong>Check every mapped topic against its syllabus source.</strong><p>The concept map records its unit and printed page when they can be identified.</p></div><Link to="/concepts" aria-label="Open concept map"><Route size={20} /></Link></section>
  </main>
}
