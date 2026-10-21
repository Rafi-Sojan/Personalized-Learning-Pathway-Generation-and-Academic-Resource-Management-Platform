import type { Concept } from '../../types'

export function ConceptMapView({ concepts }: { concepts: Concept[] }) {
  return <div className="concept-map">{concepts.map((concept, index) => <div className={`concept-node ${concept.status}`} style={{ '--index': index } as React.CSSProperties} key={concept.id}><span>{concept.status === 'completed' ? '✓' : index + 1}</span><div><strong>{concept.name}</strong><small>Difficulty {concept.difficulty}/5</small></div></div>)}</div>
}
