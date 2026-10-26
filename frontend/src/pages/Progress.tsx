import { useCallback } from 'react'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useAsync } from '../hooks/useAsync'
import { getProgress } from '../services/progress'

export function Progress() {
  const { data, loading } = useAsync(useCallback(() => getProgress(), []), { completed_concepts: 0, total_concepts: 1, updates: {} })
  const percent = Math.round((data.completed_concepts / Math.max(data.total_concepts, 1)) * 100)
  const chart = [{ day: 'Mon', mastery: Math.max(0, percent - 12) }, { day: 'Tue', mastery: Math.max(0, percent - 9) }, { day: 'Wed', mastery: Math.max(0, percent - 5) }, { day: 'Thu', mastery: Math.max(0, percent - 3) }, { day: 'Fri', mastery: percent }]
  return <main><div className="eyebrow">Momentum over perfection</div><h1>Progress</h1><p className="lede">Look back at the work that is making you stronger.</p><div className="progress-hero"><div className="ring"><strong>{percent}%</strong><span>complete</span></div><div><span className="section-kicker">Overall mastery</span><h2>{data.completed_concepts} of {data.total_concepts} concepts</h2><p>Your next session is already waiting in the roadmap.</p></div></div><div className="panel chart-panel"><div className="panel-heading"><h2>Mastery trend</h2><span className="section-kicker">This week</span></div><ResponsiveContainer width="100%" height={220}><AreaChart data={chart}><XAxis dataKey="day" /><YAxis domain={[0, 100]} /><Tooltip /><Area type="monotone" dataKey="mastery" stroke="#3c7d70" fill="#d8eee3" /></AreaChart></ResponsiveContainer></div>{loading ? <p>Loading progress…</p> : <div className="panel"><div className="panel-heading"><h2>Recent activity</h2></div><p>{Object.keys(data.updates).length ? `You have ${Object.keys(data.updates).length} recorded update${Object.keys(data.updates).length > 1 ? 's' : ''}.` : 'Complete a concept to start your activity history.'}</p></div>}</main>
}
