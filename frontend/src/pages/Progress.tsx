import { useCallback } from 'react'
import { useAsync } from '../hooks/useAsync'
import { getProgress } from '../services/progress'

export function Progress() {
  const { data, loading } = useAsync(useCallback(() => getProgress(), []), { completed_concepts: 0, total_concepts: 1, updates: {} })
  const percent = Math.round((data.completed_concepts / Math.max(data.total_concepts, 1)) * 100)
  return <main><div className="eyebrow">Momentum over perfection</div><h1>Progress</h1><p className="lede">Look back at the work that is making you stronger.</p><div className="progress-hero"><div className="ring"><strong>{percent}%</strong><span>complete</span></div><div><span className="section-kicker">Overall mastery</span><h2>{data.completed_concepts} of {data.total_concepts} concepts</h2><p>Your next session is already waiting in the roadmap.</p></div></div>{loading ? <p>Loading progress…</p> : <div className="panel"><div className="panel-heading"><h2>Recent activity</h2></div><p>{Object.keys(data.updates).length ? `You have ${Object.keys(data.updates).length} recorded update${Object.keys(data.updates).length > 1 ? 's' : ''}.` : 'Complete a concept to start your activity history.'}</p></div>}</main>
}
