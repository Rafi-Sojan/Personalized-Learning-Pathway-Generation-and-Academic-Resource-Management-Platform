import { useState } from 'react'
import type { RoadmapItem } from '../../types'

type RoadmapListProps = {
  items: RoadmapItem[]
  onUpdate?: (item: RoadmapItem, status: 'planned' | 'completed' | 'skipped', masteryScore?: number) => Promise<void>
}

/** Show typed study sessions with source context, evidence, and optional completion feedback. */
export function RoadmapList({ items, onUpdate }: RoadmapListProps) {
  const [scores, setScores] = useState<Record<string, string>>({})
  const [busyId, setBusyId] = useState('')

  /** Persist one session state and include mastery only for a completed session. */
  async function update(item: RoadmapItem, status: 'planned' | 'completed' | 'skipped') {
    if (!onUpdate) return
    const rawScore = scores[item.id]
    const score = status === 'completed' && rawScore !== undefined && rawScore !== '' ? Number(rawScore) : undefined
    setBusyId(item.id)
    try {
      await onUpdate(item, status, score)
    } finally {
      setBusyId('')
    }
  }

  return <div className="roadmap-list">{items.map((item, index) => <div className={`roadmap-row roadmap-session ${item.status}`} key={item.id}>
    <div className="roadmap-number">{String(index + 1).padStart(2, '0')}</div>
    <div>
      <div className="session-badges"><span>{item.course_code}</span><span>{item.activity_type.replace(/_/g, ' ')}</span><span>{item.modality.replace(/_/g, ' ')}</span>{item.unit_label && <span>Unit {item.unit_label}</span>}{item.assessment_scope !== 'both' && <span>{item.assessment_scope.replace(/_/g, ' ')}</span>}</div>
      <strong>{item.concept_name}</strong>
      <p>{item.reason}</p>
      {item.source_page && <small>Source page {item.source_page}</small>}
      {item.evidence_question_ids?.length ? <small>Historical evidence: {item.evidence_question_ids.map((id, evidenceIndex) => <span key={id}>{evidenceIndex ? ', ' : ''}<a href={`/exams#question-${id}`}>question {evidenceIndex + 1}</a></span>)}</small> : null}
      {onUpdate && item.status !== 'completed' && <div className="session-completion"><label>Mastery <span className="optional-label">optional on completion</span><input aria-label={`Mastery score for ${item.concept_name}`} type="number" min="0" max="100" value={scores[item.id] ?? ''} onChange={(event) => setScores((current) => ({ ...current, [item.id]: event.target.value }))} /></label><button className="secondary" type="button" disabled={busyId === item.id} onClick={() => void update(item, 'completed')}>{busyId === item.id ? 'Saving…' : 'Mark complete'}</button>{item.status === 'planned' ? <button className="secondary" type="button" disabled={busyId === item.id} onClick={() => void update(item, 'skipped')}>Skip</button> : <button className="secondary" type="button" disabled={busyId === item.id} onClick={() => void update(item, 'planned')}>Restore</button>}</div>}
      {item.status === 'completed' && <div className="session-completion"><small className="completion-label">Session completed · the concept closes after all of its sessions are complete</small>{onUpdate && <button className="secondary" type="button" disabled={busyId === item.id} onClick={() => void update(item, 'planned')}>Reopen</button>}</div>}
    </div>
    <time>{new Date(item.scheduled_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}<br /><span>{item.minutes} min</span></time>
  </div>)}</div>
}
