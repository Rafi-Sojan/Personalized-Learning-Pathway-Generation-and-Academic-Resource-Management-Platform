import type { RoadmapItem } from '../../types'

/** Show scheduled learning items with dates, durations, and prioritization reasons. */
export function RoadmapList({ items }: { items: RoadmapItem[] }) {
  return <div className="roadmap-list">{items.map((item, index) => <div className="roadmap-row" key={item.id}><div className="roadmap-number">{String(index + 1).padStart(2, '0')}</div><div><strong>{item.concept_name}</strong><p>{item.reason}</p>{item.evidence_question_ids?.length ? <small>Historical evidence: {item.evidence_question_ids.map((id, evidenceIndex) => <span key={id}>{evidenceIndex ? ', ' : ''}<a href={`/exams#question-${id}`}>question {evidenceIndex + 1}</a></span>)}</small> : null}</div><time>{new Date(item.scheduled_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}<br /><span>{item.minutes} min</span></time></div>)}</div>
}
