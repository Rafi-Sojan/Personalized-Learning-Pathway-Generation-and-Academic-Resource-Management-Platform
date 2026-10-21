import { useCallback } from 'react'
import { BookOpen, Clock3, Sparkles, Target } from 'lucide-react'
import { StatCard } from '../components/common/StatCard'
import { RoadmapList } from '../components/roadmap/RoadmapList'
import { useAsync } from '../hooks/useAsync'
import { getCourses } from '../services/courses'
import { getProgress } from '../services/progress'
import { getRoadmap } from '../services/roadmap'

export function Dashboard() {
  const courses = useAsync(useCallback(() => getCourses(), []), [])
  const progress = useAsync(useCallback(() => getProgress(), []), { completed_concepts: 0, total_concepts: 1, updates: {} })
  const roadmap = useAsync(useCallback(() => getRoadmap(), []), [])
  const completion = Math.round((progress.data.completed_concepts / Math.max(progress.data.total_concepts, 1)) * 100)
  return <main>
    <div className="eyebrow">Wednesday, October 21, 2026 <span>•</span> Week 04</div>
    <div className="hero-row"><div><h1>Good morning, learner.</h1><p className="lede">Your next breakthrough is closer than you think.</p></div><button className="primary"><Sparkles size={16} /> Generate plan</button></div>
    <section className="stats-grid"><StatCard label="Overall progress" value={`${completion}%`} detail="Keep your streak moving" /><StatCard label="Study time" value="4h 20m" detail="+38% from last week" tone="warm" /><StatCard label="Topics mastered" value={`${progress.data.completed_concepts}`} detail={`of ${progress.data.total_concepts} concepts`} tone="cool" /><StatCard label="Current streak" value="6 days" detail="Best: 12 days" /></section>
    <section className="dashboard-grid"><div className="panel large"><div className="panel-heading"><div><span className="section-kicker">Your focus</span><h2>Today’s roadmap</h2></div><a href="#roadmap">View full plan →</a></div>{roadmap.loading ? <p>Loading your plan…</p> : <RoadmapList items={roadmap.data.slice(0, 3)} />}</div><div className="panel"><div className="panel-heading"><div><span className="section-kicker">Active learning</span><h2>My courses</h2></div><BookOpen size={20} /></div>{courses.loading ? <p>Loading courses…</p> : courses.data.map((course) => <div className="course-mini" key={course.id}><div className="course-icon">{course.code.slice(0, 2)}</div><div className="course-copy"><strong>{course.title}</strong><small>{course.code} · {course.progress}% complete</small><div className="progress"><i style={{ width: `${course.progress}%` }} /></div></div></div>)}</div></section>
    <section className="quote-card"><Target size={24} /><div><strong>Small steps compound.</strong><p>Focus on one concept today. Your roadmap has already accounted for prerequisites and your available time.</p></div><Clock3 size={20} /></section>
  </main>
}
