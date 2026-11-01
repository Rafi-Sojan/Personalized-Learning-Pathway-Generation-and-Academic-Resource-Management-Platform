import { useCallback } from 'react'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useAsync } from '../hooks/useAsync'
import { getProgress } from '../services/progress'
import { getLocalDayKey } from '../utils/activity'

/** Summarize learner completion and visualize the current weekly mastery trend. */
export function Progress() {
  const { data, loading } = useAsync(useCallback(() => getProgress(), []), { completed_concepts: 0, total_concepts: 0, updates: {}, activity_timestamps: [] })
  const percent = data.total_concepts ? Math.round((data.completed_concepts / data.total_concepts) * 100) : 0
  const activeDays = new Set(data.activity_timestamps.map((timestamp) => getLocalDayKey(new Date(timestamp))))
  const chart = Array.from({ length: 7 }, (_, index) => {
    const day = new Date()
    day.setDate(day.getDate() - 6 + index)
    return { day: new Intl.DateTimeFormat(undefined, { weekday: 'short' }).format(day), studied: activeDays.has(getLocalDayKey(day)) ? 1 : 0 }
  })
  const studyDaysThisWeek = chart.filter((item) => item.studied).length
  return <main><div className="eyebrow">Momentum over perfection</div><h1>Progress</h1><p className="lede">Review your completed concepts and recorded study activity.</p><div className="progress-hero"><div className="ring"><strong>{percent}%</strong><span>complete</span></div><div><span className="section-kicker">Overall mastery</span><h2>{data.completed_concepts} of {data.total_concepts} concepts</h2><p>Your next session is already waiting in the roadmap.</p></div></div><div className="panel chart-panel"><div className="panel-heading"><h2>Study activity</h2><span className="section-kicker">{studyDaysThisWeek} of 7 days this week</span></div><ResponsiveContainer width="100%" height={220}><AreaChart data={chart}><XAxis dataKey="day" /><YAxis domain={[0, 1]} ticks={[0, 1]} tickFormatter={(value) => value ? 'Active' : 'No activity'} /><Tooltip formatter={(value) => [value ? 'Recorded activity' : 'No activity', 'Study day']} /><Area type="stepAfter" dataKey="studied" stroke="#3c7d70" fill="#d8eee3" /></AreaChart></ResponsiveContainer></div>{loading ? <p>Loading progress…</p> : <div className="panel"><div className="panel-heading"><h2>Recent activity</h2></div><p>{Object.keys(data.updates).length ? `You have ${Object.keys(data.updates).length} concepts with recorded progress.` : 'Complete a concept or quiz to start your activity history.'}</p></div>}</main>
}
