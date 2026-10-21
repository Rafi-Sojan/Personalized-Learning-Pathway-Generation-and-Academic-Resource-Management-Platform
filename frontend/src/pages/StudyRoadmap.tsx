import { useCallback } from 'react'
import { RoadmapList } from '../components/roadmap/RoadmapList'
import { useAsync } from '../hooks/useAsync'
import { getRoadmap } from '../services/roadmap'

export function StudyRoadmap() {
  const { data, loading } = useAsync(useCallback(() => getRoadmap(), []), [])
  return <main><div className="eyebrow">Personalized schedule</div><h1>Study roadmap</h1><p className="lede">A two-week path optimized for steady progress.</p><div className="panel"><div className="panel-heading"><div><span className="section-kicker">Next 14 days</span><h2>Your plan</h2></div><button className="secondary">Adjust availability</button></div>{loading ? <p>Building roadmap…</p> : <RoadmapList items={data} />}</div></main>
}
