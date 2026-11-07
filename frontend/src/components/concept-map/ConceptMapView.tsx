import type { Concept } from '../../types'
import { Background, Controls, MiniMap, ReactFlow } from '@xyflow/react'
import '@xyflow/react/dist/style.css'

/** Lay out reviewed and pending syllabus concepts in stable unit columns. */
export function ConceptMapView({ concepts }: { concepts: Concept[] }) {
  const conceptIds = new Set(concepts.map((concept) => concept.id))
  const units = [...new Set(concepts.map((concept) => concept.unit_label ?? 'Unassigned'))]
  const nodes = units.flatMap((unit, unitIndex) => {
    const members = concepts.filter((concept) => (concept.unit_label ?? 'Unassigned') === unit)
    const roots = members.filter((concept) => !concept.parent_concept_id || !conceptIds.has(concept.parent_concept_id)).sort((left, right) => left.name.localeCompare(right.name))
    const ordered = roots.flatMap((root) => [root, ...members.filter((concept) => concept.parent_concept_id === root.id).sort((left, right) => left.name.localeCompare(right.name))])
    const included = new Set(ordered.map((concept) => concept.id))
    ordered.push(...members.filter((concept) => !included.has(concept.id)).sort((left, right) => left.name.localeCompare(right.name)))
    return ordered.map((concept, rowIndex) => {
      const isChild = Boolean(concept.parent_concept_id && conceptIds.has(concept.parent_concept_id))
      const provenance = [concept.unit_label, concept.source_page ? `PDF p. ${concept.source_page}` : null, concept.review_status?.replace('_', ' ')].filter(Boolean).join(' · ')
      const pending = concept.review_status === 'pending_review'
      return {
        id: concept.id,
        position: { x: unitIndex * 460 + (isChild ? 180 : 0), y: rowIndex * 115 },
        data: { label: `${concept.name}${provenance ? `\n${provenance}` : ''}` },
        style: { width: isChild ? 230 : 260, borderColor: pending ? '#c78528' : '#3c7d70', background: pending ? '#fff8e8' : '#f2faf7' },
      }
    })
  })
  const prerequisiteEdges = concepts.flatMap((concept) => concept.prerequisites.filter((prerequisite) => conceptIds.has(prerequisite)).map((prerequisite) => ({ id: `prereq-${prerequisite}-${concept.id}`, source: prerequisite, target: concept.id })))
  const hierarchyEdges = concepts.filter((concept) => concept.parent_concept_id && conceptIds.has(concept.parent_concept_id)).map((concept) => ({ id: `topic-${concept.parent_concept_id}-${concept.id}`, source: concept.parent_concept_id!, target: concept.id, label: 'subtopic', style: { strokeDasharray: '5 5' } }))
  const edges = [...prerequisiteEdges, ...hierarchyEdges]
  return <div className="concept-flow"><ReactFlow nodes={nodes} edges={edges} fitView><MiniMap /><Controls /><Background /></ReactFlow></div>
}
