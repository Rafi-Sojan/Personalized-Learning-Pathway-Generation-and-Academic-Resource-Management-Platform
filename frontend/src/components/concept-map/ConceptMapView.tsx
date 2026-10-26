import type { Concept } from '../../types'
import { Background, Controls, MiniMap, ReactFlow } from '@xyflow/react'
import '@xyflow/react/dist/style.css'

export function ConceptMapView({ concepts }: { concepts: Concept[] }) {
  const nodes = concepts.map((concept, index) => ({ id: concept.id, position: { x: (index % 3) * 230, y: Math.floor(index / 3) * 130 }, data: { label: `${concept.name} · ${concept.status}` } }))
  const edges = concepts.flatMap((concept) => concept.prerequisites.map((prerequisite) => ({ id: `${prerequisite}-${concept.id}`, source: prerequisite, target: concept.id })))
  return <div className="concept-flow"><ReactFlow nodes={nodes} edges={edges} fitView><MiniMap /><Controls /><Background /></ReactFlow></div>
}
