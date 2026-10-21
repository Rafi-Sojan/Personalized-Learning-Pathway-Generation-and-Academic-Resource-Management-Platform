import type { RoadmapItem } from '../../types'

export function RoadmapList({ items }: { items: RoadmapItem[] }) {
  return <div className="roadmap-list">{items.map((item, index) => <div className="roadmap-row" key={item.id}><div className="roadmap-number">{String(index + 1).padStart(2, '0')}</div><div><strong>{item.concept_name}</strong><p>{item.reason}</p></div><time>{new Date(item.scheduled_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}<br /><span>{item.minutes} min</span></time></div>)}</div>
}
