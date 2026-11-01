import { useCallback } from 'react'
import { BookOpen, Clock3, Sparkles, Target } from 'lucide-react'
import { Link } from 'react-router-dom'
import { StatCard } from '../components/common/StatCard'
import { RoadmapList } from '../components/roadmap/RoadmapList'
import { useAsync } from '../hooks/useAsync'
import { getCourses } from '../services/courses'
import { getProgress } from '../services/progress'
import { getRoadmap } from '../services/roadmap'
import { calculateCurrentStreak } from '../utils/activity'

/** Combine course, progress, and roadmap summaries into the learner home screen. */
export function Dashboard() {
  const courses = useAsync(useCallback(() => getCourses(), []), [])
  const progress = useAsync(useCallback(() => getProgress(), []), { completed_concepts: 0, total_concepts: 0, updates: {}, activity_timestamps: [] })
  const roadmap = useAsync(useCallback(() => getRoadmap(), []), [])
  const completion = progress.data.total_concepts
    ? Math.round((progress.data.completed_concepts / progress.data.total_concepts) * 100)
    : 0
  const streak = calculateCurrentStreak(progress.data.activity_timestamps)
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  const storedUser = localStorage.getItem('user')
  const firstName = storedUser ? (JSON.parse(storedUser) as { name?: string }).name?.trim().split(/\s+/)[0] || 'learner' : 'learner'
  const today = new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date())
  return <main>
    <div className="eyebrow">{today}</div>
    <div className="hero-row"><div><h1>{greeting}, {firstName}.</h1><p className="lede">Pick up where your learning plan left off.</p></div><Link className="primary" to="/roadmap"><Sparkles size={16} /> Generate plan</Link></div>
    <section className="stats-grid"><StatCard label="Overall progress" value={`${completion}%`} detail="Concepts completed" /><StatCard label="Active courses" value={`${courses.data.length}`} detail="In your learning space" tone="warm" /><StatCard label="Topics mastered" value={`${progress.data.completed_concepts}`} detail={`of ${progress.data.total_concepts} concepts`} tone="cool" /><StatCard label="Current streak" value={streak >= 400 ? '400+ days' : `${streak} ${streak === 1 ? 'day' : 'days'}`} detail="Based on recorded study activity" /></section>
    {(courses.error || progress.error || roadmap.error) && <p className="form-error" role="alert">{courses.error || progress.error || roadmap.error}</p>}
    <section className="dashboard-grid"><div className="panel large"><div className="panel-heading"><div><span className="section-kicker">Your focus</span><h2>Upcoming roadmap</h2></div><Link to="/roadmap">View full plan →</Link></div>{roadmap.loading ? <p aria-live="polite">Loading your plan…</p> : roadmap.data.length ? <RoadmapList items={roadmap.data.slice(0, 3)} /> : <p className="empty-state">No roadmap yet. <Link to="/roadmap">Create a study plan</Link> to see your next steps here.</p>}</div><div className="panel"><div className="panel-heading"><div><span className="section-kicker">Active learning</span><h2>My courses</h2></div><BookOpen size={20} /></div>{courses.loading ? <p aria-live="polite">Loading courses…</p> : courses.data.length ? courses.data.map((course) => <div className="course-mini" key={course.id}><div className="course-icon">{course.code.slice(0, 2)}</div><div className="course-copy"><strong>{course.title}</strong><small>{course.code} · {course.progress}% complete</small><div className="progress"><i style={{ width: `${course.progress}%` }} /></div></div></div>) : <p className="empty-state">No courses yet. <Link to="/courses">Add a course</Link> or choose one from the RVCE catalog.</p>}</div></section>
    <section className="quote-card"><Target size={24} /><div><strong>{roadmap.data[0] ? `Next up: ${roadmap.data[0].concept_name}` : 'Build a plan that fits your goal.'}</strong><p>{roadmap.data[0]?.reason ?? 'Choose a target date and daily study time to create your first roadmap.'}</p></div><Link to="/roadmap" aria-label="Open study roadmap"><Clock3 size={20} /></Link></section>
  </main>
}
